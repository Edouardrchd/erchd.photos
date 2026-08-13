"""Publication d'un Reel via l'API Graph d'Instagram.

Chemin de connexion (detail complet dans docs/01-connexions.md) :

    Compte Instagram en mode Professionnel
      -> App sur developers.facebook.com, produit « Instagram »
      -> permissions instagram_business_basic + instagram_business_content_publish
      -> verification de l'entreprise + App Review (2 a 6 semaines)
      -> token longue duree (60 jours), a rafraichir avant expiration

La publication se fait en trois appels, jamais en un seul :

    1. POST /{ig-user-id}/media          cree un conteneur, renvoie un creation_id
    2. GET  /{container-id}?fields=status_code   attend le statut FINISHED
    3. POST /{ig-user-id}/media_publish  publie le conteneur

L'etape 2 est celle qu'on oublie : Meta telecharge et transcode la video de
maniere asynchrone. Publier immediatement apres l'etape 1 echoue avec une
erreur peu explicite.

Contraintes de l'API Reels a respecter en amont (le montage s'en charge) :
  - ratio 9:16, duree entre 3 et 90 secondes cote API ;
  - H.264 ou HEVC, audio AAC ;
  - 25 publications par periode de 24 h et par compte, Stories comprises.
"""

from __future__ import annotations

import time

import requests

from ..config import secret
from ..models import Extrait, Metadonnees
from . import ErreurPublication

PLATEFORME = "instagram"
DELAI_MAX_S = 300     # 5 minutes : au-dela, le transcodage a echoue
INTERVALLE_S = 5


def _base() -> str:
    version = secret("IG_GRAPH_VERSION", requis=False) or "v21.0"
    return f"https://graph.instagram.com/{version}"


def _creer_conteneur(url_video: str, legende: str) -> str:
    reponse = requests.post(
        f"{_base()}/{secret('IG_USER_ID')}/media",
        data={
            "media_type": "REELS",
            "video_url": url_video,
            "caption": legende,
            "share_to_feed": "true",
            "access_token": secret("IG_ACCESS_TOKEN"),
        },
        timeout=60,
    )
    charge = reponse.json()
    if "id" not in charge:
        raise ErreurPublication(
            PLATEFORME,
            f"creation du conteneur refusee : {charge.get('error', charge)}",
            charge,
        )
    return charge["id"]


def _attendre_transcodage(container_id: str) -> None:
    """Boucle sur status_code jusqu'a FINISHED, ERROR ou expiration du delai."""
    debut = time.monotonic()
    while time.monotonic() - debut < DELAI_MAX_S:
        reponse = requests.get(
            f"{_base()}/{container_id}",
            params={
                "fields": "status_code,status",
                "access_token": secret("IG_ACCESS_TOKEN"),
            },
            timeout=30,
        )
        charge = reponse.json()
        statut = charge.get("status_code")

        if statut == "FINISHED":
            return
        if statut == "ERROR":
            raise ErreurPublication(
                PLATEFORME,
                f"Meta a rejete la video au transcodage : {charge.get('status')}. "
                "Verifie le ratio (9:16), la duree (< 90 s) et le codec (H.264/AAC).",
                charge,
            )
        if statut == "EXPIRED":
            raise ErreurPublication(
                PLATEFORME, "le conteneur a expire avant publication", charge
            )
        time.sleep(INTERVALLE_S)

    raise ErreurPublication(
        PLATEFORME,
        f"transcodage toujours en cours apres {DELAI_MAX_S} s. "
        "Cause frequente : l'URL de la video n'est pas joignable publiquement "
        "par les serveurs de Meta (bucket prive, redirection, ou domaine non resolu).",
    )


def publier(extrait: Extrait, metadonnees: Metadonnees) -> str:
    if not extrait.url_publique:
        raise ErreurPublication(
            PLATEFORME,
            "aucune URL publique : Instagram telecharge la video lui-meme, "
            "l'etape de televersement vers le stockage objet est obligatoire.",
        )

    container_id = _creer_conteneur(extrait.url_publique, metadonnees.description)
    _attendre_transcodage(container_id)

    reponse = requests.post(
        f"{_base()}/{secret('IG_USER_ID')}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": secret("IG_ACCESS_TOKEN"),
        },
        timeout=60,
    )
    charge = reponse.json()
    if "id" not in charge:
        raise ErreurPublication(
            PLATEFORME, f"publication refusee : {charge.get('error', charge)}", charge
        )
    return charge["id"]


def quota_restant() -> int | None:
    """Publications encore possibles sur les 24 h glissantes (limite : 25)."""
    reponse = requests.get(
        f"{_base()}/{secret('IG_USER_ID')}/content_publishing_limit",
        params={
            "fields": "quota_usage,config",
            "access_token": secret("IG_ACCESS_TOKEN"),
        },
        timeout=30,
    )
    data = reponse.json().get("data", [])
    if not data:
        return None
    entree = data[0]
    plafond = entree.get("config", {}).get("quota_total", 25)
    return plafond - entree.get("quota_usage", 0)


def rafraichir_token() -> dict:
    """Prolonge le token longue duree de 60 jours.

    A appeler au moins une fois par mois : un token expire casse la chaine
    silencieusement, l'erreur ne remonte qu'a la prochaine publication.
    Le token doit avoir au moins 24 h d'existence pour etre rafraichissable.
    """
    reponse = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={
            "grant_type": "ig_refresh_token",
            "access_token": secret("IG_ACCESS_TOKEN"),
        },
        timeout=30,
    )
    charge = reponse.json()
    if "access_token" not in charge:
        raise ErreurPublication(
            PLATEFORME, f"rafraichissement impossible : {charge}", charge
        )
    return charge
