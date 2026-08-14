# Chemin de connexion, plateforme par plateforme

Ce document est la partie opérationnelle : quels comptes ouvrir, dans quel
ordre, ce que chaque étape demande, et combien de temps elle prend réellement.

## Vue d'ensemble

```
                      ┌──────────────────────────┐
   Vidéo source ─────▶│  Ta machine / un VPS     │
   (YouTube, rushes)  │  ffmpeg + Python         │
                      └───────────┬──────────────┘
                                  │
              ┌───────────────────┼────────────────────┐
              ▼                   ▼                    ▼
      ┌───────────────┐   ┌───────────────┐   ┌─────────────────┐
      │  Anthropic    │   │  Whisper      │   │  Cloudflare R2  │
      │  (rédaction)  │   │  (local)      │   │  (URL publique) │
      └───────────────┘   └───────────────┘   └────────┬────────┘
                                                       │
                          ┌────────────────────────────┼──────────────┐
                          ▼                            ▼              ▼
                  ┌───────────────┐          ┌───────────────┐  ┌───────────┐
                  │ Meta Graph    │          │ TikTok        │  │ YouTube   │
                  │ (Instagram)   │          │ Content API   │  │ Data v3   │
                  └───────────────┘          └───────────────┘  └───────────┘
```

Six connexions au total. Trois sont des formalités (Anthropic, R2, YouTube),
trois demandent une validation humaine par la plateforme (Meta, TikTok, et
l'audit YouTube si tu dépasses les quotas par défaut).

## Ordre recommandé

Les délais de validation sont longs et parallélisables. Lance les demandes
d'accès **en premier**, elles tourneront pendant que tu construis le reste.

| Jour | Action | Blocage |
|---|---|---|
| J0 | Ouvrir les comptes développeur Meta et TikTok, soumettre les demandes | — |
| J0 | Créer la clé Anthropic + le bucket R2 | 15 min |
| J0 | Créer le projet Google Cloud + OAuth YouTube | 30 min |
| J1–J3 | Faire tourner la chaîne en local, rendus non publiés | — |
| J7–J21 | Réponse TikTok (audit) | bloque la publication publique TikTok |
| J14–J45 | Réponse Meta (App Review) | bloque la publication Instagram |

Tant que Meta et TikTok n'ont pas répondu, YouTube Shorts fonctionne seul :
c'est la plateforme la moins contraignante et un bon terrain de rodage.

---

## 1. Anthropic — rédaction (15 minutes)

Sert à deux choses : choisir les extraits dans la transcription, et rédiger
titres/descriptions/hashtags.

1. Compte sur <https://console.anthropic.com>.
2. **Settings → API Keys → Create Key**.
3. Coller dans `.env` : `ANTHROPIC_API_KEY=sk-ant-...`
4. Provisionner du crédit (Billing). Compte quelques euros par mois pour un
   rythme de 20 shorts/mois — voir [03-budget.md](03-budget.md).

Aucune validation, aucun délai.

---

## 2. Stockage objet — Cloudflare R2 (20 minutes)

**Cette étape n'est pas optionnelle.** L'API d'Instagram ne reçoit pas de
fichier : on lui donne une URL, et ce sont les serveurs de Meta qui
téléchargent la vidéo. Il faut donc un hébergement public joignable.

R2 plutôt que S3 pour une raison précise : **l'egress est gratuit**. Or ici
c'est Meta qui télécharge, donc tout le trafic est de l'egress. Sur S3, la
même chose se facture ~0,09 $/Go.

1. Compte Cloudflare → **R2 → Create bucket** (nom : `erchd-shorts`).
2. **Manage R2 API Tokens → Create API Token**, permission *Object Read &
   Write*, limitée à ce bucket.
3. Noter l'*Access Key ID*, la *Secret Access Key* et l'*endpoint*
   (`https://<account_id>.r2.cloudflarestorage.com`).
4. Dans les réglages du bucket, activer un accès public : soit le sous-domaine
   `r2.dev` fourni, soit un domaine à toi (`media.erchd.photos`) branché via
   **Custom Domains**. Le domaine perso est préférable : plus stable, et il
   évite qu'une URL `r2.dev` apparaisse dans tes journaux.
5. Renseigner les cinq variables `S3_*` dans `.env`.

**Vérification** : ouvre dans un navigateur privé l'URL d'un fichier que tu y
déposes. Si tu ne la vois pas sans être connecté, Meta ne la verra pas non
plus, et le conteneur Instagram restera bloqué en `IN_PROGRESS`.

---

## 3. YouTube — Data API v3 (30 minutes, sans validation)

Sert à publier les Shorts et, en mode `creative_commons`, à vérifier la
licence d'une vidéo avant de la télécharger.

1. <https://console.cloud.google.com> → **Créer un projet** (`erchd-shorts`).
2. **API et services → Bibliothèque** → activer **YouTube Data API v3**.
3. **Écran de consentement OAuth** → type *Externe*. Renseigner le nom de
   l'application, ton adresse, ton domaine. Ajouter la portée
   `https://www.googleapis.com/auth/youtube.upload`.
4. Ajoute ton compte Google dans **Utilisateurs test**, puis clique sur
   **Publier l'application** pour passer en *Production*.

   Ce second geste n'est pas optionnel : laissé en mode *Test*, Google fait
   expirer le `refresh_token` au bout de **7 jours** et la chaîne s'arrête sans
   prévenir. Le passage en Production est immédiat et ne déclenche aucune
   vérification tant que tu es le seul utilisateur — la validation Google ne
   concerne que l'ouverture de l'outil à des tiers.
5. **Identifiants → Créer des identifiants → ID client OAuth**, type
   *Application de bureau*. Noter l'ID client et le secret dans `.env`.
6. Générer le jeton de rafraîchissement :

   ```bash
   cd automation && python -m src.cli auth-youtube
   ```

   Un navigateur s'ouvre, tu autorises, la commande affiche la ligne
   `YOUTUBE_REFRESH_TOKEN=...` à coller dans `.env`.

### Quotas

L'upload coûte environ **100 unités** et tire sur un compteur journalier dédié
d'environ **100 appels par jour**, distinct du quota de 10 000 unités qui
couvre les autres endpoints. Pour un rythme de quelques shorts par jour, c'est
largement suffisant.

Au-delà, il faut passer l'**audit de conformité YouTube API Services**
(formulaire *Audit and Quota Extension*), qui prend plusieurs semaines.

> ⚠️ En mode *Test*, le jeton de rafraîchissement Google **expire au bout de
> 7 jours**. Pour une chaîne qui tourne en continu, publie l'écran de
> consentement en mode *Production* (le passage est immédiat quand l'app
> n'utilise que des portées non sensibles pour ton propre compte).

---

## 4. Meta — Instagram Graph API (2 à 6 semaines)

La connexion la plus longue à obtenir, mais la mieux documentée.

### Prérequis côté compte

Le compte Instagram doit être **Professionnel** — *Entreprise* ou *Créateur*.
Un compte personnel n'a aucun accès à l'API.

- Application Instagram → **Paramètres → Type de compte → Basculer vers un
  compte professionnel**.

Deux chemins d'authentification existent, et le choix a des conséquences :

| | **Instagram Login** | **Facebook Login for Business** |
|---|---|---|
| Page Facebook liée | non requise pour un compte Créateur | requise |
| Mise en place | simple | plus lourde |
| Multi-comptes / Business Manager | non | oui |
| *Business Discovery* (lire les données publiques d'autres comptes) | non | oui |

**Pour ton cas — un seul compte, publication uniquement — prends Instagram
Login.** C'est le chemin léger, et c'est celui que le code implémente
(`graph.instagram.com`).

### Créer l'application

1. <https://developers.facebook.com> → **Mes applications → Créer une
   application** → cas d'usage *Autre* → type **Entreprise**.
2. Ajouter le produit **Instagram** → *API setup with Instagram login*.
3. Lier ton compte Instagram professionnel.
4. Demander les permissions :
   - `instagram_business_basic` — lecture du profil ;
   - `instagram_business_content_publish` — **c'est celle qui compte**.
5. Générer un jeton de test, récupérer l'`IG_USER_ID` et le token, les mettre
   dans `.env`. **À ce stade tu peux déjà publier sur ton propre compte** :
   le mode développement autorise jusqu'à 25 utilisateurs de test.

### Passer en production

Nécessaire seulement si tu veux sortir du mode développement. Pour un usage
strictement personnel sur ton propre compte, le mode développement suffit
souvent — vérifie-le avant de t'engager dans une App Review de plusieurs
semaines.

Si tu dois y aller :

1. **Vérification de l'entreprise** (Business Verification) : justificatif
   d'existence, souvent un extrait Kbis ou un avis de situation SIRENE pour
   un statut d'auto-entrepreneur. Compte 3 à 10 jours.
2. **App Review** pour `instagram_business_content_publish` : il faut fournir
   une vidéo d'écran montrant le parcours complet, et une description
   précise de l'usage. Compte 2 à 6 semaines, avec souvent un ou deux
   allers-retours.

### Gestion du jeton

Le jeton longue durée vaut **60 jours**. Il se prolonge de 60 jours à chaque
rafraîchissement, à condition d'avoir au moins 24 h d'existence.

```python
from src.publish.instagram import rafraichir_token
rafraichir_token()
```

Mets un rappel mensuel. Un jeton expiré casse la chaîne en silence :
l'erreur n'apparaît qu'à la publication suivante.

### Limites à connaître

- **25 publications par 24 h et par compte**, Stories comprises.
- **Reels : 90 secondes maximum via l'API**, alors que l'application mobile
  accepte 3 minutes. La configuration plafonne les extraits à 75 s pour
  garder de la marge.
- Ratio 9:16, H.264 ou HEVC, audio AAC.

---

## 5. TikTok — Content Posting API (30 minutes en mode brouillon)

La seule connexion où **l'automatisation *complète* est impossible avant
validation** — mais le mode brouillon en récupère l'essentiel sans aucune
attente.

### Deux modes, et un seul demande l'audit

C'est la distinction qui conditionne tout le parcours administratif.

| | **Brouillon** *(défaut)* | **Direct** |
|---|---|---|
| Scope | `video.upload` | `video.publish` |
| Audit | **aucun** | obligatoire, 1 à 3 semaines |
| Endpoint | `/v2/post/publish/inbox/video/init/` | `/v2/post/publish/video/init/` |
| Résultat | la vidéo arrive dans les brouillons du compte | publication publique immédiate |
| Geste restant | ouvrir l'app, coller la légende, publier | aucun |

**Le mode brouillon permet de démarrer le jour même.** Tout est automatisé —
découpe, recadrage, sous-titres, rédaction — sauf la publication finale, qui
prend vingt secondes depuis le téléphone et sert de dernière relecture. La
légende générée est écrite dans `var/rendus/<id>.tiktok.txt`, prête à copier :
en mode brouillon, l'API n'accepte pas de `post_info`, c'est le créateur qui
saisit la légende dans l'application.

Le mode direct est celui qui demande l'audit. Tant qu'il n'est pas validé, il
force la visibilité à `SELF_ONLY` **et** exige que le compte soit en privé au
moment de publier — autrement dit il n'apporte rien par rapport au brouillon.

Le connecteur gère les deux : `publication.tiktok_mode` dans `config.yaml`.

### Mise en place

1. <https://developers.tiktok.com> → **Manage apps → Connect an app**, connecté
   avec le compte TikTok qui publiera.
2. Ajouter le produit **Content Posting API**. **Ne pas activer *Direct Post***
   tant que tu restes en mode brouillon : c'est lui qui déclenche l'audit.
3. Portées : `user.info.basic` + `video.upload`. Ajouter `video.publish`
   seulement une fois l'audit validé.
4. Déclarer l'URL de redirection `http://localhost:8080/callback` et récupérer
   `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` dans `.env`.
5. Dérouler le parcours OAuth :

   ```bash
   cd automation && python -m src.cli auth-tiktok
   ```

   La commande affiche les lignes `TIKTOK_ACCESS_TOKEN=` et
   `TIKTOK_REFRESH_TOKEN=` à coller dans `.env`. Après l'audit, la rejouer avec
   `--mode direct` pour obtenir des jetons portant `video.publish`.

> **Pourquoi une commande dédiée plutôt qu'une bibliothèque OAuth générique.**
> TikTok impose PKCE aux applications de bureau, mais dérive le
> `code_challenge` par un SHA256 **hexadécimal** là où la RFC 7636 prescrit du
> base64url. Toute implémentation PKCE standard est donc rejetée — c'est la
> cause la plus fréquente d'échec sur cette intégration. Le port de la
> redirection est fixe (`--port` pour le changer) parce que TikTok la compare
> au caractère près avec celle déclarée à l'étape 4.

### L'audit

TikTok vérifie que l'intégration respecte ses **règles d'expérience** :

- un écran de consentement explicite avant publication ;
- la mention claire que le contenu sera publié sur TikTok ;
- le respect du choix entre brouillon et publication directe ;
- l'affichage des options renvoyées par `creator_info` (durée maximale,
  niveaux de confidentialité disponibles, interactions désactivées).

C'est pour cela que `src/publish/tiktok.py` appelle
`creator_info/query` avant chaque publication et refuse un niveau de
confidentialité non listé : sauter cet appel est un motif de refus.

### Jetons

**L'`access_token` TikTok expire en 24 heures.** Le rafraîchissement doit être
quotidien et automatisé — c'est la principale différence d'exploitation avec
Meta. Le parcours `auth-tiktok` ne se rejoue pas pour autant : le
`refresh_token` obtenu vaut un an.

```bash
python -m src.tokens tiktok      # écrit les nouvelles lignes sur stdout
```

TikTok fait aussi tourner le `refresh_token` à chaque rafraîchissement : il
faut réinjecter **les deux** valeurs, pas seulement l'`access_token`.

---

## 6. Transcription (optionnel — 10 minutes)

Par défaut la chaîne utilise **faster-whisper en local** : gratuit, aucune
donnée envoyée, ~1× temps réel sur un CPU récent.

Si tu préfères une API hébergée (mise en route plus rapide, meilleure
ponctuation sur l'audio de bord de terrain) :

1. Compte sur <https://www.assemblyai.com>, récupérer la clé.
2. `ASSEMBLYAI_API_KEY=` dans `.env`.
3. Dans `config.yaml` : `transcription.provider: assemblyai`.

Compte environ 0,15 $/heure d'audio.

---

## Comment me transmettre les secrets

**Ne colle jamais une clé d'API dans la conversation.** Tout ce qui est écrit
dans un fil de discussion peut être conservé dans un historique, et une clé
divulguée doit être révoquée.

Les trois manières correctes, par ordre de préférence :

1. **Tu les mets toi-même dans `automation/.env`** sur ta machine. Le fichier
   est déjà dans `.gitignore`. Je n'y ai pas accès et je n'en ai pas besoin :
   je peux écrire, corriger et tester tout le code sans jamais voir une clé.
2. **GitHub Secrets** si tu fais tourner la chaîne dans GitHub Actions :
   *Settings → Secrets and variables → Actions*. Je peux écrire le workflow
   qui les consomme sans les connaître.
3. **Un gestionnaire de secrets** (1Password, Doppler, AWS Secrets Manager)
   si tu passes sur un serveur.

Si une clé a déjà circulé quelque part, révoque-la et régénère-la : c'est
l'affaire de deux minutes sur chacune des consoles.

---

## Ce que je peux faire, et ce que tu dois faire

| Étape | Moi | Toi |
|---|---|---|
| Écrire et corriger le code de la chaîne | ✅ | |
| Concevoir les prompts de sélection et de rédaction | ✅ | |
| Écrire le workflow CI, les scripts de rafraîchissement de jetons | ✅ | |
| Diagnostiquer une erreur d'API à partir de son message | ✅ | |
| Créer les comptes développeur | | ✅ |
| Accepter les CGU des plateformes | | ✅ |
| Passer la vérification d'identité / d'entreprise | | ✅ |
| Cliquer dans les consoles Meta, TikTok, Google | | ✅ |
| Enregistrer la vidéo de démonstration pour l'App Review | | ✅ |
| Décider ce qui se publie | | ✅ |

La ligne de partage est simple : tout ce qui engage ton identité ou ta
responsabilité juridique te revient. Tout le reste, je peux le prendre.

---

## Ce dont j'ai besoin de ta part pour aller plus loin

Rien de tout cela ne bloque le fonctionnement actuel — ce sont les décisions
qui affineront la chaîne :

1. **Les vidéos sources.** L'angle éditorial dans `config.yaml` est calé sur
   « photographie de sport, explication technique ». Un lien vers deux ou
   trois vidéos réelles me permettrait de l'ajuster sur ta façon de parler.
2. **Le rythme visé.** 2 shorts/semaine et 2/jour ne mènent pas à la même
   architecture (le second justifie un serveur et une file d'attente).
3. **La police et le filigrane.** `templates/watermark.png` est à fournir, et
   la police Montserrat ExtraBold doit être installée sur la machine de rendu.
4. **Le niveau d'automatisation souhaité.** Aujourd'hui la validation humaine
   est active : rien ne part sans ton feu vert. Tu peux la désactiver dans
   `config.yaml`, mais je recommande de la garder les premières semaines.
