import logging, os, csv, requests
from azure.storage.blob import BlobServiceClient
import azure.functions as func
from datetime import datetime

app = func.FunctionApp()

def safe_get(dct, *keys, default=None):
    for key in keys:
        if isinstance(dct, dict):
            dct = dct.get(key, default)
        else:
            return default
    return dct

def extract_text_from_rich_text(rich_text_list):
    if isinstance(rich_text_list, list) and len(rich_text_list) > 0:
        return rich_text_list[0].get("text", {}).get("content", "")
    return ""

# 🔗 Récupérer un champ "Nom" depuis une page liée
def get_name_from_relation_page(page_id, headers, property_name):
    try:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            logging.warning(f"⚠️ Impossible de récupérer la page liée : {page_id} | Status: {res.status_code}")
            return ""
        data = res.json()
        prop = data["properties"].get(property_name)
        if not prop:
            logging.warning(f"❗ Propriété '{property_name}' introuvable dans la page liée.")
            return ""
        title_list = prop.get("title", [])
        return title_list[0]["text"]["content"] if title_list else ""
    except Exception as e:
        logging.error(f"❌ Erreur lecture page liée '{page_id}' : {e}")
        return ""

@app.function_name(name="extract_RDVs_from_notion")
@app.schedule(schedule="*/30 * * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_RDVs_from_notion(myTimer: func.TimerRequest) -> None:
    logging.info("🔁 Déclenchement de la récupération Notion...")

    headers = {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    notion_url = "https://api.notion.com/v1/databases/'ton id-databse'/query"
    payload, all_rows = {}, []

    while True:
        res = requests.post(notion_url, headers=headers, json=payload)
        data = res.json()
        all_rows.extend(data["results"])
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]

    lignes = []
    for page in all_rows:
        p = page["properties"]

        # 🕒 Traitement de la date/heure du RDV
        date_rdv = safe_get(p, "Date & Heure RDV", "date", "start")
        if date_rdv:
            try:
                dt = datetime.fromisoformat(date_rdv)
                if dt.time().hour == 0 and dt.time().minute == 0:
                    dt = dt.replace(hour=0, minute=0)
                datetime_rdv = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                datetime_rdv = f"{date_rdv} 00:00:00"
        else:
            datetime_rdv = None

        # 🔗 Commercial depuis "Candidats Recrutement"
        commercial_name = ""
        commercial_rel = p.get("Commercial", {}).get("relation", [])
        if commercial_rel:
            commercial_name = get_name_from_relation_page(commercial_rel[0]["id"], headers, "Nom")

        # 🔗 Nom Client depuis "KITS MISSIONS"
        nom_client = ""
        client_rel = p.get("Client", {}).get("relation", [])
        logging.info(f"🔗 Relation 'Client' = {client_rel}")
        if client_rel:
            nom_client = get_name_from_relation_page(client_rel[0]["id"], headers, "Nom")
            logging.info(f"✅ Nom client extrait : {nom_client}")

        lignes.append({
            "Date_generation": safe_get(p, "Date de génération", "date", "start"),
            "Date_RDV": date_rdv,
            "DateTime_RDV": datetime_rdv,
            "Statut": safe_get(p, "Statut", "status", "name"),
            "Intitulé_poste": safe_get(p, "Intitulé du poste", "rich_text", 0, "text", "content", default=""),
            "Source_RDV": safe_get(p, "Source RDV", "select", "name"),
            "Responsable": commercial_name,
            "Nom_Client": nom_client
        })

    filename = "/tmp/RDVs.csv"
    try:
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=lignes[0].keys())
            writer.writeheader()
            writer.writerows(lignes)
        logging.info("📁 Fichier CSV généré.")
    except Exception as e:
        logging.error(f"❌ Erreur écriture CSV : {e}")
        return

    try:
        blob = BlobServiceClient.from_connection_string(os.environ["AZURE_STORAGE_CONNECTION_STRING"])
        container = blob.get_container_client("rdvs")
        with open(filename, "rb") as data:
            container.upload_blob(name="RDVs.csv", data=data, overwrite=True)
        logging.info("✅ Fichier 'RDVs-modif.csv' uploadé dans Azure Blob Storage.")
    except Exception as e:
        logging.error(f"❌ Erreur upload Azure : {e}")
