"""Etape 1 - Recuperation de la video source.

Trois modes, par ordre de securite juridique decroissante (docs/02-droits.md) :

  proprietaire       tes propres videos YouTube. Tu detiens les droits, aucune
                     restriction en aval.
  creative_commons   videos publiees sous CC-BY par leur auteur. Reutilisation
                     autorisee AVEC attribution obligatoire, que la chaine
                     injecte automatiquement dans la description.
  fichier            fichier deja present sur le disque (rushes perso, etc.).

Le mode `creative_commons` verifie la licence via l'API YouTube Data avant
tout telechargement, et refuse de continuer si la licence n'est pas CC.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import requests

from .config import Config, secret


@dataclass
class Source:
    video_id: str
    chemin: Path
    titre: str
    auteur: str
    licence: str          # "proprietaire" | "creativeCommon" | "local"
    url: str | None = None

    @property
    def attribution(self) -> str:
        """Ligne d'attribution a inserer dans la description (CC-BY)."""
        if self.licence != "creativeCommon":
            return ""
        return f"Extrait de « {self.titre} » par {self.auteur} — licence CC BY 3.0. Source : {self.url}"


def _verifier_licence(video_id: str, cle_api: str) -> dict:
    """Interroge l'API YouTube Data v3 pour la licence et les metadonnees.

    Cout : 1 unite de quota (endpoint videos.list).
    """
    reponse = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={"part": "snippet,status", "id": video_id, "key": cle_api},
        timeout=30,
    )
    reponse.raise_for_status()
    items = reponse.json().get("items", [])
    if not items:
        raise ValueError(f"Video {video_id} introuvable ou privee.")
    item = items[0]
    return {
        "titre": item["snippet"]["title"],
        "auteur": item["snippet"]["channelTitle"],
        "licence": item["status"]["license"],  # 'youtube' ou 'creativeCommon'
    }


def _telecharger(url: str, destination: Path) -> Path:
    """Telechargement via yt-dlp, en 1080p max, piste audio incluse."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    commande = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", str(destination),
        url,
    ]
    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(f"yt-dlp a echoue :\n{resultat.stderr[-2000:]}")
    return destination


def recuperer(cfg: Config, cible: str) -> Source:
    """Point d'entree de l'etape.

    `cible` est une URL YouTube, un identifiant de video, ou un chemin de
    fichier local selon le mode configure.
    """
    mode = cfg.source["mode"]
    dossier = cfg.dossier("sources")

    if mode == "fichier":
        chemin = Path(cible).expanduser().resolve()
        if not chemin.exists():
            raise FileNotFoundError(chemin)
        return Source(
            video_id=chemin.stem,
            chemin=chemin,
            titre=chemin.stem,
            auteur=cfg.marque["nom"],
            licence="local",
        )

    video_id = _extraire_id(cible)
    url = f"https://www.youtube.com/watch?v={video_id}"
    destination = dossier / f"{video_id}.mp4"

    if mode == "creative_commons":
        infos = _verifier_licence(video_id, secret("YOUTUBE_API_KEY"))
        if infos["licence"] != "creativeCommon":
            raise PermissionError(
                f"La video {video_id} est sous licence YouTube standard, pas Creative "
                f"Commons. La reutiliser exposerait le compte a une revendication "
                f"Content ID. Voir automation/docs/02-droits.md."
            )
        if not destination.exists():
            _telecharger(url, destination)
        return Source(
            video_id=video_id,
            chemin=destination,
            titre=infos["titre"],
            auteur=infos["auteur"],
            licence="creativeCommon",
            url=url,
        )

    if mode == "proprietaire":
        # Les videos de ta propre chaine peuvent aussi etre recuperees depuis
        # tes masters locaux : c'est plus rapide et cela evite un aller-retour
        # par YouTube. On telecharge seulement si le master n'existe pas.
        if not destination.exists():
            _telecharger(url, destination)
        return Source(
            video_id=video_id,
            chemin=destination,
            titre=cible,
            auteur=cfg.marque["nom"],
            licence="proprietaire",
            url=url,
        )

    raise ValueError(f"Mode de source inconnu : {mode}")


def _extraire_id(cible: str) -> str:
    """Accepte une URL complete, une URL courte, ou un identifiant nu."""
    cible = cible.strip()
    if "youtube.com" in cible and "v=" in cible:
        return cible.split("v=")[1].split("&")[0]
    if "youtu.be/" in cible:
        return cible.split("youtu.be/")[1].split("?")[0]
    return cible
