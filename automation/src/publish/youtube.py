"""Publication d'un Short via l'API YouTube Data v3.

Chemin de connexion :
    Projet Google Cloud -> activer « YouTube Data API v3 »
      -> ecran de consentement OAuth (externe)
      -> identifiants OAuth de type « Application de bureau »
      -> `python -m src.cli auth-youtube` genere le refresh token

Ce qui compte pour qu'une video soit traitee comme un Short :
  - ratio vertical (9:16) ;
  - duree inferieure a 3 minutes ;
  - le hashtag #Shorts dans le titre ou la description aide au classement
    mais n'est plus strictement necessaire.

Quotas : l'upload consomme environ 100 unites (contre 1 600 auparavant) et
tire sur un compteur journalier dedie d'environ 100 appels, distinct du quota
de 10 000 unites qui couvre les autres endpoints. Pour un depassement, il faut
passer l'audit de conformite YouTube API Services.
"""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from ..config import secret
from ..models import Extrait, Metadonnees
from . import ErreurPublication

PLATEFORME = "youtube"
PORTEES = ["https://www.googleapis.com/auth/youtube.upload"]


def _service():
    identifiants = Credentials(
        token=None,
        refresh_token=secret("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=secret("YOUTUBE_CLIENT_ID"),
        client_secret=secret("YOUTUBE_CLIENT_SECRET"),
        scopes=PORTEES,
    )
    identifiants.refresh(Request())
    return build("youtube", "v3", credentials=identifiants, cache_discovery=False)


def publier(
    extrait: Extrait,
    metadonnees: Metadonnees,
    visibilite: str = "private",
) -> str:
    """Televerse le short.

    `visibilite` vaut 'private' par defaut : c'est le reglage prudent pour les
    premieres executions. Passe a 'public' une fois la chaine eprouvee, ou
    utilise 'unlisted' pour une relecture avant diffusion.
    """
    if not extrait.chemin_rendu:
        raise ErreurPublication(PLATEFORME, "aucun fichier rendu pour cet extrait")

    chemin = Path(extrait.chemin_rendu)
    titre = metadonnees.titre
    if "#Shorts" not in titre and len(titre) < 92:
        titre = f"{titre} #Shorts"

    corps = {
        "snippet": {
            "title": titre[:100],
            "description": metadonnees.description[:5000],
            "tags": metadonnees.hashtags[:15],
            "categoryId": "22",   # People & Blogs
        },
        "status": {
            "privacyStatus": visibilite,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(chemin), chunksize=-1, resumable=True, mimetype="video/mp4")

    try:
        requete = _service().videos().insert(
            part="snippet,status", body=corps, media_body=media
        )
        reponse = None
        while reponse is None:
            _, reponse = requete.next_chunk()
    except HttpError as erreur:
        indice = ""
        if erreur.resp.status == 403 and "quota" in str(erreur).lower():
            indice = (
                " — quota journalier d'upload epuise. Il se reinitialise a minuit "
                "heure du Pacifique ; au-dela, demande une extension via l'audit "
                "de conformite YouTube API Services."
            )
        raise ErreurPublication(
            PLATEFORME, f"upload refuse : {erreur}{indice}", erreur
        ) from erreur

    return reponse["id"]
