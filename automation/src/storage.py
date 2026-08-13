"""Stockage objet : rend le rendu accessible par une URL publique HTTPS.

Cette etape n'est pas optionnelle. L'API de publication d'Instagram ne recoit
pas de fichier : on lui transmet une URL, et ce sont les serveurs de Meta qui
telechargent la video. Il faut donc un hebergement public, meme temporaire.

Cloudflare R2 est recommande plutot que S3 : l'API est compatible S3 (meme
client boto3), le stockage coute environ 0,015 $/Go/mois, et surtout l'egress
est gratuit — or c'est Meta qui telecharge, donc c'est bien de l'egress.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

import boto3
from botocore.config import Config as BotoConfig

from .config import secret


def _client():
    return boto3.client(
        "s3",
        endpoint_url=secret("S3_ENDPOINT_URL"),
        aws_access_key_id=secret("S3_ACCESS_KEY_ID"),
        aws_secret_access_key=secret("S3_SECRET_ACCESS_KEY"),
        config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 3}),
        region_name="auto",   # valeur attendue par R2 ; ignoree par S3
    )


def televerser(chemin: Path, cle: str | None = None) -> str:
    """Envoie le fichier et renvoie son URL publique."""
    cle = cle or f"shorts/{chemin.name}"
    bucket = secret("S3_BUCKET")
    type_mime = mimetypes.guess_type(chemin.name)[0] or "video/mp4"

    _client().upload_file(
        str(chemin),
        bucket,
        cle,
        ExtraArgs={
            "ContentType": type_mime,
            # 7 jours : la video n'a besoin d'etre accessible que le temps que
            # Meta et TikTok la recuperent. Au-dela, elle vit sur les plateformes.
            "CacheControl": "public, max-age=604800",
        },
    )

    base = secret("S3_PUBLIC_BASE_URL").rstrip("/")
    return f"{base}/{cle}"


def supprimer(cle: str) -> None:
    """Nettoyage apres publication reussie sur toutes les plateformes."""
    _client().delete_object(Bucket=secret("S3_BUCKET"), Key=cle)
