"""Structures de donnees partagees entre les etages de la chaine.

Chaque extrait est materialise sur disque par un fichier JSON dans
`var/extraits/`, ce qui rend la chaine reprenable : si le rendu echoue,
la transcription et la selection ne sont pas rejouees.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Mot:
    """Un mot de la transcription avec ses bornes temporelles absolues."""

    texte: str
    debut: float
    fin: float


@dataclass
class Transcription:
    video_id: str
    langue: str
    mots: list[Mot]

    @property
    def texte(self) -> str:
        return " ".join(m.texte for m in self.mots)

    def mots_entre(self, debut: float, fin: float) -> list[Mot]:
        """Mots dont le centre tombe dans la fenetre demandee."""
        return [m for m in self.mots if debut <= (m.debut + m.fin) / 2 <= fin]

    def sauver(self, chemin: Path) -> None:
        charge = {
            "video_id": self.video_id,
            "langue": self.langue,
            "mots": [asdict(m) for m in self.mots],
        }
        chemin.write_text(json.dumps(charge, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def charger(cls, chemin: Path) -> "Transcription":
        d = json.loads(chemin.read_text(encoding="utf-8"))
        return cls(
            video_id=d["video_id"],
            langue=d["langue"],
            mots=[Mot(**m) for m in d["mots"]],
        )


@dataclass
class Metadonnees:
    titre: str
    description: str
    hashtags: list[str] = field(default_factory=list)
    # Texte alternatif pour l'accessibilite (Instagram accepte un alt-text)
    alt: str = ""


@dataclass
class Extrait:
    """Un short candidat, de la selection jusqu'a la publication."""

    id: str
    video_id: str
    debut: float
    fin: float
    accroche: str            # phrase d'ouverture reperee par le LLM
    justification: str       # pourquoi ce passage a ete retenu
    score: int               # 0-100, potentiel estime

    # Rempli au fur et a mesure des etapes
    chemin_rendu: str | None = None
    url_publique: str | None = None
    metadonnees: Metadonnees | None = None
    valide: bool = False
    publications: dict[str, str] = field(default_factory=dict)  # plateforme -> id du post

    @property
    def duree(self) -> float:
        return self.fin - self.debut

    def sauver(self, dossier: Path) -> Path:
        chemin = dossier / f"{self.id}.json"
        charge = asdict(self)
        chemin.write_text(
            json.dumps(charge, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return chemin

    @classmethod
    def charger(cls, chemin: Path) -> "Extrait":
        d = json.loads(chemin.read_text(encoding="utf-8"))
        meta = d.pop("metadonnees", None)
        extrait = cls(**d)
        if meta:
            extrait.metadonnees = Metadonnees(**meta)
        return extrait

    @classmethod
    def charger_tous(cls, dossier: Path) -> list["Extrait"]:
        return sorted(
            (cls.charger(p) for p in dossier.glob("*.json")),
            key=lambda e: (e.video_id, e.debut),
        )
