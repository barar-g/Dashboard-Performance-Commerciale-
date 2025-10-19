import logging, os, csv, requests
from azure.storage.blob import BlobServiceClient
import azure.functions as func

app = func.FunctionApp()

# 🔍 Pour extraire les textes manuels
def extract_text_from_rich_text(rich_text_list):
    if isinstance(rich_text_list, list) and len(rich_text_list) > 0:
        return rich_text_list[0].get("text", {}).get("content", "")
    return ""

# 🔗 Récupérer le nom du client via son ID
def get_client_name_from_relation(client_id, headers):
    try:
        url = f"https://api.notion.com/v1/pages/{client_id}"
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            logging.warning(f"⚠️ Impossible de récupérer la page liée : {client_id}")
            return ""
        data = res.json()
        nom_field = data["properties"].get("Nom", {}).get("title", [])
        return nom_field[0]["text"]["content"] if nom_field else ""
    except Exception as e:
        logging.error(f"❌ Erreur lecture client lié : {e}")
        return ""

@app.function_name(name="timer_trigger1")
@app.schedule(schedule="*/30 * * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def timer_trigger1(myTimer: func.TimerRequest) -> None:
    logging.info("🔁 Déclenchement de la récupération Notion...")

    headers = {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    notion_url = "https://api.notion.com/v1/databases/'ton id-databse'/query"
    all_rows = []
    payload = {}

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

        # 🔗 Extraction du nom du client depuis la relation
        client_name = ""
        client_relations = p.get("Client", {}).get("relation", [])
        if client_relations:
            client_name = get_client_name_from_relation(client_relations[0]["id"], headers)

        lignes.append({
            "Cible": p["Cible"]["title"][0]["text"]["content"] if p["Cible"]["title"] else "",
            "Commercial": (p["Commercial"].get("select") or {}).get("name"),
            "Appels": (p["Appels"].get("number") if p["Appels"] else None),
            "Conversations": (p["Conversations"].get("number") if p["Conversations"] else None),
            "RDVs": (p["RDVs"].get("number") if p["RDVs"] else None),
            "Objectif_RDVs": (p["Objectif RDVs"].get("number") if p["Objectif RDVs"] else None),
            "Minari": p["Minari"]["checkbox"] if "Minari" in p else None,
            "Bonus": p["Bonus"]["checkbox"] if "Bonus" in p else None,
            "Rem_genere": (p["Rem. (généré)"].get("formula") or {}).get("number"),
            "Rem_honore": (p["Rem. (honoré)"].get("formula") or {}).get("number"),
            "Start": (p["Date & Heure Session"]["date"]["start"] if p["Date & Heure Session"]["date"] else None),
            "End": (p["Date & Heure Session"]["date"]["end"] if p["Date & Heure Session"]["date"] else None),
            "Nom_Client": client_name
        })

    filename = "/tmp/plan_de_charge.csv"
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=lignes[0].keys())
            writer.writeheader()
            writer.writerows(lignes)
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'écriture du fichier CSV : {e}")
        return

    try:
        blob = BlobServiceClient.from_connection_string(os.environ["AZURE_STORAGE_CONNECTION_STRING"])
        container = blob.get_container_client("testrelation")
        with open(filename, "rb") as data:
            container.upload_blob(name="plan_de_charge.csv", data=data, overwrite=True)
        logging.info(f"✅ Fichier 'plan_de_charge.csv' uploadé dans Azure Blob Storage.")
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'upload : {e}")
