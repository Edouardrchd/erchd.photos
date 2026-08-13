"""Etape 5 - Redaction du titre, de la description et des hashtags.

Une seule requete par extrait produit les variantes des trois plateformes.
Elles ne demandent pas la meme chose :

  Instagram   legende jusqu'a 2 200 caracteres, hashtags toleres mais le
              texte court fonctionne mieux ; pas de titre separe.
  TikTok      2 200 caracteres, hashtags integres au texte, ton direct.
  YouTube     titre <= 100 caracteres qui porte tout le referencement,
              description longue utile pour la recherche.

On demande donc au modele les trois versions d'un coup plutot que de payer
trois appels et de risquer trois angles differents.
"""

from __future__ import annotations

import json

import anthropic

from .config import Config, secret
from .models import Extrait, Metadonnees, Transcription

SCHEMA = {
    "type": "object",
    "properties": {
        "titre_youtube": {
            "type": "string",
            "description": "100 caracteres maximum, sans emoji, porte le mot-cle principal.",
        },
        "description_youtube": {
            "type": "string",
            "description": "2 a 4 phrases. Reprend le propos et invite a voir la video complete.",
        },
        "legende_instagram": {
            "type": "string",
            "description": "1 a 3 phrases, ton direct, sans hashtags (ils sont ajoutes ensuite).",
        },
        "legende_tiktok": {
            "type": "string",
            "description": "1 a 2 phrases, plus percutant qu'Instagram, sans hashtags.",
        },
        "hashtags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Sans le caractere #. Melange de generiques et de specifiques.",
        },
        "alt": {
            "type": "string",
            "description": "Description visuelle factuelle pour les lecteurs d'ecran.",
        },
    },
    "required": [
        "titre_youtube",
        "description_youtube",
        "legende_instagram",
        "legende_tiktok",
        "hashtags",
        "alt",
    ],
    "additionalProperties": False,
}

CONSIGNE = """Tu rediges les metadonnees d'un short vertical pour le compte {compte}, \
qui publie de la photographie de sport.

Ecris en {langue}. Ton sobre et concret, a la premiere personne. Pas de \
superlatifs vides, pas d'emoji en debut de phrase, pas d'appel a l'action \
generique du type « likez et abonnez-vous ».

Le titre YouTube doit tenir sous 100 caracteres et rester comprehensible hors \
contexte. Les legendes ne repetent pas mot pour mot ce qui est dit dans la \
video : elles donnent envie de l'ecouter.

Propose au maximum {hashtags_max} hashtags, pertinents pour la photo de sport \
et le sujet precis de l'extrait. Evite les hashtags a plusieurs millions de \
publications, ils n'apportent aucune visibilite."""


def rediger(
    cfg: Config, extrait: Extrait, transcription: Transcription
) -> dict[str, Metadonnees]:
    """Renvoie un dictionnaire plateforme -> Metadonnees."""
    reglages = cfg.metadonnees
    client = anthropic.Anthropic(api_key=secret("ANTHROPIC_API_KEY"))

    verbatim = " ".join(
        m.texte for m in transcription.mots_entre(extrait.debut, extrait.fin)
    )

    reponse = client.messages.create(
        model=reglages["modele_llm"],
        max_tokens=8000,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": SCHEMA},
        },
        system=CONSIGNE.format(
            compte=cfg.marque["nom"],
            langue=cfg.langue_sortie,
            hashtags_max=reglages["hashtags_max"],
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Duree de l'extrait : {extrait.duree:.0f} secondes.\n"
                    f"Pourquoi il a ete retenu : {extrait.justification}\n\n"
                    f"Transcription exacte de l'extrait :\n{verbatim}"
                ),
            }
        ],
    )

    if reponse.stop_reason == "refusal":
        raise RuntimeError(f"Redaction refusee pour {extrait.id}.")

    d = json.loads(next(b.text for b in reponse.content if b.type == "text"))
    hashtags = [h.lstrip("#") for h in d["hashtags"]][: reglages["hashtags_max"]]
    signature = reglages.get("signature", "")
    ligne_tags = " ".join(f"#{h}" for h in hashtags)

    return {
        "youtube": Metadonnees(
            titre=d["titre_youtube"][:100],
            description="\n\n".join(
                filter(None, [d["description_youtube"], signature, ligne_tags])
            ),
            hashtags=hashtags,
            alt=d["alt"],
        ),
        "instagram": Metadonnees(
            titre=d["titre_youtube"][:100],
            description="\n\n".join(
                filter(None, [d["legende_instagram"], signature, ligne_tags])
            )[:2200],
            hashtags=hashtags,
            alt=d["alt"],
        ),
        "tiktok": Metadonnees(
            titre=d["titre_youtube"][:100],
            description=" ".join(filter(None, [d["legende_tiktok"], ligne_tags]))[:2200],
            hashtags=hashtags,
            alt=d["alt"],
        ),
    }
