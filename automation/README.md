# Chaîne d'automatisation : vidéo longue → shorts publiés

Transforme une vidéo longue en plusieurs shorts verticaux sous-titrés, avec
titre, description et hashtags générés, puis les publie sur Instagram Reels,
TikTok et YouTube Shorts.

Ce module est autonome : il vit à côté du site `erchd.photos` sans interférer
avec lui.

---

## 1. Comment ça marche

Sept étages. Chacun écrit son résultat sur disque, ce qui rend la chaîne
reprenable : si le montage échoue, la transcription et la sélection ne sont
pas rejouées ni repayées.

```
  ①  SOURCE          vidéo YouTube ou fichier local          src/ingest.py
        ↓                (contrôle de licence)
  ②  TRANSCRIPTION   texte + horodatage au mot               src/transcribe.py
        ↓                (Whisper local ou API)
  ③  SÉLECTION       Claude choisit les N meilleurs passages src/segment.py
        ↓                (sortie contrainte par JSON Schema)
  ④  MONTAGE         découpe, 9:16, sous-titres, filigrane   src/edit.py
        ↓                (ffmpeg, une seule passe)           src/subtitles.py
  ⑤  RÉDACTION       titre, description, hashtags × 3        src/metadata.py
        ↓                plateformes
  ⑥  VALIDATION      ← porte humaine, activée par défaut     src/cli.py
        ↓
  ⑦  PUBLICATION     Instagram · TikTok · YouTube            src/publish/
```

L'étage ⑥ est la seule étape non automatique, et c'est volontaire. Voir
[§ 6](#6-la-porte-de-validation).

### Ce que chaque étage apporte

| Étage | Choix retenu | Pourquoi |
|---|---|---|
| Transcription | horodatage **au mot**, pas à la phrase | c'est ce qui permet le sous-titrage « karaoké » où le mot prononcé se colore — le standard visuel sur TikTok et Reels |
| Sélection | Claude Opus 5, sortie JSON Schema | l'étage où le jugement compte : un extrait doit tenir debout sorti de son contexte |
| Montage | ffmpeg, un seul ré-encodage | chaque génération de compression coûte de la qualité, avant même celle des plateformes |
| Rédaction | une requête pour les 3 plateformes | évite trois appels et trois angles différents |
| Publication | API officielles, pas d'automatisation d'interface | seule voie durable ; l'automatisation d'interface se casse et fait fermer les comptes |

---

## 2. Démarrage

```bash
cd automation
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp config.example.yaml config.yaml    # réglages éditoriaux, versionnable
cp .env.example .env                  # secrets, jamais versionné

python -m src.doctor                  # contrôle de l'environnement
```

Prérequis système : **ffmpeg ≥ 6.0** (`apt install ffmpeg` ou
`brew install ffmpeg`) et Python 3.11+.

`doctor` sépare volontairement ce qui est nécessaire à la **préparation**
(ffmpeg, clé Anthropic) de ce qui ne l'est qu'à la **publication** (jetons des
plateformes). Tu peux donc monter des shorts dès aujourd'hui, avant même
d'avoir obtenu les accès Meta et TikTok — qui prennent plusieurs semaines.

### Le cycle

```bash
python -m src.cli preparer "https://www.youtube.com/watch?v=XXXXXXXXXXX"
python -m src.cli revue --detail
open var/rendus/XXXXXXXXXXX-01.mp4          # visionner avant de valider
python -m src.cli valider XXXXXXXXXXX-01 XXXXXXXXXXX-03
python -m src.cli publier
```

---

## 3. Les connexions à mettre en place

Six connexions. Trois sont des formalités, trois demandent une validation
humaine par la plateforme. **Le détail pas-à-pas est dans
[docs/01-connexions.md](docs/01-connexions.md)** — ce tableau en donne la forme.

| Service | Rôle | Mise en place | Délai de validation |
|---|---|---|---|
| **Anthropic** | sélection + rédaction | 15 min | aucun |
| **Cloudflare R2** | URL publique de la vidéo | 20 min | aucun |
| **YouTube Data v3** | publication Shorts | 30 min | aucun (quotas par défaut) |
| **Meta / Instagram** | publication Reels | 1 h | **2 à 6 semaines** |
| **TikTok** | publication | 1 h | **1 à 3 semaines** |
| Transcription hébergée | *optionnel* | 10 min | aucun |

**Conseil d'ordonnancement** : lance les demandes Meta et TikTok le premier
jour. Elles tourneront pendant que tu construis et rodes le reste. YouTube
fonctionne seul dans l'intervalle, et c'est un bon terrain d'essai.

### Le point non négociable : le stockage objet

L'API d'Instagram **ne reçoit pas de fichier**. On lui transmet une URL, et ce
sont les serveurs de Meta qui téléchargent la vidéo. Un hébergement public
joignable est donc obligatoire, même temporaire.

Cloudflare R2 plutôt qu'AWS S3 pour une raison précise : **l'egress est
gratuit**, or ici tout le trafic est de l'egress (c'est Meta qui télécharge).
Sur S3 la même chose se facture ~0,09 $/Go.

