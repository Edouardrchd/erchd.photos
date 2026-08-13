"""Rafraichissement des jetons : `python -m src.tokens`.

A programmer en tache recurrente. Les echeances different fortement :

    TikTok      access_token valable 24 h  -> rafraichissement quotidien
    Instagram   token valable 60 jours     -> rafraichissement mensuel
    YouTube     refresh_token permanent    -> rien a faire

Un jeton expire ne declenche aucune alerte : l'erreur n'apparait qu'a la
publication suivante, souvent des jours plus tard. D'ou cette commande
separee, faite pour tourner sans supervision.

Le script ecrit les nouvelles valeurs sur la sortie standard au format
`CLE=valeur`. Charge a l'appelant de les reinjecter dans son magasin de
secrets : GitHub Secrets n'a pas d'API d'ecriture simple, un gestionnaire
dedie (Doppler, 1Password, AWS Secrets Manager) est preferable des que la
chaine tourne sans toi.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent


def _rafraichir_tiktok() -> dict[str, str]:
    from .publish.tiktok import rafraichir_token

    charge = rafraichir_token()
    return {
        "TIKTOK_ACCESS_TOKEN": charge["access_token"],
        # TikTok fait tourner aussi le refresh_token : ne pas le perdre.
        "TIKTOK_REFRESH_TOKEN": charge.get(
            "refresh_token", os.environ.get("TIKTOK_REFRESH_TOKEN", "")
        ),
    }


def _rafraichir_instagram() -> dict[str, str]:
    from .publish.instagram import rafraichir_token

    charge = rafraichir_token()
    jours = int(charge.get("expires_in", 0)) // 86400
    print(f"  Instagram : nouveau jeton valable {jours} jours", file=sys.stderr)
    return {"IG_ACCESS_TOKEN": charge["access_token"]}


def principal(argv: list[str] | None = None) -> int:
    from .config import _charger_env

    _charger_env(RACINE / ".env")

    argv = argv if argv is not None else sys.argv[1:]
    # Sans argument, on rafraichit tout ce qui est configure.
    cibles = argv or [
        nom
        for nom, variable in (("tiktok", "TIKTOK_REFRESH_TOKEN"),
                              ("instagram", "IG_ACCESS_TOKEN"))
        if os.environ.get(variable)
    ]

    if not cibles:
        print("Aucun jeton configure a rafraichir.", file=sys.stderr)
        return 0

    fonctions = {"tiktok": _rafraichir_tiktok, "instagram": _rafraichir_instagram}
    resultats: dict[str, str] = {}
    code = 0

    for cible in cibles:
        if cible not in fonctions:
            print(f"Cible inconnue : {cible}", file=sys.stderr)
            code = 1
            continue
        try:
            resultats.update(fonctions[cible]())
            print(f"  {cible} : OK", file=sys.stderr)
        except Exception as erreur:  # noqa: BLE001 - on continue les autres cibles
            print(f"  {cible} : ECHEC — {erreur}", file=sys.stderr)
            code = 1

    # Sortie standard exploitable : `python -m src.tokens > nouveaux.env`
    for cle, valeur in resultats.items():
        if valeur:
            print(f"{cle}={valeur}")

    return code


if __name__ == "__main__":
    sys.exit(principal())
