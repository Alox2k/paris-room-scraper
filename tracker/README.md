# Tracker — schéma du tableur

Fichier : `appart-tracker.xlsx`, une feuille unique nommée `Annonces`.

| Colonne             | Type              | Description                                                  |
| -------------------- | ----------------- | -------------------------------------------------------------- |
| URL                  | texte (clé unique) | Utilisée pour la déduplication                                 |
| Plateforme           | texte              | PAP / SeLoger / LeBonCoin / Bien'ici                             |
| Date d'ajout          | date               | Date du premier passage du run                                 |
| Prix                 | nombre             | En euros, charges comprises si possible                        |
| Surface (m²)          | nombre             |                                                                  |
| Ville / Quartier      | texte              |                                                                  |
| Étage                 | texte              |                                                                  |
| Ascenseur             | booléen            | true / false / null si non précisé                             |
| Type de bail          | texte              | classique / mobilité / colocation / coliving                    |
| Disponible le          | date               |                                                                  |
| Priorité              | texte              | HAUTE / MOYENNE / BASSE                                          |
| Statut                | texte              | Nouveau / Contacté / Visite prévue / Refusé / Signé              |
| Message envoyé         | booléen            |                                                                  |
| Notes                 | texte libre        |                                                                  |

## Couleurs de ligne (mise en forme conditionnelle)

- HAUTE priorité → fond vert `E2EFDA`
- MOYENNE priorité → fond jaune `FFFFC7`
- BASSE priorité → fond rouge `FCE4D6`

## Création initiale

Si le fichier n'existe pas au premier run, la skill le crée automatiquement avec ces colonnes et la mise en forme conditionnelle appliquée sur toute la plage.
