"""Connecteurs de publication, un module par plateforme.

Chaque module expose la meme fonction :

    publier(extrait, metadonnees) -> str   # renvoie l'identifiant du post

et leve `ErreurPublication` en cas d'echec, avec un message qui dit quoi faire.
"""

from __future__ import annotations


class ErreurPublication(RuntimeError):
    """Echec de publication, avec le contexte necessaire au diagnostic."""

    def __init__(self, plateforme: str, message: str, reponse: object = None):
        self.plateforme = plateforme
        self.reponse = reponse
        super().__init__(f"[{plateforme}] {message}")
