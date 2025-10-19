# BI — Dashboard Performance Commerciale (Power BI)

Dossier contenant les **ressources de visualisation** : captures d’écran du dashboard, vidéo de démonstration et fichiers d’assets (logos, thèmes).

## 🎯 Objectif
Donner une vue claire et actionnable de la **performance commerciale** :
- activité d’appels, **joignabilité** et **conversion**,
- **parcours RDV** (pris → fait / annulé / no-show),
- suivi des **objectifs** et des **scores** par commercial.

## 📦 Contenu du dossier
- `captures/` *(images)* : vues principales du rapport  
  - **Performance** (`perfomance.png`)  
  - **RDVs** (`RDVs.png`)  
  - **Objectifs** (`objectif.png`)  
  - **Joignabilité** (`app.png`)  
  - **Classement / Scores** (`classement.png`)  
  - **Modèle de données (étoile)** (`etoile.png`)
- `demo/` *(optionnel)* : **vidéo** de démonstration (navigation & usages)
- `assets/` : logos, thèmes, pictos

> Le fichier `.pbix` est maintenu en dehors de ce dossier (ou à ajouter selon votre convention).

## 🧭 Pages du rapport (aperçu fonctionnel)
- **Performance** : synthèse par commercial et période (appels, conversations, RDVs pris, CA, délais, réalisation d’objectifs, conversion, décrochage).  
- **RDVs** : volumes et qualité des rendez-vous (faits/annulés/no-show), clients générateurs, tendance temporelle.  
- **Objectifs** : réalisé vs cible, **rang jour**, variations **J-1** / **S-1**.  
- **Joignabilité** : **taux de connectivité** par jour/heure, **total d’appels connectés** et **total d’appels**, répartition des dispositions (connecté, sans réponse, etc.).  
- **Classement / Scores** : **Score Global** et sous-scores (génération RDVs, non-faits, délai), **rang** par commercial.  
- **Modèle (étoile)** : schéma logique pour comprendre les relations faits/dimensions.

## 🔗 Sources / actualisation
- Les données proviennent des **CSV déposés dans Azure Blob** par l’ETL (dossier `ETL/`).  
- Actualisation prévue via **Power BI Service** (planning aligné sur l’ETL).  
- Tables clés : `rdvs`, `hubspot-data-latest`, `dim-clients`, `plan-de-charge`, dimensions auxiliaires.

## 🧪 KPIs & mesures (exemples)
- **Taux de RDVs faits / annulés / no-show**  
- **Taux de conversion RDVs** (RDVs pris / conversations)  
- **Taux de décrochage** (conversations / appels)  
- **Taux de réalisation des objectifs**  
- **Délais** (génération → RDV, génération → RDV fait)  
- **Score Global** (pondéré) et **rang**

> La définition complète des KPIs (DAX) se trouve dans `../Documentation Technique/`.

## 🧰 Utilisation (tips rapides)
- Filtres principaux : **plage de dates**, **commercial**, **client/source**.  
- Survolez les graphes pour les **tooltips** et utilisez les légendes pour **isoler** une série.  
- Drill-down/Drill-through disponibles sur certaines visuels temporels.

## ✅ Prérequis pour ouvrir/modifier le .pbix
- Power BI Desktop (version récente)  
- Accès en lecture au **compte de stockage** Azure (conteneurs Blob)  
- Chemins d’accès aux CSV **identiques** à ceux configurés en Power Query (ou à reparamétrer via **Paramètres de source**)

---

**Contact / évolutions** : ouvrir une issue dans le repo ou contacter l’équipe Data.
