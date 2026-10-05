# Config — Recherche d'appart Paris (à deux)

Copie ce fichier en `config.md` (ignoré par git) et remplis-le. `config.md` reste local, jamais commit.

Les critères **chiffrés** utilisés par les scrapers (budget, pièces, chambres, surface, codes postaux) sont dans `search.toml` (copie de `search.example.toml`). Ce fichier-ci sert à Claude pour prioriser et écrire les messages.

## Le foyer

| Champ                        | Personne 1                                   | Personne 2                                   |
| ---------------------------- | -------------------------------------------- | -------------------------------------------- |
| Prénom                       | (à compléter)                                | (à compléter)                                |
| Âge                          |                                              |                                              |
| Situation pro                | (CDI / CDD / freelance / étudiant…, depuis)  |                                              |
| Revenus nets / mois          |                                              |                                              |
| Garant / Visale              | (oui/non, type)                              |                                              |
| Lieux réguliers à desservir  | (travail, sport… + fréquence)                | (travail, sport… + fréquence)                |
| Trajet max acceptable        | (ex : 35 min porte à porte)                  |                                              |

Relation (couple, amis…) : (à compléter — utile pour le ton des messages et le type de bail)

## Le logement

| Champ                        | Valeur                                                                  |
| ---------------------------- | ----------------------------------------------------------------------- |
| Type                         | Appartement 2 chambres (3 pièces minimum)                               |
| Budget                       | (max charges comprises — reporter dans `search.toml` → `max_rent`)      |
| Surface minimale              | (reporter dans `search.toml` → `min_surface`)                          |
| Meublé                        | (oui / non / indifférent — `search.toml` → `furnished`)               |
| Type de bail accepté          | (bail classique résidence principale / mobilité / code civil…)        |
| Ascenseur                     | (obligatoire à partir de quel étage)                                  |
| Must-have                     | (ex : chambres séparées, 2e WC, lave-linge, extérieur…)              |
| Date d'emménagement           | (date cible ± tolérance — `search.toml` → `move_in`)                  |

## Zones

Décris-les ici en clair (Claude s'en sert pour juger les trajets), et reporte les **codes postaux** dans `search.toml` (`[zones]`).

- **Priorité 1** : (quartiers/villes + lignes de métro/RER, et pourquoi)
- **Priorité 2** : (zones acceptables)
- **À éviter** : (et pourquoi)

## Contact & dossier

| Champ                         | Valeur                                                 |
| ----------------------------- | ------------------------------------------------------ |
| Email du récap                | (à compléter)                                          |
| Dossiers de location          | (statut : prêts / en cours, DossierFacile…)            |
| Dossier de recherche local    | (ex : ~/Paris-Appart-Hunt)                             |

---

## Notes de priorisation spécifiques

Règles personnelles qui affinent HAUTE/MOYENNE/BASSE au-delà de `skill.md` — ex : "trajet > 45 min pour l'un des deux → BASSE", "pas d'ascenseur au-dessus du 3e → MOYENNE", "balcon = +1 niveau", exceptions coup de cœur.
