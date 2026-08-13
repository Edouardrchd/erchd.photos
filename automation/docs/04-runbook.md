# Exploitation au quotidien

## Le cycle normal

```bash
cd automation

# 1. Préparer : télécharge, transcrit, sélectionne, monte, rédige.
#    Aucune publication à ce stade.
python -m src.cli preparer "https://www.youtube.com/watch?v=XXXXXXXXXXX"

# 2. Passer en revue.
python -m src.cli revue --detail

# 3. Visionner les rendus, puis valider ceux qu'on garde.
open var/rendus/XXXXXXXXXXX-01.mp4
python -m src.cli valider XXXXXXXXXXX-01 XXXXXXXXXXX-03

# 4. Publier uniquement les extraits validés.
python -m src.cli publier
```

Le découpage en deux commandes est délibéré : la porte de validation humaine
se situe entre `preparer` et `publier`. Rien ne part vers une plateforme sans
un `valider` explicite.

Pour supprimer cette porte (à faire seulement après plusieurs semaines de
résultats stables) : `publication.validation_humaine: false` dans
`config.yaml`.

## Premier lancement

```bash
cd automation
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
cp .env.example .env          # puis remplir les secrets
python -m src.doctor          # contrôle de l'environnement
```

`doctor` sépare volontairement ce qui est nécessaire à la **préparation**
(ffmpeg, clé Anthropic) de ce qui ne l'est qu'à la **publication** (jetons des
plateformes). Tu peux donc travailler tout le montage avant d'avoir obtenu les
accès Meta et TikTok.

## Reprise après incident

Chaque étage écrit son résultat sur disque, et chaque étage relit ce qui
existe déjà :

| Fichier | Contenu | Effet si supprimé |
|---|---|---|
| `var/sources/<id>.mp4` | vidéo source | re-téléchargement |
| `var/audio/<id>.wav` | piste audio 16 kHz | ré-extraction (rapide) |
| `var/transcriptions/<id>.json` | mots horodatés | re-transcription (lent, payant) |
| `var/extraits/<id>-NN.json` | état de l'extrait | perte de la sélection |
| `var/extraits/<id>-NN.meta.json` | légendes des 3 plateformes | nouvel appel de rédaction |
| `var/rendus/<id>-NN.mp4` | rendu final | re-rendu |

Conséquence pratique : si un rendu échoue, relancer `preparer` ne repaie pas
la transcription ni la sélection.

`publier` est **idempotent par plateforme** : un extrait déjà publié sur
Instagram mais échoué sur TikTok ne sera republié que sur TikTok. La liste des
publications réussies vit dans `extrait.publications`.

## Entretien des jetons

C'est la principale cause de panne d'une chaîne de ce type. Deux échéances :

| Plateforme | Durée de vie | Fréquence de rafraîchissement |
|---|---|---|
| TikTok | **24 heures** | quotidienne, obligatoirement automatisée |
| Instagram | 60 jours | mensuelle |
| YouTube | jeton de rafraîchissement permanent (app en production) | aucune |

> ⚠️ Si l'écran de consentement Google est resté en mode *Test*, le jeton de
> rafraîchissement YouTube **expire au bout de 7 jours**. Passe l'application
> en *Production*.

Un jeton expiré ne provoque aucune alerte : l'erreur n'apparaît qu'à la
publication suivante. Automatise le rafraîchissement plutôt que d'y penser.

```yaml
# .github/workflows/tokens.yml
name: Rafraichissement des jetons
on:
  schedule:
    - cron: "0 4 * * *"      # TikTok, tous les jours à 4h UTC
    - cron: "0 5 1 * *"      # Instagram, le 1er du mois
  workflow_dispatch:

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r automation/requirements.txt
      - run: python -m src.tokens
        working-directory: automation
        env:
          TIKTOK_CLIENT_KEY:     ${{ secrets.TIKTOK_CLIENT_KEY }}
          TIKTOK_CLIENT_SECRET:  ${{ secrets.TIKTOK_CLIENT_SECRET }}
          TIKTOK_REFRESH_TOKEN:  ${{ secrets.TIKTOK_REFRESH_TOKEN }}
          IG_ACCESS_TOKEN:       ${{ secrets.IG_ACCESS_TOKEN }}
```

