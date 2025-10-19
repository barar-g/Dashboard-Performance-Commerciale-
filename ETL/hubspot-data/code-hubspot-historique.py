import logging
import os
import requests
import json
import time
import locale
from datetime import datetime, timezone, timedelta, date
import pandas as pd
from dateutil import parser
from azure.storage.blob import BlobServiceClient
from concurrent.futures import ThreadPoolExecutor, as_completed

# Azure Function setup
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="ping")
@app.route(route="ping")
def ping(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("pong", status_code=200)

@app.function_name(name="hubspot_fast_export")
@app.schedule(
    schedule="0 */2 * * * *",
    arg_name="mytimer",
    run_on_startup=False,
    use_monitor=False
)
def hubspot_fast_export(mytimer: func.TimerRequest) -> None:
    logging.info("🚀 Démarrage - Export rapide des appels HubSpot depuis mai 2023...")

    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')  # Linux/macOS
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'French_France')  # Windows fallback

    HUBSPOT_TOKEN = os.environ["HUBSPOT_TOKEN"]
    EXPORT_PATH = "/tmp"
    os.makedirs(EXPORT_PATH, exist_ok=True)

    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

    gmt_plus_2 = timezone(timedelta(hours=2))
    # Historique complet
    start_date = date(2024, 5, 23)
    end_date   = date(2025, 5, 14)

    # Récupération des propriétaires
    owner_map = {}
    try:
        r = requests.get("https://api.hubapi.com/crm/v3/owners", headers=headers)
        r.raise_for_status()
        for o in r.json().get("results", []):
            owner_map[o['id']] = f"{o.get('firstName','')} {o.get('lastName','')}".strip()
        logging.info(f"✅ {len(owner_map)} agents chargés depuis HubSpot")
    except Exception as e:
        logging.error(f"❌ Erreur récupération owners: {e}")

    def get_call_data(day: pd.Timestamp):
        local_calls = []
        for hour in range(0, 24, 2):
            start_time = datetime(day.year, day.month, day.day, hour, 0, tzinfo=gmt_plus_2)
            end_time   = start_time + timedelta(hours=2)
            start_ts   = int(start_time.timestamp() * 1000)
            end_ts     = int(end_time.timestamp() * 1000)
            payload = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "hs_timestamp",
                        "operator": "BETWEEN",
                        "value": start_ts,
                        "highValue": end_ts
                    }]
                }],
                "properties": [
                    "hs_call_duration",
                    "hs_call_disposition",
                    "hs_timestamp",
                    "hubspot_owner_id"
                ],
                "limit": 100
            }
            after, retries = None, 0
            while True:
                body = dict(payload)
                if after:
                    body["after"] = after
                resp = requests.post(
                    "https://api.hubapi.com/crm/v3/objects/calls/search",
                    headers=headers,
                    data=json.dumps(body)
                )
                if resp.status_code == 429:
                    time.sleep(min(60, 2**retries))
                    retries += 1
                    continue
                if resp.status_code != 200:
                    break
                page = resp.json()
                local_calls.extend(page.get("results", []))
                after = page.get("paging", {}).get("next", {}).get("after")
                if not after:
                    break
        return local_calls

    # Récupération parallèle
    logging.info("🧵 Récupération parallèle...")
    all_calls = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_call_data, day): day
                   for day in pd.date_range(start_date, end_date)}
        for future in as_completed(futures):
            day = futures[future]
            try:
                calls = future.result()
                all_calls.extend(calls)
                logging.info(f"📆 {day.date()} → {len(calls)} appels")
            except Exception as e:
                logging.error(f"❌ Erreur jour {day.date()}: {e}")

    if not all_calls:
        logging.warning("⚠️ Aucun appel récupéré.")
        return

    logging.info(f"📦 Total appels récupérés : {len(all_calls)}")

    # Mapping dispositions
    disposition_labels = {
        "a4c4c377-d246-4b32-a13b-75a56a4cd0ff": "A laissé un message en direct",
        "b2cf5968-551e-4856-9783-52b3da59a7d0": "A laissé un message vocal",
        "73a0d17f-1163-4015-bdd5-ec830791da20": "Aucune réponse",
        "f240bbac-87c9-4f6e-bf70-924b57d47db7": "Connecté",
        "17b47fee-58de-441e-a44c-c6300d46f273": "Mauvais numéro",
        "9d9162e7-6cf3-4944-bf63-4dff82258764": "Occupé"
    }

    # Construction du DataFrame
    rows = []
    for call in all_calls:
        props    = call.get("properties", {})
        timestamp= props.get("hs_timestamp")
        dt       = parser.isoparse(timestamp).astimezone(gmt_plus_2) if timestamp else None
        rows.append({
            "id": call.get("id"),
            "Durée_Secondes": int(int(props.get("hs_call_duration") or 0) / 1000),
            "Résultat de l'appel": disposition_labels.get(props.get("hs_call_disposition"), "Inconnu"),
            "Date d’activité": dt,
            "Activité attribuée à": owner_map.get(props.get("hubspot_owner_id"), "Inconnu")
        })

    df = pd.DataFrame(rows)
    df["Jour"]   = df["Date d’activité"].dt.strftime("%A")
    df["Heure"]  = df["Date d’activité"].dt.hour
    df["Minute"] = df["Date d’activité"].dt.strftime("%H:%M")

    # ── Bloc assign_creneau : 1h de 09h30 à 18h30 ─────────────────────────────
    DEBUTS = [
        (datetime.min + timedelta(hours=9, minutes=30) + timedelta(hours=i)).time()
        for i in range(9)
    ]
    def assign_creneau(dt):
        if pd.isna(dt):
            return "Hors plage"
        t = dt.time()
        for start in DEBUTS:
            end = (datetime.combine(date.min, start) + timedelta(hours=1)).time()
            if start <= t < end:
                return f"{start.hour:02d}h{start.minute:02d}-{end.hour:02d}h{end.minute:02d}"
        return "Hors plage"
    df["Créneau Horaire"] = df["Date d’activité"].apply(assign_creneau)

    # ── Calcul de la différence entre appels ──────────────────────────────────
    pause_start = datetime.strptime("12:30", "%H:%M").time()
    pause_end   = datetime.strptime("14:00", "%H:%M").time()
    df = df.sort_values(by="Date d’activité", ascending=False).reset_index(drop=True)
    diffs = [None]
    for i in range(1, len(df)):
        curr = df.loc[i-1, "Date d’activité"]
        prev = df.loc[i,   "Date d’activité"]
        if pd.isna(curr) or pd.isna(prev) or curr.date() != prev.date():
            diffs.append(None)
            continue
        if pause_start <= curr.time() < pause_end or pause_start <= prev.time() < pause_end:
            diffs.append(None)
            continue
        diffs.append((curr - prev).total_seconds())
    df["Différence entre les appels (secondes)"] = diffs

    # Export et upload historique complet
    final_path = os.path.join(EXPORT_PATH, "hubspot-data.csv")
    df.to_csv(final_path, index=False, encoding="utf-8-sig")

    try:
        blob_service      = BlobServiceClient.from_connection_string(os.environ["AZURE_STORAGE_CONNECTION_STRING"])
        container_client  = blob_service.get_container_client("hubspot-data")
        with open(final_path, "rb") as f:
            container_client.upload_blob(name="hubspot-data.csv", data=f, overwrite=True)
        logging.info("✅ Fichier 'hubspot-data.csv' uploadé dans Azure Blob Storage.")
    except Exception as e:
        logging.error(f"❌ Erreur upload : {e}")
