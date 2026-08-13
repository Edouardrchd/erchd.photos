"""Publication via la Content Posting API de TikTok.

C'est la connexion la plus contraignante des trois. Deux etats possibles pour
une application, et la difference est structurante :

  NON AUDITEE   5 utilisateurs maximum, le compte doit etre en prive au
                moment de la publication, et le contenu est force en
                SELF_ONLY (visible de toi seul). Pour le rendre public il
                faut passer le compte en public PUIS changer la visibilite
                de chaque video a la main. Autrement dit : l'automatisation
                de bout en bout n'existe pas tant que l'audit n'est pas passe.

  AUDITEE       publication directe et publique. Soumise a un plafond
                journalier par createur, fixe selon les volumes declares
                dans le formulaire d'audit.

L'audit verifie que l'integration respecte les regles d'experience imposees
par TikTok : ecran de consentement, mention explicite que la publication se
fera sur TikTok, respect du choix brouillon / publication directe, et
affichage des options de creator_info.

Le flux d'appels :
    1. POST /v2/post/publish/creator_info/query/   obligatoire, renvoie les
       options autorisees pour ce createur (duree max, confidentialites
       disponibles, interactions desactivees)
    2. POST /v2/post/publish/video/init/           ouvre la session d'upload
    3. PUT  <upload_url>                            envoi du fichier
    4. POST /v2/post/publish/status/fetch/          suivi jusqu'a PUBLISH_COMPLETE
"""

from __future__ import annotations

import time
from pathlib import Path

import requests

from ..config import secret
from ..models import Extrait, Metadonnees
from . import ErreurPublication

PLATEFORME = "tiktok"
BASE = "https://open.tiktokapis.com/v2"
DELAI_MAX_S = 600
INTERVALLE_S = 6


def _entetes() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {secret('TIKTOK_ACCESS_TOKEN')}",
        "Content-Type": "application/json; charset=UTF-8",
    }


def infos_createur() -> dict:
    """Appel obligatoire avant toute publication (regle d'experience TikTok).

    Renvoie notamment `privacy_level_options`, `max_video_post_duration_sec`
    et les interactions desactivees par le createur. Publier sans avoir
    consulte ces valeurs est un motif de refus a l'audit.
    """
    reponse = requests.post(
        f"{BASE}/post/publish/creator_info/query/", headers=_entetes(), timeout=30
    )
    charge = reponse.json()
    if charge.get("error", {}).get("code") not in (None, "ok"):
        raise ErreurPublication(
            PLATEFORME, f"creator_info refuse : {charge['error']}", charge
        )
    return charge.get("data", {})


def _init_upload(chemin: Path, metadonnees: Metadonnees, confidentialite: str) -> dict:
    taille = chemin.stat().st_size
    corps = {
        "post_info": {
            "title": metadonnees.description[:2200],
            "privacy_level": confidentialite,
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            # Obligatoire quand le contenu est genere ou assiste par IA.
            # Voir docs/02-droits.md sur la declaration de contenu synthetique.
            "is_aigc": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": taille,
            "chunk_size": taille,   # envoi en une fois : nos shorts font < 64 Mo
            "total_chunk_count": 1,
        },
    }

    reponse = requests.post(
        f"{BASE}/post/publish/video/init/",
        headers=_entetes(),
        json=corps,
        timeout=60,
    )
    charge = reponse.json()
    erreur = charge.get("error", {})
    if erreur.get("code") not in (None, "ok"):
        indice = ""
        if "unaudited" in str(erreur).lower() or erreur.get("code") == "spam_risk_too_many_posts":
            indice = (
                " — application probablement non auditee : la publication publique "
                "est impossible tant que l'audit n'est pas valide."
            )
        raise ErreurPublication(PLATEFORME, f"init refuse : {erreur}{indice}", charge)
    return charge["data"]


def _envoyer_fichier(url_upload: str, chemin: Path) -> None:
    taille = chemin.stat().st_size
    with chemin.open("rb") as flux:
        reponse = requests.put(
            url_upload,
            data=flux,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{taille - 1}/{taille}",
            },
            timeout=900,
        )
    if reponse.status_code not in (200, 201, 204):
        raise ErreurPublication(
            PLATEFORME,
            f"televersement echoue (HTTP {reponse.status_code}) : {reponse.text[:500]}",
        )


def _attendre_publication(publish_id: str) -> str:
    debut = time.monotonic()
    while time.monotonic() - debut < DELAI_MAX_S:
        reponse = requests.post(
            f"{BASE}/post/publish/status/fetch/",
            headers=_entetes(),
            json={"publish_id": publish_id},
            timeout=30,
        )
        data = reponse.json().get("data", {})
        statut = data.get("status")

        if statut == "PUBLISH_COMPLETE":
            return publish_id
        if statut == "FAILED":
            raise ErreurPublication(
                PLATEFORME,
                f"TikTok a rejete la video : {data.get('fail_reason')}",
                data,
            )
        time.sleep(INTERVALLE_S)

    raise ErreurPublication(
        PLATEFORME, f"statut toujours en attente apres {DELAI_MAX_S} s"
    )


def publier(
    extrait: Extrait, metadonnees: Metadonnees, confidentialite: str | None = None
) -> str:
    if not extrait.chemin_rendu:
        raise ErreurPublication(PLATEFORME, "aucun fichier rendu pour cet extrait")

    chemin = Path(extrait.chemin_rendu)
    infos = infos_createur()
    options = infos.get("privacy_level_options", [])

    if confidentialite is None:
        # Si l'app n'est pas auditee, SELF_ONLY est la seule valeur acceptee.
        confidentialite = (
            "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in options else "SELF_ONLY"
        )

    if confidentialite not in options and options:
        raise ErreurPublication(
            PLATEFORME,
            f"confidentialite '{confidentialite}' non autorisee pour ce compte. "
            f"Valeurs disponibles : {options}",
        )

    duree_max = infos.get("max_video_post_duration_sec")
    if duree_max and extrait.duree > duree_max:
        raise ErreurPublication(
            PLATEFORME,
            f"extrait de {extrait.duree:.0f} s, plafond du compte : {duree_max} s",
        )

    session = _init_upload(chemin, metadonnees, confidentialite)
    _envoyer_fichier(session["upload_url"], chemin)
    return _attendre_publication(session["publish_id"])


def rafraichir_token() -> dict:
    """Les access tokens TikTok expirent en 24 h : ce rafraichissement est quotidien."""
    reponse = requests.post(
        f"{BASE}/oauth/token/",
        data={
            "client_key": secret("TIKTOK_CLIENT_KEY"),
            "client_secret": secret("TIKTOK_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": secret("TIKTOK_REFRESH_TOKEN"),
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    charge = reponse.json()
    if "access_token" not in charge:
        raise ErreurPublication(
            PLATEFORME, f"rafraichissement du token impossible : {charge}", charge
        )
    return charge
