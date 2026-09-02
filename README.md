# Paris Property Hunt

Adapté de [london-property-hunt](https://github.com/mikepapadim/london-property-hunt-public) pour une recherche d'appartement à Paris/petite couronne.

Workflow IA qui cherche sur les plateformes de location parisiennes, suit les annonces dans un tableur, priorise selon tes critères, et t'envoie un mail récap automatiquement.

---

## Ce que ça fait

1. **Cherche sur 4 plateformes** — PAP, SeLoger, LeBonCoin, Bien'ici, sur tes zones cibles
2. **Déduplique** contre ton tableur de suivi (par URL)
3. **Priorise** les annonces en HAUTE / MOYENNE / BASSE selon tes critères
4. **Génère des messages de contact** prêts à envoyer pour chaque annonce HAUTE priorité
5. **T'envoie un mail récap** avec cartes cliquables, messages prêts à l'emploi, et un backlog des annonces pas encore contactées

Tourne sur un cron (ex : 8h et 19h, les meilleurs créneaux pour les nouvelles annonces à Paris). Effort humain entre deux runs : zéro.

---

## Structure du repo

```
paris-property-hunt/
├── README.md              ← toi, ici
├── skill.md                ← la skill Claude Code principale (copie-colle dans ton setup)
├── config.md                ← ta config perso, déjà pré-remplie avec tes critères
├── tracker/
│   └── README.md           ← schéma des colonnes du tableur
└── outreach/                ← les messages générés atterrissent ici (à ignorer dans git)
```

---

## Pré-requis

- **Claude Code** (CLI ou app desktop) — claude.ai/code
- **Claude in Chrome** (extension MCP) — pour scraper PAP/SeLoger/LeBonCoin/Bien'ici (ils bloquent souvent le scraping API classique, d'où le passage par navigateur réel)
- **Gmail MCP connector** — pour l'envoi du mail récap
- Python 3 + openpyxl (`pip install openpyxl`) — pour la mise à jour du tableur

---

## Mise en place

### 1. Config

Copie `config.example.md` en `config.md` et remplis-le avec tes propres critères (zones, budget, contraintes de déplacement, date d'emménagement...). `config.md` est ignoré par git — il reste local, jamais commit.

```bash
cp config.example.md config.md
```

### 2. Créer le tableur de suivi

```bash
mkdir -p ~/Paris-Appart-Hunt/outreach
```

Le tableur se crée automatiquement au premier run, au chemin indiqué dans `config.md`. Schéma détaillé dans `tracker/README.md`.

### 3. Installer la skill dans Claude Code

Copie le contenu de `skill.md` comme nouvelle skill dans Claude Code, ou pointe ta config Claude Code vers ce fichier.

Ou lance-le manuellement :

```bash
claude "Lance la recherche d'appart Paris — cherche sur toutes les plateformes, mets à jour le tracker, envoie le mail"
```

### 4. Planifier

Dans Claude Code, utilise `/schedule` :

```
/schedule 0 8,19 * * * Lance la skill de recherche d'appart Paris
```

---

*Adapté du repo london-property-hunt de mikepapadim — Claude Code + Claude in Chrome + Gmail MCP*
