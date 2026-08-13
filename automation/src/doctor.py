"""Controle de l'environnement : `python -m src.doctor`.

A lancer avant la premiere execution et apres chaque changement de machine.
Verifie separement ce qui est necessaire a la preparation (ffmpeg, cle
Anthropic) et ce qui ne l'est qu'a la publication (tokens des plateformes),
pour qu'on puisse travailler la partie montage avant d'avoir obtenu les acces.
"""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

VERT, ROUGE, JAUNE, GRIS, FIN = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m"


def _ligne(etat: str, libelle: str, detail: str = "") -> None:
    couleur = {"ok": VERT, "manque": ROUGE, "option": JAUNE}[etat]
    marque = {"ok": "✓", "manque": "✗", "option": "!"}[etat]
    print(f" {couleur}{marque}{FIN} {libelle:<38} {GRIS}{detail}{FIN}")


def _binaire(nom: str, obligatoire: bool = True) -> bool:
    chemin = shutil.which(nom)
    if chemin:
        version = ""
        try:
            sortie = subprocess.run(
                [nom, "-version"], capture_output=True, text=True, timeout=10
            ).stdout
            version = sortie.splitlines()[0][:48] if sortie else ""
        except Exception:  # noqa: BLE001
            pass
        _ligne("ok", nom, version)
        return True
    _ligne("manque" if obligatoire else "option", nom, "introuvable dans le PATH")
    return not obligatoire


def _module(nom: str, obligatoire: bool = True) -> bool:
    try:
        importlib.import_module(nom)
        _ligne("ok", nom)
        return True
    except ImportError:
        _ligne(
            "manque" if obligatoire else "option",
            nom,
            "pip install -r requirements.txt",
        )
        return not obligatoire


def _variable(nom: str, obligatoire: bool = True) -> bool:
    valeur = os.environ.get(nom, "")
    if valeur:
        _ligne("ok", nom, f"{valeur[:6]}… ({len(valeur)} car.)")
        return True
    _ligne("manque" if obligatoire else "option", nom, "absent de .env")
    return not obligatoire


def principal() -> int:
    from .config import _charger_env

    _charger_env(RACINE / ".env")
    tout_va_bien = True

    print("\nOutils systeme")
    tout_va_bien &= _binaire("ffmpeg")
    tout_va_bien &= _binaire("ffprobe")
    _binaire("yt-dlp", obligatoire=False)

    print("\nBibliotheques Python")
    for nom in ("anthropic", "yaml", "requests", "boto3"):
        tout_va_bien &= _module(nom)
    for nom in ("faster_whisper", "googleapiclient"):
        _module(nom, obligatoire=False)

    print("\nConfiguration")
    if (RACINE / "config.yaml").exists():
        _ligne("ok", "config.yaml")
    else:
        _ligne("manque", "config.yaml", "cp config.example.yaml config.yaml")
        tout_va_bien = False

    print("\nSecrets — preparation (montage)")
    tout_va_bien &= _variable("ANTHROPIC_API_KEY")

    print("\nSecrets — publication (peuvent attendre)")
    for nom in (
        "S3_ENDPOINT_URL", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY",
        "S3_BUCKET", "S3_PUBLIC_BASE_URL",
        "IG_USER_ID", "IG_ACCESS_TOKEN",
        "TIKTOK_CLIENT_KEY", "TIKTOK_ACCESS_TOKEN",
        "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN",
    ):
        _variable(nom, obligatoire=False)

    print("\nPolices (sous-titres)")
    try:
        sortie = subprocess.run(
            ["fc-list"], capture_output=True, text=True, timeout=15
        ).stdout
        if "Montserrat" in sortie:
            _ligne("ok", "Montserrat", "installee")
        else:
            _ligne(
                "option",
                "Montserrat",
                "absente — ffmpeg substituera une police par defaut",
            )
    except Exception:  # noqa: BLE001
        _ligne("option", "fc-list", "indisponible (normal sur macOS)")

    print()
    if tout_va_bien:
        print(f"{VERT}Pret pour `python -m src.cli preparer <url>`{FIN}\n")
        return 0
    print(f"{ROUGE}Corrige les lignes marquees ✗ avant de continuer.{FIN}\n")
    return 1


if __name__ == "__main__":
    sys.exit(principal())
