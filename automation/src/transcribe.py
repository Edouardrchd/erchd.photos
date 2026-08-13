"""Etape 2 - Transcription avec horodatage au mot.

L'horodatage au mot (et pas seulement a la phrase) est indispensable : c'est
lui qui permet le sous-titrage « karaoke » ou le mot prononce est mis en
couleur, qui est le standard visuel sur TikTok et Reels.

Deux implementations interchangeables :
  faster-whisper : tourne en local, gratuit, ~1x temps reel sur CPU moderne,
                   ~10x plus rapide avec un GPU. Aucun envoi de donnees.
  assemblyai     : API hebergee, ~0,15 $/heure, plus rapide a mettre en place,
                   meilleure ponctuation sur l'audio bruite (bord de terrain).
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import requests

from .config import Config, secret
from .models import Mot, Transcription


def _extraire_audio(video: Path, destination: Path) -> Path:
    """Extrait une piste WAV 16 kHz mono : format attendu par les moteurs ASR."""
    if destination.exists():
        return destination
    commande = [
        "ffmpeg", "-y", "-i", str(video),
        "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(destination),
    ]
    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(f"Extraction audio impossible :\n{resultat.stderr[-2000:]}")
    return destination


def _via_faster_whisper(audio: Path, cfg: Config, video_id: str) -> Transcription:
    from faster_whisper import WhisperModel  # import tardif : dependance lourde

    reglages = cfg.transcription
    device = reglages.get("device", "auto")
    if device == "auto":
        try:
            import torch  # noqa: F401

            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"

    modele = WhisperModel(
        reglages["modele"],
        device=device,
        compute_type="float16" if device == "cuda" else "int8",
    )
    segments, _ = modele.transcribe(
        str(audio),
        language=cfg.brut["langue"]["source"],
        word_timestamps=True,      # c'est l'option qui compte
        vad_filter=True,           # coupe les silences, ameliore le calage
    )

    mots: list[Mot] = []
    for segment in segments:
        for mot in segment.words or []:
            texte = mot.word.strip()
            if texte:
                mots.append(Mot(texte=texte, debut=mot.start, fin=mot.end))

    return Transcription(video_id=video_id, langue=cfg.brut["langue"]["source"], mots=mots)


def _via_assemblyai(audio: Path, cfg: Config, video_id: str) -> Transcription:
    cle = secret("ASSEMBLYAI_API_KEY")
    entetes = {"authorization": cle}

    # 1. Televersement du fichier audio
    with audio.open("rb") as flux:
        televersement = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=entetes,
            data=flux,
            timeout=600,
        )
    televersement.raise_for_status()
    url_audio = televersement.json()["upload_url"]

    # 2. Demande de transcription
    demande = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=entetes,
        json={"audio_url": url_audio, "language_code": cfg.brut["langue"]["source"]},
        timeout=60,
    )
    demande.raise_for_status()
    transcript_id = demande.json()["id"]

    # 3. Attente active du resultat
    while True:
        etat = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers=entetes,
            timeout=60,
        )
        etat.raise_for_status()
        charge = etat.json()
        if charge["status"] == "completed":
            break
        if charge["status"] == "error":
            raise RuntimeError(f"AssemblyAI : {charge.get('error')}")
        time.sleep(5)

    mots = [
        Mot(texte=m["text"], debut=m["start"] / 1000, fin=m["end"] / 1000)
        for m in charge.get("words", [])
    ]
    return Transcription(video_id=video_id, langue=cfg.brut["langue"]["source"], mots=mots)


def transcrire(cfg: Config, video: Path, video_id: str) -> Transcription:
    """Transcrit la video, avec cache sur disque."""
    cache = cfg.dossier("transcriptions") / f"{video_id}.json"
    if cache.exists():
        return Transcription.charger(cache)

    audio = _extraire_audio(video, cfg.dossier("audio") / f"{video_id}.wav")

    provider = cfg.transcription["provider"]
    if provider == "faster-whisper":
        transcription = _via_faster_whisper(audio, cfg, video_id)
    elif provider == "assemblyai":
        transcription = _via_assemblyai(audio, cfg, video_id)
    else:
        raise ValueError(f"Provider de transcription inconnu : {provider}")

    transcription.sauver(cache)
    return transcription
