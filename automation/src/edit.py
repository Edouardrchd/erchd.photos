"""Etape 4b - Montage : decoupe, passage en 9:16, incrustation, normalisation.

Tout est fait par ffmpeg en une seule passe. C'est volontaire : chaque
re-encodage coute de la qualite, et un rendu unique evite d'empiler les
generations de compression avant que les plateformes n'appliquent la leur.

Reglages retenus :
  H.264 High profile, yuv420p     accepte partout, y compris par l'API Reels
  CRF 20 + maxrate                qualite constante, debit borne
  loudnorm I=-14 LUFS             cible commune a TikTok, Reels et Shorts ;
                                  sans cela le son parait faible a cote des
                                  autres videos du fil
  +faststart                      atome moov en tete : Instagram telecharge la
                                  video par HTTP et refuse les fichiers dont
                                  l'index est en fin de fichier
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .config import Config
from .models import Extrait, Transcription
from .subtitles import generer as generer_sous_titres


class RenduEchoue(RuntimeError):
    pass


def _verifier_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RenduEchoue(
            "ffmpeg est introuvable dans le PATH. "
            "Installe-le : `apt install ffmpeg` ou `brew install ffmpeg`."
        )


def _chaine_recadrage(mode: str, largeur: int, hauteur: int) -> str:
    """Renvoie le graphe de filtres qui transforme le 16:9 en 9:16."""
    if mode == "blur_pad":
        # Fond : la meme image agrandie, floutee et assombrie. Garde l'integralite
        # du cadre d'origine, ce qui compte quand la composition photo est le sujet.
        return (
            f"split=2[bg][fg];"
            f"[bg]scale={largeur}:{hauteur}:force_original_aspect_ratio=increase,"
            f"crop={largeur}:{hauteur},gblur=sigma=28,eq=brightness=-0.12[bgf];"
            f"[fg]scale={largeur}:-2[fgs];"
            f"[bgf][fgs]overlay=(W-w)/2:(H-h)/2"
        )

    if mode == "crop_centre":
        # Recadrage plein cadre : image plus grande, mais on perd les bords.
        return (
            f"scale={largeur}:{hauteur}:force_original_aspect_ratio=increase,"
            f"crop={largeur}:{hauteur}"
        )

    if mode == "crop_suivi":
        raise NotImplementedError(
            "Le recadrage avec suivi du sujet n'est pas inclus dans cette version : "
            "il demande un modele de detection par image et un lissage de "
            "trajectoire. Utilise 'blur_pad' ou 'crop_centre' en attendant. "
            "Piste d'implementation : automation/docs/04-runbook.md, section "
            "« Recadrage intelligent »."
        )

    raise ValueError(f"Mode de recadrage inconnu : {mode}")


def rendre(
    cfg: Config,
    extrait: Extrait,
    source: Path,
    transcription: Transcription,
) -> Path:
    """Produit le MP4 final d'un extrait et renvoie son chemin."""
    _verifier_ffmpeg()

    montage = cfg.montage
    largeur, hauteur = (int(v) for v in montage["format"].split("x"))
    dossier = cfg.dossier("rendus")
    destination = dossier / f"{extrait.id}.mp4"

    # Sous-titres : on les ecrit dans le meme dossier que le rendu et on lance
    # ffmpeg depuis ce dossier. Cela evite d'echapper les deux-points et les
    # apostrophes d'un chemin absolu dans le graphe de filtres, source
    # classique d'erreurs silencieuses.
    mots = transcription.mots_entre(extrait.debut, extrait.fin)
    fichier_ass = generer_sous_titres(
        mots=mots,
        destination=dossier / f"{extrait.id}.ass",
        reglages=cfg.sous_titres,
        decalage=extrait.debut,
        largeur=largeur,
        hauteur=hauteur,
    )

    filtres = [f"[0:v]{_chaine_recadrage(montage['recadrage'], largeur, hauteur)}[cadre]"]
    dernier = "cadre"

    filtres.append(f"[{dernier}]subtitles={fichier_ass.name}[st]")
    dernier = "st"

    entrees = ["-ss", f"{extrait.debut:.3f}", "-i", str(source.resolve()),
               "-t", f"{extrait.duree:.3f}"]

    watermark = Path(cfg.marque.get("watermark", ""))
    if watermark.name and (cfg_wm := (Path(cfg.workdir).parent / watermark)).exists():
        entrees += ["-i", str(cfg_wm.resolve())]
        filtres.append(f"[1:v]scale={largeur // 5}:-1[wm]")
        filtres.append(f"[{dernier}][wm]overlay=W-w-40:H-h-70[sortie]")
        dernier = "sortie"

    filtre_audio = "[0:a]aresample=async=1"
    if montage.get("loudnorm", True):
        filtre_audio += ",loudnorm=I=-14:TP=-1.5:LRA=11"
    filtres.append(f"{filtre_audio}[audio]")

    commande = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *entrees,
        "-filter_complex", ";".join(filtres),
        "-map", f"[{dernier}]", "-map", "[audio]",
        "-c:v", "libx264", "-profile:v", "high", "-preset", "medium",
        "-crf", "20", "-maxrate", montage["bitrate_video"], "-bufsize", "12M",
        "-pix_fmt", "yuv420p",
        "-r", str(montage["fps"]),
        "-c:a", "aac", "-b:a", montage["bitrate_audio"], "-ar", "48000",
        "-movflags", "+faststart",
        destination.name,
    ]

    resultat = subprocess.run(
        commande, cwd=dossier, capture_output=True, text=True
    )
    if resultat.returncode != 0:
        raise RenduEchoue(
            f"Rendu de {extrait.id} echoue.\n"
            f"Commande : {' '.join(commande)}\n\n{resultat.stderr[-3000:]}"
        )

    extrait.chemin_rendu = str(destination)
    return destination


def sonder(chemin: Path) -> dict:
    """Renvoie duree, dimensions et debit du fichier rendu (controle qualite)."""
    commande = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,bit_rate:format=duration,size",
        "-of", "default=noprint_wrappers=1:nokey=0",
        str(chemin),
    ]
    try:
        resultat = subprocess.run(commande, capture_output=True, text=True)
    except FileNotFoundError:
        # ffprobe est livre avec ffmpeg, mais certaines images minimales ne
        # contiennent que le binaire ffmpeg. Le sondage est un confort de
        # controle qualite, jamais un prerequis : on n'echoue pas pour cela.
        return {}
    if resultat.returncode != 0:
        return {}
    infos: dict[str, str] = {}
    for ligne in resultat.stdout.splitlines():
        if "=" in ligne:
            cle, _, valeur = ligne.partition("=")
            infos[cle] = valeur
    return infos
