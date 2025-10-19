import logging, os, json, csv, requests
from azure.storage.blob import BlobServiceClient
import azure.functions as func

app = func.FunctionApp()

# 🔍 Extraction du texte depuis les champs rich_text
def extract_text_from_rich_text(rich_text_list):
    if isinstance(rich_text_list, list) and len(rich_text_list) > 0:
        return rich_text_list[0].get("text", {}).get("content", "")
    return ""

@app.function_name(name="extract_dim_clients")
@app.schedule(schedule="0 */1 * * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False)
def extract_dim_clients(myTimer: func.TimerRequest) -> None:
    logging.info("🚀 Déclenchement de l'extraction des données métier Notion (dim_clients)...")

    headers = {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    notion_url = "https://api.notion.com/v1/databases/'ton id-datbase'/query"

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

        lignes.append({
            "Nom": extract_text_from_rich_text(p["Nom"]["title"]),
            "Statut": p["Statut"]["status"]["name"] if p["Statut"].get("status") else "",
            "Score_Coopération": p["Score de Coopération"].get("number", ""),
            "Score_Client": p["Score Client (Formule)"]["formula"].get("number", ""),
            "ID_Client": p["ID Client"]["unique_id"].get("prefix", "") + str(p["ID Client"]["unique_id"].get("number", "")),
            "Démarrage_1er_Contrat": p["Démarrage 1er Contrat"]["date"].get("start", "") if p["Démarrage 1er Contrat"].get("date") else "",
            "Type": p["Type"]["select"]["name"] if p["Type"].get("select") else "",
            "Type_de_Secteur": p["Type de Secteur"]["select"]["name"] if p["Type de Secteur"].get("select") else "",
            "Taille_Entreprise": p["Taille d'entreprise"]["select"]["name"] if p["Taille d'entreprise"].get("select") else "",
            "Taille_Entreprise_Ciblee": ', '.join([item["name"] for item in p["Taille d'entreprise ciblée"]["multi_select"]]),
            "Potentiel_Upsell": p["Potentiel d'Upsell"].get("number", ""),
            "Prestation": ', '.join([item["name"] for item in p["Prestation"]["multi_select"]]),
            "Localisation": extract_text_from_rich_text(p["Localisation"]["rich_text"]),
            "Objectif_RDVs": p["Objectif RDVs"].get("number", ""),
            "Mensualites_HT": p["Mensualités (H.T.)"].get("number", ""),
            "Marque_Client": p["Marque du Client"].get("number", ""),
            "Code_NAF": extract_text_from_rich_text(p["Code NAF"]["rich_text"]),
            "Delai_Moyen_Paiement": p["Délai moyen paiement Factures (Jours)"].get("number", ""),
            "Niveau_Energie": p["Niveau d'énergie demandé"].get("number", ""),
            "Difficulte_Projet": p["Difficulté Projet"].get("number", ""),
            "Source": p["Source"]["select"]["name"] if p["Source"].get("select") else "",
            "Leads_envoyes_GH": p["Leads envoyés à GH"].get("number", ""),
            "Secteurs_Cibles": extract_text_from_rich_text(p["Secteur(s) ciblé(s)"]["rich_text"]),
            "Panier_Moyen_Client": p["Panier Moyen (Client)"].get("number", ""),
            "ROI_Potentiel_Client": p["ROI potentiel Client"].get("number", ""),
            "ROI_Reel_Client": p["ROI réel Client"].get("number", ""),
            "Feedbacks_Terrain": extract_text_from_rich_text(p["Feedbacks terrain"]["rich_text"]),
            "Account_Manager": p["Account Manager(s)"]["people"][0]["name"] if p["Account Manager(s)"]["people"] else ""
        }) 

    # 📁 Écriture du fichier CSV : dim_clients.csv
    filename = "/tmp/dim_clients.csv"
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=lignes[0].keys())
            writer.writeheader()
            writer.writerows(lignes)
        logging.info("✅ Fichier CSV 'dim_clients.csv' généré avec succès.")
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'écriture du fichier CSV : {e}")
        return

    # 📤 Upload dans Azure Blob Storage (container 'dim-client')
    try:
        blob_service = BlobServiceClient.from_connection_string(os.environ["AZURE_STORAGE_CONNECTION_STRING"])
        container = blob_service.get_container_client("dim-clients")
        with open(filename, "rb") as data:
            container.upload_blob(name="dim_clients.csv", data=data, overwrite=True)
        logging.info("📦 Upload réussi : 'dim_clients.csv' dans le conteneur 'dim-client'.")
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'upload vers Azure Blob Storage : {e}")
