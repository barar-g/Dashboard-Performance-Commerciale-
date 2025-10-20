# Dashboard Performance Commerciale — ETL & BI

Dépôt vitrine (lecture seule) présentant :
- une **chaîne ETL** automatisée (Azure Functions → Azure Blob, CSV) ;
- un **dashboard Power BI** documenté (captures, démo, KPIs).

## Vue d’ensemble
- **Sources** : Notion (RDVs, Clients, Plan de charge) & HubSpot (Appels).
- **ETL** : 4 fonctions **indépendantes** (extraction → transformation → export **CSV** sur Azure Blob, écrasement).
  - **Fréquences** : Notion toutes les **30 s** ; HubSpot toutes les **2 min**.
- **BI** : modèle en **étoile**, **Power Query (M)** pour la préparation, **DAX** pour les KPIs.

## Ce que vous trouverez
- **ETL/** : structure des fonctions et des sorties (CSV normalisés par conteneur).
- **BI/** : **captures** des pages (Performance, RDVs, Objectifs, Joignabilité, Classement/Score, Modèle), **vidéo de démo** et **docs** (architecture, Power Query M, KPIs DAX).
- **Documentation Technique/** : définitions détaillées (modèle, transformations, mesures).

## Indicateurs clés (exemples)
- **RDVs** : taux faits / annulés / no-show ; **conversion RDVs** (pris / conversations).
- **Joignabilité** : **taux de décrochage** (conversations / appels).
- **Pilotage** : **réalisation des objectifs**, **délais** (génération → RDV / RDV fait), **Score Global** & **rang** par commercial.

## Architecture (simplifiée)