### Les deux pièges qui cassent une chaîne de ce type

1. **Les jetons expirent.** L'`access_token` TikTok vaut **24 heures** —
   le rafraîchissement doit être quotidien et automatisé. Celui d'Instagram
   vaut 60 jours. Un jeton expiré ne déclenche aucune alerte : l'erreur
   n'apparaît qu'à la publication suivante. `python -m src.tokens` est fait
   pour tourner en tâche planifiée.

2. **TikTok non audité ne publie pas en public.** Tant que l'audit n'est pas
   passé, l'API force la visibilité à `SELF_ONLY` et exige que le compte soit
   privé au moment de publier. Le code le détecte et bascule proprement plutôt
   que d'échouer, mais l'automatisation de bout en bout n'existe qu'après
   validation.

---

## 4. Ce que je peux faire, et ce que tu dois faire

| | Moi | Toi |
|---|---|---|
| Écrire, corriger, tester le code | ✅ | |
| Concevoir les prompts de sélection et de rédaction | ✅ | |
| Écrire les workflows CI et les scripts de jetons | ✅ | |
| Diagnostiquer une erreur d'API depuis son message | ✅ | |
| Créer les comptes développeur | | ✅ |
| Accepter les CGU, passer la vérification d'identité | | ✅ |
| Cliquer dans les consoles Meta, TikTok, Google | | ✅ |
| Enregistrer la démo vidéo pour l'App Review Meta | | ✅ |
| Décider ce qui se publie | | ✅ |

La ligne de partage : **tout ce qui engage ton identité ou ta responsabilité
juridique te revient ; le reste, je peux le prendre.**

### Comment me transmettre les secrets

**Ne colle jamais une clé d'API dans une conversation.** Mets-les toi-même
dans `automation/.env` (déjà dans `.gitignore`) ou dans GitHub Secrets. Je
peux écrire, corriger et tester l'intégralité du code sans jamais voir une
clé — le code lit des variables d'environnement, pas des valeurs en dur.

Si une clé a déjà circulé quelque part, révoque-la et régénère-la.

---

## 5. Droits : à lire avant de viser des vidéos qui ne sont pas les tiennes

Tu m'as autorisé à utiliser des services externes, ce que j'ai fait. Mais
l'autorisation que tu peux me donner ne couvre pas les droits d'un tiers sur
sa vidéo — d'où ce garde-fou, qui est aussi une protection pour tes comptes.

| Cas | Mode | Verdict |
|---|---|---|
| **Tes propres vidéos** | `proprietaire` | ✅ recommandé — une vidéo de 15 min donne 5 à 8 shorts |
| **Vidéos tierces sous Creative Commons** | `creative_commons` | ✅ utilisable, attribution générée automatiquement |
| **Vidéos tierces sous licence standard** | *non implémenté* | ❌ CGU YouTube + droit d'auteur + détection Content ID |

Le troisième cas n'est pas implémenté délibérément. L'argument décisif n'est
même pas juridique : Content ID et ses équivalents chez Meta et TikTok
détectent le contenu réutilisé **y compris recadré, sous-titré et ré-encodé**.
Bâtir une audience sur un compte qui peut être fermé pour récidive est un
mauvais investissement.

En mode `creative_commons`, `src/ingest.py` interroge l'API YouTube pour lire
la licence **avant tout téléchargement** et refuse de continuer si elle n'est
pas CC.

Si tu veux exploiter du contenu tiers, la voie propre est la licence directe :
beaucoup de créateurs et de clubs accordent une autorisation écrite pour une
demande précise. Passe alors en mode `fichier` et conserve l'écrit.

Détail complet, dont le droit à l'image en photographie de sport et la
déclaration de contenu IA : **[docs/02-droits.md](docs/02-droits.md)**.

---

## 6. La porte de validation

Par défaut, `publier` ne traite que les extraits explicitement validés.
C'est le réglage `publication.validation_humaine: true`.

Ce n'est pas de la prudence de principe. Trois choses ne peuvent pas être
déléguées au code :

- **le droit à l'image** des personnes filmées, qui suppose un jugement de
  contexte ;
