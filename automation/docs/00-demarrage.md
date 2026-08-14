# Démarrage — YouTube Shorts + TikTok

Guide pas-à-pas pour la configuration retenue : **YouTube + TikTok, sans
Instagram**. Compter une heure et demie en tout, en une seule fois.

---

## D'abord, la confusion à lever

Avoir un compte YouTube et un compte TikTok, c'est le **compte créateur** :
celui avec lequel tu publies depuis ton téléphone. C'est nécessaire, mais ça
ne suffit pas.

Pour qu'un programme publie à ta place, il faut en plus un **compte
développeur** et une **application** déclarée sur la plateforme. C'est gratuit,
c'est séparé, et c'est ce qui produit les clés que le code utilise.

```
   Compte créateur          Compte développeur         Application
   (tu l'as déjà)      +    (à créer, gratuit)    =    déclarée
        │                          │                       │
        └──────────────────────────┴───────────────────────┘
                                   ▼
                    Clés + jetons  →  automation/.env
```

L'application, c'est une fiche déclarative : un nom, une description, la liste
de ce que le programme a le droit de faire. Personne ne la voit à part toi.

---

## Ce que tu dois m'envoyer : **rien de secret**

C'est la réponse courte à ta question. Je n'ai besoin d'**aucun** identifiant,
mot de passe ou clé d'API.

| | Envoi |
|---|---|
| Mots de passe YouTube / TikTok | ❌ **jamais** |
| Clés d'API, jetons, secrets client | ❌ **jamais** — tu les mets toi-même dans `.env` |
| Un message d'erreur affiché par le terminal | ✅ utile, colle-le tel quel |
| Une capture d'un formulaire où tu bloques | ✅ utile |
| Le nom de ta chaîne YouTube, ton @ TikTok | ✅ sans risque, mais je n'en ai pas besoin |
| Deux ou trois liens de tes vidéos | ✅ utile pour caler l'angle éditorial |

**Pourquoi je n'en ai pas besoin :** le code ne contient aucune valeur en dur.
Il lit des variables d'environnement (`os.environ`). Je peux écrire, corriger
et tester toute la chaîne avec des cases vides — c'est exactement ce que j'ai
fait jusqu'ici.

Si un message d'erreur que tu me colles contient un bout de jeton, ce n'est pas
dramatique mais **révoque-le et régénère-le** : c'est deux minutes sur la
console concernée.

---

## Les délais — ce qu'ils sont vraiment

Les « 1 à 3 semaines » ne concernent **pas** la création du compte
développeur : ça, c'est immédiat. C'est l'**audit** que TikTok fait de ton
application avant de l'autoriser à publier **directement en public**. Un humain
chez TikTok vérifie que l'intégration respecte leurs règles.

Et **tu peux entièrement l'éviter au départ**, parce que TikTok a deux modes :

| Mode | Audit | Ce qui se passe |
|---|---|---|
| **Brouillon** *(retenu)* | ❌ aucun | la vidéo arrive dans tes brouillons TikTok, tu ouvres l'app et tu publies |
| Direct | ✅ 1 à 3 semaines | publication publique sans intervention |

En mode brouillon, tout est automatisé sauf le dernier geste : le montage, les
sous-titres, la légende. Tu ouvres TikTok, tu colles la légende, tu publies.
Ça prend vingt secondes et ça te sert de dernière relecture.

**Côté YouTube, il n'y a aucun délai** : la publication de Shorts fonctionne
dès la création du projet.

Tu peux donc être opérationnel **aujourd'hui**. L'audit TikTok se demandera
plus tard, quand le volume le justifiera.

---

## Étape 1 — Anthropic (15 min)

Oui, c'est un compte à créer, distinct de ton abonnement Claude. C'est le
compte *développeur* d'Anthropic, qui facture à l'usage.

1. <https://console.anthropic.com> → créer un compte.
2. **Billing** → ajouter un moyen de paiement et créditer **5 €**. C'est
   suffisant pour plus d'un an à ton rythme (~3 €/mois pour 20 shorts).
3. **Settings → API Keys → Create Key**. Nomme-la `erchd-shorts`.
4. Copie la clé **immédiatement** : elle ne s'affiche qu'une fois. Elle
   commence par `sk-ant-`.
5. Colle-la dans `automation/.env` :

   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

> Un abonnement Claude Pro ou Max ne donne pas accès à l'API : ce sont deux
> facturations séparées. Il faut bien créditer la console.

---

## Étape 2 — TikTok (30 min, aucune attente)

1. <https://developers.tiktok.com> → **Log in**, avec **le compte TikTok qui
   publiera**. C'est important : l'application sera liée à ce compte.
2. Accepter les conditions développeur.
3. **Manage apps → Connect an app**. Remplis :
   - *App name* : `erchd.photos shorts`
   - *Description* : « Outil personnel de découpe et de publication de shorts
     à partir de mes propres vidéos de photographie de sport. »
   - *Category* : Content & Publishing
   - *Website URL* : `https://erchd.photos`
4. Onglet **Products → add product → Content Posting API**.

   ⚠️ **N'active PAS « Direct Post »** pour l'instant : c'est lui qui déclenche
   l'audit. Laisse le mode brouillon.
5. Onglet **Scopes**, coche :
   - `user.info.basic`
   - `video.upload` ← **celui-ci, pas `video.publish`**
