# ETL — Azure Functions → Azure Blob (Python)

**But** : 4 fonctions **indépendantes** extraient depuis **Notion** et **HubSpot**, transforment, puis déposent des **CSV** dans **Azure Blob Storage**.

## Fonctions
| Dossier            | Source   | Sortie (conteneur / fichier)                  | Rôle |
|--------------------|----------|-----------------------------------------------|------|
| `Dim-Clients/`     | Notion   | `dim-clients` / `dim_clients.csv`             | Dimension clients |
| `RDVs/`            | Notion   | `rdvs` / `rdvs.csv`                           | Rendez-vous (pris, faits, annulés, no-shows) |
| `plan de charge/`  | Notion   | `plan-de-charge` / `plan_de_charge.csv`       | Créneaux & sessions |
| `hubspot-data/`    | HubSpot  | `hubspot-data-latest` / `hubspot-data-latest.csv` | Appels & conversations |

## Planification (TimerTrigger)
- **Notion** : toutes les **30 secondes** → `*/30 * * * * *`
- **HubSpot** : toutes les **2 minutes** → `0 */2 * * * *`

## Clés à REMPLIR (Azure → Function App → Configuration, ou `local.settings.json`)
- `AzureWebJobsStorage` → **Chaîne de connexion Azure Storage** (requis par le runtime)
- `AZURE_STORAGE_CONNECTION_STRING` → **Chaîne de connexion Azure Storage** (upload CSV)
- `NOTION_TOKEN` → **Notion Internal Integration Token**
- `NOTION_DATABASE_ID` → **ID** de la base Notion (si nécessaire)
- `HUBSPOT_TOKEN` → **HubSpot Private App Token** (uniquement pour `hubspot-data`)

> Le code lit ces valeurs via `os.environ[...]`.

## Pipeline (chaque fonction)
**Extraction** (API + pagination/retry) → **Transformation** (typages, enrichissements) → **Upload** CSV sur **Azure Blob** (**overwrite**).

## Lancer en local (optionnel)
```bash
cd ETL/<NomDeLaFonction>
pip install -r requirements.txt
func start