- **la justesse de la légende** : le modèle reformule parfois une affirmation
  en la durcissant ;
- **la qualité de l'accroche** : un extrait qui démarre sur un « donc » est à
  jeter quelle que soit la suite.

Compte 2 à 3 minutes de relecture par short. Sur 20 shorts, c'est une heure
par mois — plus que tout le reste réuni, mais c'est aussi là que tu affines
l'angle éditorial de `config.yaml`. Un prompt bien calé fait ensuite gagner ce
temps.

Tu peux désactiver la porte une fois la chaîne éprouvée.

---

## 7. Budget

Environ **4 € par mois** pour 20 shorts sur trois plateformes.

| Poste | Solution | Coût |
|---|---|---|
| Transcription | faster-whisper, local | 0 € |
| Sélection + rédaction | API Anthropic | ~3 € |
| Montage | ffmpeg, local | 0 € |
| Stockage / diffusion | Cloudflare R2 | ~0,50 € |
| Publication | API officielles | 0 € |

Les alternatives payantes existent et sont documentées, mais elles se
justifient rarement à cette échelle : une API de rendu vidéo coûte ~50 €/mois
pour éviter d'installer ffmpeg, un agrégateur de publication ~149 €/mois pour
éviter deux formulaires qu'on remplit une fois. Comparatif chiffré et seuils
de bascule : **[docs/03-budget.md](docs/03-budget.md)**.

Le vrai coût est ailleurs : les semaines de validation des plateformes, et
ton heure mensuelle de relecture.

---

## 8. Exploitation

Reprise après incident, entretien des jetons, tableau de diagnostic des
pannes courantes, contrôle qualité avant validation :
**[docs/04-runbook.md](docs/04-runbook.md)**.

---

## 9. État du module

**Vérifié par exécution réelle** — la chaîne de montage a été testée de bout
en bout (ffmpeg 7.0.2) : rendu 1080×1920 conforme, durée exacte, sous-titres
ASS incrustés avec coloration du mot actif, dans les deux modes de recadrage.

| Composant | État |
|---|---|
| Ingestion + contrôle de licence | écrit |
| Transcription (Whisper local / AssemblyAI) | écrit |
| Sélection par LLM, sortie contrainte | écrit |
| Génération des sous-titres ASS | **testé** |
| Montage ffmpeg `blur_pad` et `crop_centre` | **testé** |
| Rédaction des métadonnées ×3 plateformes | écrit |
| Stockage objet S3/R2 | écrit |
| Connecteurs Instagram · TikTok · YouTube | écrits |
| CLI, doctor, rafraîchissement des jetons | écrit |
| Recadrage avec suivi du sujet (`crop_suivi`) | **non implémenté** — lève une exception explicite |

Les composants marqués « écrit » n'ont pas pu être exécutés ici faute de
comptes et de jetons : ils sont écrits contre la documentation en vigueur des
API et lèvent des erreurs explicites, mais leur premier passage réel demandera
probablement des ajustements. C'est normal et attendu à cette étape.

`crop_suivi` est le seul manque assumé : un recadrage qui suit le sujet sans
lissage de trajectoire tremble, et rend un résultat pire qu'un cadrage fixe.
Pistes d'implémentation dans le runbook.

---

## Arborescence

```
automation/
├── README.md                   ce document
├── requirements.txt
├── config.example.yaml         réglages éditoriaux et techniques
├── .env.example                modèle de secrets
├── docs/
│   ├── 01-connexions.md        chemin de connexion, plateforme par plateforme
│   ├── 02-droits.md            cadre juridique et arbre de décision
│   ├── 03-budget.md            coûts et alternatives chiffrées
│   └── 04-runbook.md           exploitation, pannes, contrôle qualité
├── templates/
│   └── watermark.png           filigrane (à fournir)
└── src/
    ├── config.py               configuration + secrets
    ├── models.py               structures partagées, persistance JSON
    ├── ingest.py               ① source et licence
    ├── transcribe.py           ② transcription horodatée au mot
    ├── segment.py              ③ sélection des extraits
    ├── subtitles.py            ④a sous-titres ASS karaoké
    ├── edit.py                 ④b montage ffmpeg
    ├── metadata.py             ⑤ titres, descriptions, hashtags
    ├── storage.py              stockage objet → URL publique
    ├── publish/
    │   ├── instagram.py        conteneur → attente → publication
    │   ├── tiktok.py           creator_info → init → upload → statut
    │   └── youtube.py          upload résumable OAuth
    ├── cli.py                  orchestrateur
    ├── doctor.py               contrôle de l'environnement
    └── tokens.py               rafraîchissement des jetons
```
