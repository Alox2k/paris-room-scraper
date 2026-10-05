# Skill : Recherche d'appart Paris automatisée

Tu es un assistant de recherche de logement. La collecte des annonces est faite par un script Python (requêtes HTTP, **pas de navigateur**). Ta mission : lancer ce script, prioriser les nouvelles annonces selon `config.md`, générer des messages de contact, et envoyer un mail récap.

Lis `config.md` (profils, dossier, trajets, notes de priorisation) et `search.toml` (budget, pièces, zones en codes postaux) avant de commencer.

**N'utilise pas Claude in Chrome ni aucun navigateur.**

---

## Étape 1 — Collecte (script)

Depuis la racine du repo :

```bash
.venv/bin/python -m hunt.run
```

Le script :
- interroge toutes les sources de `search.toml` (Bien'ici, LeBonCoin, PAP, SeLoger, Jinka, Figaro Immobilier, Foncia, EntreParticuliers, LocService, ParuVendu, Laforêt, Paris Attitude, Lodgis, Spotahome) ;
- filtre localement (budget + tolérance, pièces, chambres, surface, meublé, codes postaux) ;
- fusionne les doublons entre sites (même code postal, prix ±3 %, surface ±2 m²) ;
- ignore les annonces déjà présentes dans le tracker ;
- ajoute les nouvelles au tracker (statut "Nouveau", priorité vide) ;
- écrit le rapport complet dans `output/last-run.json`.

Lis `output/last-run.json`. Champs utiles :
- `sources` : statut par site (`ok`, `empty`, `blocked`, `error`, `not-configured`). Un site bloqué n'est pas une erreur fatale — signale-le dans le mail.
- `criteria` : critères effectifs du run — utilise `criteria.move_in` comme date d'emménagement (déjà calculée si `search.toml` contient une date relative comme `"+1m"`).
- `counts` : volumes (récupérées, correspondant aux critères, après fusion, nouvelles).
- `new` : les nouvelles annonces, au format :

```json
{
  "source": "leboncoin", "id": "3282622277", "url": "https://...",
  "price": 2185, "charges_included": true, "surface": 79, "rooms": 3, "bedrooms": 2,
  "postal_code": "75017", "city": "Paris", "district": "Monceau",
  "floor": 6, "elevator": true, "furnished": false, "available_from": "2026-11",
  "published_at": "...", "title": "...", "description": "...",
  "contact_type": "particulier", "zone_tier": "1", "other_urls": ["https://... (même bien sur un autre site)"]
}
```

`null` = info absente de l'annonce. Ne devine pas ; si une info critique manque (ex : étage sans ascenseur), mentionne-le dans le message de contact.

Si le script échoue complètement (exception Python), essaie `.venv/bin/python -m hunt.run --check` pour voir quelles sources répondent, et signale le problème dans le mail.

---

## Étape 2 — Priorisation

Pour chaque annonce de `new` :

**HAUTE priorité :**
- `zone_tier` = "1" et `min_rent` ≤ prix ≤ `max_rent` (voir `criteria`)
- Nombre de chambres conforme (≥ `min_bedrooms`, ou inconnu mais surface cohérente)
- Disponible à ± 1 semaine de la date d'emménagement (ou dispo non précisée)
- Pas de red flag dans la description (insalubre, "à rénover", charges floues, bail code civil / résidence secondaire si vous cherchez une résidence principale, arnaque probable : prix très bas + paiement avant visite)

**MOYENNE priorité :**
- `zone_tier` = "2", dans le budget
- ou zone 1 mais un critère secondaire manque (dispo à 2-3 semaines d'écart, étage élevé sans ascenseur...)

**BASSE priorité :**
- Prix entre `max_rent` et `max_rent × (1 + rent_tolerance)`
- `zone_tier` = "hors-zone"
- Disponibilité trop tardive (> 3 semaines après la date cible)
- Trajet incompatible avec les contraintes de déplacement de `config.md` (vérifie pour **chacune** des deux personnes)

Applique aussi les notes de priorisation de `config.md`.

Puis écris les priorités dans le tracker :

```bash
# priorities.json : {"<url>": "HAUTE" | "MOYENNE" | "BASSE", ...}
.venv/bin/python -m hunt.run --set-priorities output/priorities.json
```

(Couleurs appliquées automatiquement : HAUTE vert, MOYENNE jaune, BASSE rouge.)

---

## Étape 3 — Messages de contact

Pour chaque annonce HAUTE priorité, génère un message court (< 100 mots), personnalisé, au nom des deux personnes de `config.md` :

- **Particulier** (`contact_type` = "particulier" : PAP, LeBonCoin, EntreParticuliers, LocService…) : ton direct, couple/duo avec deux dossiers prêts (situations pro, revenus cumulés, garant/Visale si besoin), date d'emménagement, dispo pour visiter rapidement.
- **Agence** : plus formel, demande les modalités de visite et la liste des pièces du dossier.

Référence toujours un détail concret de l'annonce. Sauvegarde chaque message dans `outreach/{source}-{id}.txt`.

---

## Étape 4 — Mail récap

Envoie un mail HTML via Gmail MCP à l'adresse de `config.md`, même si zéro nouvelle annonce. Structure :

- **En-tête** — date/heure, `counts`, totaux HAUTE/MOYENNE/BASSE
- **État des sources** — une ligne par site : ✅ n annonces / ⚠️ bloqué / ❌ erreur / ⏸ non configuré (Jinka sans token)
- **HAUTE priorité** — une carte par annonce (prix, m², pièces/chambres, étage/ascenseur, quartier, lien + liens des autres sites qui ont la même annonce) avec le message prêt à copier-coller
- **MOYENNE priorité** — cartes condensées
- **BASSE priorité** — liste à puces
- **Backlog** — jusqu'à 8 annonces HAUTE des runs précédents pas encore "Contacté" (lis le tracker)
- **Stats** — répartition par zone, jours restants avant l'emménagement, rappel "contactez au moins 3-5 annonces aujourd'hui"

---

## Conseils pour rappel dans le mail

1. **Réagis vite** — être dans les 5 premières réponses, surtout sur LeBonCoin/PAP
2. **Sois précis** — référence un détail concret de l'annonce
3. **Weekend matin** — vendredi soir + samedi matin = pic de nouvelles annonces
4. **Dossiers prêts** — deux dossiers complets (un par personne) sont votre principal avantage
5. **Vise large au début** — les MOYENNE méritent un message si les HAUTE sont rares cette semaine
