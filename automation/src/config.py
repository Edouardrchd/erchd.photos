"""Chargement de la configuration et des secrets.

Deux sources distinctes, volontairement separees :
  - config.yaml : choix editoriaux et techniques, versionnable ;
  - .env        : secrets, jamais versionne.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

RACINE = Path(__file__).resolve().parent.parent


def _charger_env(chemin: Path) -> None:
    """Lecteur .env minimal : evite une dependance supplementaire.

    Les variables deja presentes dans l'environnement gagnent, ce qui permet
    a un runner CI d'injecter ses secrets sans toucher au fichier.
    """
    if not chemin.exists():
        return
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        os.environ.setdefault(cle.strip(), valeur.strip().strip("\"'"))


class SecretManquant(RuntimeError):
    """Leve quand un secret requis par une etape n'est pas renseigne."""


def secret(nom: str, requis: bool = True) -> str:
    valeur = os.environ.get(nom, "")
    if requis and not valeur:
        raise SecretManquant(
            f"{nom} n'est pas defini. Renseigne-le dans .env "
            f"(modele : automation/.env.example) ou dans les secrets du runner."
        )
    return valeur


@dataclass(frozen=True)
class Config:
    """Vue typee de config.yaml, avec acces brut pour les sections libres."""

    brut: dict[str, Any] = field(repr=False)
    workdir: Path

    @property
    def marque(self) -> dict[str, Any]:
        return self.brut["marque"]

    @property
    def source(self) -> dict[str, Any]:
        return self.brut["source"]

    @property
    def transcription(self) -> dict[str, Any]:
        return self.brut["transcription"]

    @property
    def selection(self) -> dict[str, Any]:
        return self.brut["selection"]

    @property
    def montage(self) -> dict[str, Any]:
        return self.brut["montage"]

    @property
    def sous_titres(self) -> dict[str, Any]:
        return self.brut["sous_titres"]

    @property
    def metadonnees(self) -> dict[str, Any]:
        return self.brut["metadonnees"]

    @property
    def publication(self) -> dict[str, Any]:
        return self.brut["publication"]

    @property
    def langue_sortie(self) -> str:
        return self.brut["langue"]["sortie"]

    def dossier(self, *parties: str) -> Path:
        """Cree si besoin et renvoie un sous-dossier du repertoire de travail."""
        chemin = self.workdir.joinpath(*parties)
        chemin.mkdir(parents=True, exist_ok=True)
        return chemin


def charger(chemin_config: Path | None = None) -> Config:
    _charger_env(RACINE / ".env")

    chemin_config = chemin_config or RACINE / "config.yaml"
    if not chemin_config.exists():
        raise FileNotFoundError(
            f"{chemin_config} introuvable. Copie config.example.yaml en config.yaml."
        )

    brut = yaml.safe_load(chemin_config.read_text(encoding="utf-8"))
    workdir = RACINE / brut["source"].get("workdir", "var")
    workdir.mkdir(parents=True, exist_ok=True)
    return Config(brut=brut, workdir=workdir)
