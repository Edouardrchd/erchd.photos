"""Etape 3 - Selection des moments qui feront de bons shorts.

C'est l'etape ou la chaine cesse d'etre mecanique. On donne a Claude la
transcription horodatee complete et on lui demande de reperer les passages
qui tiennent debout tout seuls, sortis de leur contexte.

Le format de sortie est contraint par un JSON Schema (`output_config.format`),
ce qui garantit un objet exploitable sans post-traitement fragile.
"""

from __future__ import annotations

import json
import re

import anthropic

from .config import Config, secret
from .models import Extrait, Transcription

SCHEMA = {
    "type": "object",
    "properties": {
        "extraits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "debut": {
                        "type": "number",
                        "description": "Horodatage de debut en secondes, cale sur le premier mot de l'idee.",
                    },
                    "fin": {
                        "type": "number",
                        "description": "Horodatage de fin en secondes, cale sur la fin de la derniere phrase.",
                    },
                    "accroche": {
                        "type": "string",
                        "description": "Les 5 a 10 premiers mots prononces, verbatim.",
                    },
                    "justification": {
                        "type": "string",
                        "description": "En une phrase, pourquoi ce passage fonctionne isole du reste.",
                    },
                    "score": {
                        "type": "integer",
                        "description": "Potentiel estime de 0 a 100.",
                    },
                },
                "required": ["debut", "fin", "accroche", "justification", "score"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["extraits"],
    "additionalProperties": False,
}

CONSIGNE = """Tu selectionnes des extraits dans la transcription d'une video longue \
pour en faire des shorts verticaux (Instagram Reels, TikTok, YouTube Shorts).

Un bon extrait :
- s'ouvre sur une phrase qui se suffit a elle-meme, sans « comme je disais » ni \
« du coup » ni reference a ce qui precede ;
- contient une idee complete : une affirmation, son explication, et sa conclusion ;
- se termine sur une fin de phrase nette, jamais au milieu d'une proposition ;
- reste comprehensible pour quelqu'un qui n'a pas vu le reste de la video.

Un mauvais extrait est un passage qui a besoin de contexte, une transition, une \
introduction, un remerciement, ou une reponse a une question qu'on n'entend pas.

Cale `debut` et `fin` exactement sur les horodatages des mots de la transcription. \
Mieux vaut demarrer une demi-seconde avant le premier mot que de le tronquer.

Angle editorial impose :
{angle}

Contraintes de duree : entre {duree_min} et {duree_max} secondes.
Rends exactement {nb} extraits, tries du meilleur au moins bon."""


def _transcription_horodatee(transcription: Transcription, pas: float = 5.0) -> str:
    """Rend la transcription lisible par le modele avec des reperes temporels.

    On insere un marqueur toutes les `pas` secondes plutot qu'a chaque mot :
    cela divise par dix le volume de tokens tout en gardant une precision
    largement suffisante pour un decoupage a la seconde.
    """
    lignes: list[str] = []
    tampon: list[str] = []
    prochain_repere = 0.0

    for mot in transcription.mots:
        if mot.debut >= prochain_repere:
            if tampon:
                lignes.append(" ".join(tampon))
                tampon = []
            lignes.append(f"[{mot.debut:.1f}s]")
            prochain_repere = mot.debut + pas
        tampon.append(mot.texte)

    if tampon:
        lignes.append(" ".join(tampon))
    return " ".join(lignes)


def selectionner(
    cfg: Config, transcription: Transcription, video_id: str
) -> list[Extrait]:
    reglages = cfg.selection
    client = anthropic.Anthropic(api_key=secret("ANTHROPIC_API_KEY"))

    consigne = CONSIGNE.format(
        angle=reglages["angle"].strip(),
        duree_min=reglages["duree_min_s"],
        duree_max=reglages["duree_max_s"],
        nb=reglages["nb_extraits"],
    )

    reponse = client.messages.create(
        model=reglages["modele_llm"],
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={
            "effort": reglages.get("effort", "high"),
            "format": {"type": "json_schema", "schema": SCHEMA},
        },
        system=consigne,
        messages=[
            {
                "role": "user",
                "content": (
                    "Transcription horodatee de la video "
                    f"(duree totale {transcription.mots[-1].fin:.0f} s) :\n\n"
                    + _transcription_horodatee(transcription)
                ),
            }
        ],
    )

    if reponse.stop_reason == "refusal":
        raise RuntimeError(
            "Le modele a decline la demande de selection "
            f"({getattr(reponse.stop_details, 'category', 'sans categorie')})."
        )

    texte = next(bloc.text for bloc in reponse.content if bloc.type == "text")
    charge = json.loads(texte)

    extraits: list[Extrait] = []
    for index, brut in enumerate(charge["extraits"], start=1):
        debut = max(0.0, float(brut["debut"]) - 0.3)   # marge de securite avant le premier mot
        fin = float(brut["fin"]) + 0.4                  # laisse respirer la fin de phrase
        extraits.append(
            Extrait(
                id=f"{video_id}-{index:02d}",
                video_id=video_id,
                debut=debut,
                fin=fin,
                accroche=brut["accroche"],
                justification=brut["justification"],
                score=int(brut["score"]),
            )
        )

    return _filtrer_durees(extraits, reglages)


def _filtrer_durees(extraits: list[Extrait], reglages: dict) -> list[Extrait]:
    """Ecarte les extraits hors bornes plutot que de les tronquer.

    Un extrait tronque a 75 s coupe au milieu d'une phrase : c'est pire que
    pas d'extrait du tout. On prefere en publier quatre bons que cinq dont un
    inutilisable.
    """
    mini, maxi = reglages["duree_min_s"], reglages["duree_max_s"]
    gardes, ecartes = [], []
    for extrait in extraits:
        (gardes if mini <= extrait.duree <= maxi else ecartes).append(extrait)

    for extrait in ecartes:
        print(
            f"  ecarte {extrait.id} : duree {extrait.duree:.0f}s hors bornes "
            f"[{mini}-{maxi}]"
        )
    return gardes


def nettoyer_accroche(texte: str) -> str:
    """Normalise une accroche pour l'affichage (usage : rapports, revue)."""
    return re.sub(r"\s+", " ", texte).strip(" .,;:")