6. Onglet **App details** → note le **Client key** et le **Client secret**.
7. Dans **Redirect URI**, ajoute : `http://localhost:8080/callback`
8. Colle dans `.env` :

   ```
   TIKTOK_CLIENT_KEY=...
   TIKTOK_CLIENT_SECRET=...
   ```

Les deux jetons (`TIKTOK_ACCESS_TOKEN` et `TIKTOK_REFRESH_TOKEN`) s'obtiennent
ensuite par le parcours d'autorisation — dis-moi quand tu en es là, je te
prépare la commande qui le déroule.

---

## Étape 3 — YouTube / Google Cloud (30 min, aucune attente)

1. <https://console.cloud.google.com> → **Créer un projet** → `erchd-shorts`.
2. **API et services → Bibliothèque** → chercher **YouTube Data API v3** →
   **Activer**.
3. **API et services → Écran de consentement OAuth** :
   - Type : **Externe**
   - Nom de l'application : `erchd.photos shorts`
   - Adresse d'assistance et de contact : ton adresse
   - **Ajouter une portée** : `https://www.googleapis.com/auth/youtube.upload`
   - **Utilisateurs test** : ajoute ta propre adresse Google
4. **Important** : une fois l'écran rempli, clique sur **PUBLIER
   L'APPLICATION** pour passer en mode *Production*.

   Sinon le jeton expire tous les **7 jours** et la chaîne s'arrête sans
   prévenir. Le passage est immédiat et ne déclenche pas de vérification tant
   que tu n'utilises que ton propre compte.
5. **Identifiants → Créer des identifiants → ID client OAuth** :
   - Type d'application : **Application de bureau**
   - Nom : `erchd-shorts-cli`
6. Note l'**ID client** et le **Code secret**, colle-les dans `.env` :

   ```
   YOUTUBE_CLIENT_ID=...apps.googleusercontent.com
   YOUTUBE_CLIENT_SECRET=...
   ```
7. Génère le jeton de rafraîchissement :

   ```bash
   cd automation
   python -m src.cli auth-youtube
   ```

   Un navigateur s'ouvre, tu autorises avec ton compte Google. Google affichera
   un avertissement « Application non validée » : c'est normal, c'est ta propre
   application → **Paramètres avancés → Accéder à erchd.photos shorts**.

   La commande affiche alors la ligne à coller dans `.env` :

   ```
   YOUTUBE_REFRESH_TOKEN=1//...
   ```

---

## Étape 4 — Stockage objet : **pas nécessaire pour toi**

Le bucket Cloudflare R2 ne servait qu'à Instagram, qui télécharge la vidéo
depuis une URL publique. YouTube et TikTok reçoivent le fichier directement.

**Tu peux ignorer toutes les variables `S3_*`.** Elles restent dans
`.env.example` au cas où tu rallumerais Instagram plus tard.

---

## Étape 5 — Vérifier

```bash
cd automation
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
python -m src.doctor
```

Ce que tu dois voir :

```
Secrets — préparation (montage)
 ✓ ANTHROPIC_API_KEY
```

Les lignes `S3_*` et `IG_*` resteront marquées `!` (jaune) : c'est normal,
elles sont optionnelles et Instagram est désactivé.

---

## Étape 6 — Premier passage

```bash
python -m src.cli preparer "https://www.youtube.com/watch?v=TON_ID"
python -m src.cli revue --detail
```

Regarde les rendus dans `var/rendus/`, puis :

```bash
python -m src.cli valider <id-de-l-extrait>
python -m src.cli publier
```

Ce qui se passe alors :

- **YouTube** : le Short est téléversé en **privé** (réglage
  `youtube_visibilite` dans `config.yaml`). Tu le passes en public depuis
  YouTube Studio quand il te convient.
- **TikTok** : la vidéo arrive dans tes **brouillons**. La légende générée est
  écrite dans `var/rendus/<id>.tiktok.txt`, prête à copier. Tu ouvres
  l'application, tu colles, tu publies.

---

## Récapitulatif : ton `.env` final

```bash
# Indispensable
ANTHROPIC_API_KEY=sk-ant-...

# TikTok
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
TIKTOK_ACCESS_TOKEN=          # obtenu au parcours d'autorisation
TIKTOK_REFRESH_TOKEN=         # idem

# YouTube
YOUTUBE_CLIENT_ID=...apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=...
YOUTUBE_REFRESH_TOKEN=1//...

# Tout le reste (S3_*, IG_*) : laisser vide
```

Ce fichier ne quitte jamais ta machine — il est dans `.gitignore`.

---

## Le seul entretien à prévoir

L'`access_token` TikTok **expire toutes les 24 heures**. Tant que tu lances la
chaîne à la main, `python -m src.tokens` avant chaque session suffit. Quand tu
passeras à un rythme régulier, on le mettra en tâche planifiée.

Côté YouTube, si tu as bien publié l'écran de consentement en *Production*, il
n'y a rien à faire.

---

## Et si tu veux la publication TikTok automatique plus tard

Il faudra passer l'audit :

1. Activer **Direct Post** dans les produits de l'application.
2. Ajouter le scope `video.publish`.
3. Soumettre le formulaire d'audit : description de l'usage, volumes
   attendus, et une **vidéo d'écran** montrant le parcours complet.
4. Attendre 1 à 3 semaines, avec souvent un ou deux allers-retours.
5. Une fois validé : `tiktok_mode: "direct"` dans `config.yaml`.

Rien d'autre ne change dans le code — le connecteur gère déjà les deux modes.
