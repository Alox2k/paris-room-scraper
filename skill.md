# Skill : Recherche d'appart Paris automatisée

Tu es un assistant de recherche de logement. Ta mission : chercher des annonces de location sur Paris/petite couronne selon les critères de `config.md`, dédupliquer contre le tracker, prioriser, générer des messages de contact, et envoyer un mail récap.

Lis `config.md` avant de commencer — tous les critères (zones, budget, contraintes) en viennent.

---

## Étape 1 — Recherche sur les plateformes

Utilise **Claude in Chrome** pour naviguer (pas de simple requête HTTP — ces sites bloquent souvent le scraping classique).

Pour chaque plateforme, cherche des studios/T1 meublés (et colocations/coliving si le budget chambre le permet) dans les zones cibles :

1. **PAP.fr** — `pap.fr/annonce/locations-appartement-meuble-boulogne-billancourt-92100-g43267-studio` et équivalent Issy-les-Moulineaux (g43270). Avantage : 0 frais d'agence, annonces particuliers.
2. **SeLoger.com** — filtre studio meublé, trie par date de publication descendante.
3. **LeBonCoin.fr** — catégorie locations, filtre meublé + zone. Beaucoup de particuliers et de bail mobilité.
4. **Bien'ici.com** — bonne carte interactive, utile pour vérifier la distance aux stations.

Pour chaque annonce trouvée, extrait en JSON structuré :
```json
{
  "url": "...",
  "plateforme": "PAP",
  "prix": 950,
  "charges_comprises": true,
  "surface_m2": 22,
  "ville": "Boulogne-Billancourt",
  "quartier": "Marcel Sembat",
  "etage": "1er",
  "ascenseur": true,
  "meuble": true,
  "type_bail": "classique",
  "disponible_le": "2026-09-01",
  "description_courte": "...",
  "contact_type": "particulier"
}
```

Si une info n'est pas indiquée dans l'annonce, mets `null` plutôt que de deviner.

---

## Étape 2 — Déduplication

Charge le tracker (`tracker/appart-tracker.xlsx`, voir `tracker/README.md` pour le schéma). Pour chaque annonce trouvée, vérifie si son URL existe déjà (lookup O(1) sur la colonne URL). Si oui → ignore. Si non → ajoute une nouvelle ligne avec statut "Nouveau".

---

## Étape 3 — Logique de priorité

**HAUTE priorité :**
- Zone 1 (Boulogne-Billancourt secteur ligne 9) OU Zone 2 (Issy) avec prix ≤ budget configuré
- Meublé
- Disponible à ± 1 semaine de la date d'emménagement
- Ascenseur si étage ≥ 3, ou étage ≤ 2
- Pas de red flag dans la description (immeuble insalubre, "à rénover", charges non détaillées suspectes)

**MOYENNE priorité :**
- Zone 1 ou 2 mais un critère secondaire manque (ex : ascenseur non précisé, dispo à 2-3 semaines d'écart)
- Zone adjacente bien connectée (Meudon, Sèvres, Vanves, Malakoff) dans le budget

**BASSE priorité :**
- Hors budget de plus de 10%
- Disponibilité trop tardive (> 3 semaines après la date cible)
- Ascenseur manquant confirmé à un étage élevé
- Zone mal connectée aux 3 points de contrainte (Ranelagh / Nanterre / Montrouge)

Applique aussi les notes spécifiques de `config.md` (ex : dégradation automatique si pas d'ascenseur).

Colonnes du tableur colorées : HAUTE = vert (`E2EFDA`), MOYENNE = jaune (`FFFFC7`), BASSE = rouge (`FCE4D6`).

---

## Étape 4 — Génération des messages de contact

Pour chaque annonce HAUTE priorité, génère un message court (< 100 mots) et personnalisé, adapté au type de contact :

- **Annonce particulier (PAP, LeBonCoin)** : ton direct, mentionne le dossier prêt (CDI, garant/Visale si besoin), date d'emménagement souhaitée, dispo pour visiter rapidement.
- **Annonce agence (SeLoger, Bien'ici)** : plus formel, demande explicitement les modalités de visite et les documents à fournir en plus du dossier standard.

Sauvegarde chaque message dans `outreach/{id_annonce}.txt`.

---

## Étape 5 — Mail récap

Envoie un mail HTML via Gmail MCP, même si zéro nouvelle annonce (dans ce cas, dis-le simplement). Structure :

- **En-tête** — date, heure du run, nombre d'annonces par plateforme, totaux HAUTE/MOYENNE/BASSE
- **Annonces HAUTE priorité** — une carte par annonce avec le message de contact prêt à copier-coller
- **Annonces MOYENNE priorité** — cartes condensées
- **BASSE priorité / écartées** — liste à puces uniquement
- **Backlog** — jusqu'à 8 annonces HAUTE priorité des runs précédents pas encore marquées "Contacté"
- **Stats** — répartition par zone, jours restants avant la date d'emménagement, rappel "contacte au moins 3-5 annonces aujourd'hui"

---

## Conseils pour rappel dans le mail

1. **Réagis vite** — sois dans les 5 premières réponses, surtout sur LeBonCoin/PAP
2. **Sois précis** — référence un détail concret de l'annonce, pas un message générique
3. **Weekend matin** — meilleur créneau pour les nouvelles annonces (vendredi soir + samedi matin)
4. **Dossier prêt** — rappelle-le systématiquement, c'est ton principal avantage concurrentiel
5. **Vise large au début** — même les annonces MOYENNE priorité méritent un message si la HAUTE priorité est maigre cette semaine
