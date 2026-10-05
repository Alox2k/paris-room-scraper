# Paris Property Hunt

Adapté de [london-property-hunt](https://github.com/mikepapadim/london-property-hunt-public) pour une recherche d'appartement à Paris/petite couronne — ici pour **deux personnes cherchant un 2 chambres**.

Un script Python récupère les annonces de 14 sites **par simples requêtes HTTP** (pas de navigateur, pas de Claude in Chrome), filtre selon tes critères et fusionne les doublons. Claude ne fait plus que ce qu'il fait bien : prioriser, écrire les messages de contact, envoyer le mail récap.

---

## Ce que ça fait

1. **Collecte** sur 14 sources (voir tableau) — `python -m hunt.run`
2. **Filtre** localement : budget, pièces, chambres, surface, meublé, codes postaux
3. **Fusionne** le même appart publié sur plusieurs sites (code postal + prix ±3 % + surface ±2 m²)
4. **Déduplique** contre le tracker Excel (URL + URLs des doublons)
5. **Claude priorise** HAUTE / MOYENNE / BASSE et colore le tracker
6. **Claude génère** des messages de contact pour les HAUTE priorité
7. **Claude envoie** un mail récap (Gmail MCP), avec l'état de chaque source

---

## Sources

Testées le 2026-10-05 avec `python -m hunt.run --check` (taux de remplissage des champs clés).

| Source | Méthode | Couverture | Qualité des données |
| --- | --- | --- | --- |
| **Bien'ici** | API JSON publique | 75/92/93/94 | excellente (prix, m², pièces, chambres, étage, ascenseur, meublé, CP) |
| **LeBonCoin** | JSON embarqué (`__NEXT_DATA__`) | 75/92/93/94 | excellente — mais protégé par DataDome, peut bloquer par moments |
| **PAP** | cartes HTML | 75/92/93/94 | bonne (prix, m², pièces, chambres, CP ; étage/meublé via description) |
| **SeLoger** | JSON embarqué (`__UFRN_FETCHER__`) | 75/92/93/94 | très bonne ; **Logic-Immo** (même inventaire) sert de secours si SeLoger bloque |
| **Figaro Immobilier** | payload Nuxt | 75/92/93/94 | très bonne |
| **Foncia** | API JSON | 75/92/93/94 | bonne (pas de nb de chambres) |
| **EntreParticuliers** | cartes HTML | 75/92/93/94 | correcte (pas de chambres) — particuliers |
| **LocService** | cartes HTML | 75/92/93/94 | correcte — particuliers |
| **ParuVendu** | cartes HTML | 75/92/93/94 | bonne |
| **Laforêt** | cartes HTML | 75/92/93/94 | bonne |
| **Paris Attitude** | cartes HTML | Paris, meublé | prix/m²/chambres ; **pas de code postal** (quartier seulement) |
| **Lodgis** | cartes HTML | Paris, meublé | bonne ; CP ~70 % |
| **Spotahome** | cartes HTML | Paris, meublé | **pas de code postal** |
| **Jinka** (agrégateur) | API de l'app | selon ton alerte | **non testé** — nécessite ton token (voir plus bas) |

Écartés : Orpi, Guy Hoquet (annonces chargées en JavaScript), La Carte des Colocs (bloqué), Superimmo (rate-limit 429), HousingAnywhere (données difficiles à extraire), Studapart/ImmoJeune (étudiants).

⚠️ **Ces scrapers casseront un jour** : quand un site change sa page, sa source passe en `error` ou `empty` dans le rapport — les autres continuent. Lance `python -m hunt.run --check` pour diagnostiquer. Reste raisonnable sur la fréquence (2 runs/jour, ~2 s entre requêtes) pour ne pas te faire bloquer.

---

## Structure du repo

```
paris-room-scraper/
├── README.md
├── skill.md               ← la skill Claude Code (lance le script, priorise, mail)
├── config.example.md      ← profils, dossier, trajets (→ config.md, ignoré par git)
├── search.example.toml    ← critères chiffrés pour les scrapers (→ search.toml, ignoré par git)
├── requirements.txt
├── hunt/
│   ├── run.py             ← point d'entrée : python -m hunt.run
│   ├── sources/           ← un module par site
│   ├── http.py            ← client HTTP "navigateur" (curl_cffi), pauses, retry
│   ├── cards.py           ← parseur générique de cartes HTML
│   ├── filters.py, dedup.py, tracker.py, geo.py, config.py, models.py
├── tracker/README.md      ← schéma du tableur
└── outreach/              ← messages générés (ignoré par git)
```

---

## Mise en place

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp config.example.md config.md          # profils, trajets, dossier, email
cp search.example.toml search.toml      # budget, pièces, codes postaux
```

Vérifie que tout répond :

```bash
.venv/bin/python -m hunt.run --check                 # toutes les sources, sans toucher au tracker
.venv/bin/python -m hunt.run --dry-run               # run complet sans écrire le tracker
.venv/bin/python -m hunt.run --only bienici,pap      # quelques sources seulement
```

Le rapport du dernier run est dans `output/last-run.json`.

### Jinka (optionnel, recommandé)

Jinka agrège gratuitement LeBonCoin, SeLoger, PAP, etc. Le script lit **tes** alertes Jinka :

1. Crée un compte sur [jinka.fr](https://www.jinka.fr) et une alerte correspondant à ta recherche.
2. Dans le navigateur connecté à Jinka : DevTools → Application → Cookies → `jinka.fr` → copie la valeur de `LA_API_TOKEN`.
3. `export JINKA_TOKEN="<la valeur>"` (dans ton shell ou ton `.env`, jamais dans le repo).

Le token expire de temps en temps : la source passera alors en `error` (HTTP 401) — recopie-le.

### Installer la skill

Copie `skill.md` comme skill Claude Code, ou lance :

```bash
claude "Lance la recherche d'appart Paris en suivant skill.md"
```

### Planifier

```
/schedule 0 8,19 * * * Lance la skill de recherche d'appart Paris
```

---

## Pré-requis

- Python 3.11+ (`tomllib`)
- Claude Code + **Gmail MCP** (mail récap) — plus besoin de Claude in Chrome

---

*Adapté du repo london-property-hunt de mikepapadim.*