Le jeton renouvelé doit être réécrit dans le magasin de secrets — d'où
l'intérêt d'un gestionnaire dédié (Doppler, 1Password, AWS Secrets Manager)
plutôt que de GitHub Secrets, qui n'a pas d'API d'écriture simple.

## Diagnostic des pannes courantes

| Symptôme | Cause la plus fréquente | Correction |
|---|---|---|
| Instagram bloqué sur `IN_PROGRESS` puis délai dépassé | l'URL de la vidéo n'est pas joignable publiquement | ouvrir l'URL en navigation privée ; vérifier l'accès public du bucket R2 |
| Instagram `ERROR` au transcodage | ratio, durée ou codec hors spécifications | vérifier 9:16, < 90 s, H.264/AAC |
| TikTok `spam_risk_too_many_posts` | application non auditée, ou plafond createur atteint | attendre 24 h, ou terminer l'audit |
| TikTok publie en `SELF_ONLY` | application non auditée | comportement normal ; passer les vidéos en public à la main |
| YouTube HTTP 403 « quota » | quota journalier d'upload épuisé | attendre la réinitialisation (minuit heure du Pacifique) |
| Sous-titres absents du rendu | police introuvable, ou chemin `.ass` mal échappé | `fc-list \| grep Montserrat` ; le code lance ffmpeg depuis le dossier du `.ass` pour éviter le problème |
| Sous-titres décalés | horodatage du modèle de transcription imprécis | passer sur un modèle Whisper plus grand (`large-v3`) |
| Le son paraît faible sur TikTok | `loudnorm` désactivé | `montage.loudnorm: true` |
| Une virgule parasite avant le texte des sous-titres | champ `Dialogue` en trop dans le fichier ASS | 8 virgules exactement avant le champ Text |

## Contrôle qualité avant validation

Ce qu'il faut regarder sur chaque rendu, dans cet ordre :

1. **Les trois premières secondes.** Si l'accroche démarre au milieu d'un mot
   ou sur un « donc », l'extrait est à jeter quelle que soit la suite.
2. **La fin.** Une phrase coupée est plus pénalisante qu'un extrait court.
3. **Le calage des sous-titres.** Un décalage de plus de 200 ms se voit.
4. **Le cadrage.** En `blur_pad`, l'image doit rester lisible ; si le sujet est
   déjà petit dans le 16:9, `crop_centre` donne un meilleur résultat.
5. **La légende.** C'est là que le modèle se trompe le plus souvent : il
   reformule parfois une affirmation en la durcissant.

## Recadrage intelligent

Le mode `crop_suivi` est déclaré dans la configuration mais **non implémenté** :
il lève une exception explicite. Il demande une détection du sujet image par
image puis un lissage de trajectoire, sans quoi le cadre tremble et le résultat
est pire qu'un recadrage fixe.

Pistes si tu veux l'ajouter plus tard :

- détection de visage/personne par image via un petit modèle
  (YOLO-n, MediaPipe) échantillonné à 5 images/seconde ;
- lissage de la trajectoire du centre par moyenne glissante ou filtre de
  Kalman, avec seuil de déclenchement pour éviter les micro-mouvements ;
- injection dans ffmpeg via le filtre `crop` avec expressions temporelles, ou
  génération d'une piste de commandes `sendcmd`.

En pratique, sur de la photographie de sport où l'on parle face caméra,
`blur_pad` suffit et préserve la composition de l'image, ce qui est souvent
le sujet même du propos.

## Planification

Les créneaux de `config.yaml` ne sont pas encore câblés à un ordonnanceur :
`publier` publie immédiatement. Pour étaler les publications, la voie la plus
simple est un `cron` qui appelle `publier --id <extrait>` aux heures voulues,
ou un workflow GitHub Actions déclenché par `schedule`.

Ne publie pas les trois plateformes à la seconde près : un décalage de
quelques dizaines de minutes évite que les algorithmes voient un contenu
strictement identique publié simultanément.
