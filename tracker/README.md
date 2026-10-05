# Tracker — schéma du tableur

Fichier : `tracker/appart-tracker.xlsx` (chemin réglable dans `search.toml` → `[output] tracker`), une feuille `Annonces`. Créé automatiquement au premier run par `hunt/tracker.py`.

| Colonne            | Type        | Rempli par | Description                                                       |
| ------------------ | ----------- | ---------- | ----------------------------------------------------------------- |
| URL                | texte (clé) | script     | Clé de déduplication                                              |
| Plateforme         | texte       | script     | bienici / leboncoin / pap / seloger / figaro / foncia / …         |
| Date d'ajout       | date        | script     | Premier run où l'annonce est apparue                              |
| Prix               | nombre      | script     | €/mois, charges comprises si le site le précise                   |
| Surface (m²)       | nombre      | script     |                                                                   |
| Pièces             | nombre      | script     |                                                                   |
| Chambres           | nombre      | script     |                                                                   |
| Code postal        | texte       | script     |                                                                   |
| Ville / Quartier   | texte       | script     |                                                                   |
| Étage              | nombre      | script     | 0 = RDC ; vide si inconnu                                         |
| Ascenseur          | oui/non     | script     | vide si non précisé                                               |
| Meublé             | oui/non     | script     | vide si non précisé                                               |
| Type de contact    | texte       | script     | particulier / agence                                              |
| Disponible le      | date/texte  | script     |                                                                   |
| Zone               | texte       | script     | 1 / 2 / hors-zone (d'après `search.toml`)                         |
| Priorité           | texte       | Claude     | HAUTE / MOYENNE / BASSE (via `--set-priorities`)                  |
| Statut             | texte       | toi        | Nouveau / Contacté / Visite prévue / Refusé / Signé               |
| Message envoyé     | oui/non     | toi        |                                                                   |
| Autres URLs        | texte       | script     | Même bien publié sur d'autres sites (une URL par ligne) — aussi utilisé pour la déduplication |
| Notes              | texte libre | toi        |                                                                   |

## Couleurs de ligne

Appliquées par `python -m hunt.run --set-priorities priorities.json` :

- HAUTE → vert `E2EFDA`
- MOYENNE → jaune `FFFFC7`
- BASSE → rouge `FCE4D6`
