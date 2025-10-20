# BI — Dashboard Performance Commerciale (Power BI)

https://github.com/user-attachments/assets/89df5565-bc9a-4e31-8e1c-44f82249ad96

Dossier contenant les **ressources de visualisation** : captures d’écran du dashboard, **vidéo de démonstration** et **documentation technique** (architecture globale, **Power Query / code M**, développement des **KPIs DAX**).

## 🎯 Finalité du dashboard
Offrir une lecture rapide et actionnable de la **performance commerciale** :
- activité d’appels, **joignabilité** et **conversion**,
- **parcours RDV** (pris → fait / annulé / no-show),
- suivi des **objectifs** et un **classement par scores**.

## 📦 Ce que contient ce dossier
- `captures/` : vues clés du rapport  
  - **Performance** (`perfomance.png`) – synthèse par commercial et période  
  - **RDVs** (`RDVs.png`) – volumes & qualité (faits/annulés/no-show)  
  - **Objectifs** (`objectif.png`) – réalisé vs cible, rang & variations  
  - **Joignabilité** (`app.png`) – taux de connectivité par jour/heure  
  - **Classement / Scores** (`classement.png`) – Score Global & rang  
  - **Modèle (étoile)** (`etoile.png`) – schéma logique du modèle
- `docs/` : **note technique** (architecture globale, **Power Query / code M**, **KPIs DAX**)

## 🔗 D’où viennent les données ?
Les visuels reposent sur des **CSV alimentés automatiquement** par l’ETL (voir dossier `ETL/`) :
- **HubSpot** pour les **appels** (joignabilité, dispositions, durées),
- **Notion** pour les **RDVs**, **clients** et **plan de charge**.

## 🧪 KPIs principaux
- **Taux de RDVs** (faits / annulés / no-show)  
- **Taux de conversion RDVs** (pris / conversations)  
- **Taux de décrochage** (conversations / appels)  
- **Taux de réalisation des objectifs**  
- **Délais** (génération → RDV / RDV fait)  
- **Score Global** (pondération : volume, qualité, non-faits, délai) & **rang**

## 🧰 Stack & méthode (haut niveau)
- **Power BI** (modèle en étoile, DAX mesurable et lisible)
- **Power Query (M)** pour normalisation/typage
- **Azure Blob** comme couche données (CSV) alimentée par **Azure Functions (Python)**




https://github.com/user-attachments/assets/89df5565-bc9a-4e31-8e1c-44f82249ad96

