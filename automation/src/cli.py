"""Orchestrateur en ligne de commande.

    python -m src.doctor                     controle de l'environnement
    python -m src.cli preparer <url>         source -> extraits prets a valider
    python -m src.cli revue                  liste les extraits et leur etat
    python -m src.cli valider <id> [...]     autorise la publication
    python -m src.cli publier [--id <id>]    publie les extraits valides
    python -m src.cli auth-youtube           genere le refresh token YouTube
    python -m src.cli auth-tiktok            genere les jetons TikTok

Le decoupage en deux commandes (`preparer` puis `publier`) est deliberе : la
porte de validation humaine se situe entre les deux. Rien ne part vers une
plateforme sans un passage explicite par `valider`.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from . import config as configuration
from . import edit, ingest, metadata, segment, storage, transcribe
from .models import Extrait, Metadonnees, Transcription
from .publish import ErreurPublication


def _dossier_extraits(cfg) -> Path:
    return cfg.dossier("extraits")


# --------------------------------------------------------------------------
# preparer
# --------------------------------------------------------------------------
def commande_preparer(args) -> int:
    cfg = configuration.charger()

    print(f"1/5  Recuperation de la source : {args.cible}")
    source = ingest.recuperer(cfg, args.cible)
    print(f"     {source.chemin.name} ({source.chemin.stat().st_size / 1e6:.0f} Mo)")

    print("2/5  Transcription")
    transcription = transcribe.transcrire(cfg, source.chemin, source.video_id)
    print(f"     {len(transcription.mots)} mots horodates")

    print("3/5  Selection des extraits")
    extraits = segment.selectionner(cfg, transcription, source.video_id)
    print(f"     {len(extraits)} extraits retenus")

    dossier = _dossier_extraits(cfg)
    for extrait in extraits:
        print(f"4/5  Rendu {extrait.id} ({extrait.duree:.0f}s) — {extrait.accroche[:50]}")
        try:
            edit.rendre(cfg, extrait, source.chemin, transcription)
        except edit.RenduEchoue as erreur:
            print(f"     ECHEC : {erreur}", file=sys.stderr)
            continue

        print(f"5/5  Redaction des metadonnees {extrait.id}")
        variantes = metadata.rediger(cfg, extrait, transcription)
        # On stocke la variante Instagram par defaut ; les autres sont
        # regenerees a la publication depuis le meme fichier.
        extrait.metadonnees = variantes["instagram"]
        _sauver_variantes(dossier, extrait, variantes)

        if source.attribution:
            extrait.metadonnees.description += f"\n\n{source.attribution}"

        extrait.sauver(dossier)

    print(f"\nTermine. Passe en revue : python -m src.cli revue")
    return 0


def _sauver_variantes(dossier: Path, extrait: Extrait, variantes: dict) -> None:
    import json

    chemin = dossier / f"{extrait.id}.meta.json"
    chemin.write_text(
        json.dumps(
            {k: v.__dict__ for k, v in variantes.items()}, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )


def _charger_variantes(dossier: Path, extrait: Extrait) -> dict[str, Metadonnees]:
    import json

    chemin = dossier / f"{extrait.id}.meta.json"
    if not chemin.exists():
        base = extrait.metadonnees or Metadonnees(titre=extrait.id, description="")
        return {p: base for p in ("instagram", "tiktok", "youtube")}
    brut = json.loads(chemin.read_text(encoding="utf-8"))
    return {k: Metadonnees(**v) for k, v in brut.items()}


# --------------------------------------------------------------------------
# revue
# --------------------------------------------------------------------------
def commande_revue(args) -> int:
    cfg = configuration.charger()
    extraits = Extrait.charger_tous(_dossier_extraits(cfg))

    if not extraits:
        print("Aucun extrait. Lance d'abord : python -m src.cli preparer <url>")
        return 0

    print(f"{'ID':<20} {'DUREE':>6} {'SCORE':>6}  {'ETAT':<12} ACCROCHE")
    print("-" * 100)
    for extrait in extraits:
        if extrait.publications:
            etat = "publie"
        elif extrait.valide:
            etat = "valide"
        elif extrait.chemin_rendu:
            etat = "a valider"
        else:
            etat = "sans rendu"
        print(
            f"{extrait.id:<20} {extrait.duree:>5.0f}s {extrait.score:>6}  "
            f"{etat:<12} {extrait.accroche[:44]}"
        )

    if args.detail:
        print()
        for extrait in extraits:
            print(f"\n=== {extrait.id} ===")
            print(f"  fenetre      : {extrait.debut:.1f}s -> {extrait.fin:.1f}s")
            print(f"  justification: {extrait.justification}")
            print(f"  rendu        : {extrait.chemin_rendu or '-'}")
            if extrait.metadonnees:
                print(f"  titre        : {extrait.metadonnees.titre}")
                print(f"  legende      : {extrait.metadonnees.description[:160]}")
            if extrait.publications:
                for plateforme, identifiant in extrait.publications.items():
                    print(f"  {plateforme:<12} : {identifiant}")
    return 0


# --------------------------------------------------------------------------
# valider
# --------------------------------------------------------------------------
def commande_valider(args) -> int:
    cfg = configuration.charger()
    dossier = _dossier_extraits(cfg)

    for identifiant in args.ids:
        chemin = dossier / f"{identifiant}.json"
        if not chemin.exists():
            print(f"{identifiant} : introuvable", file=sys.stderr)
            continue
        extrait = Extrait.charger(chemin)
        if not extrait.chemin_rendu or not Path(extrait.chemin_rendu).exists():
            print(f"{identifiant} : pas de rendu, validation refusee", file=sys.stderr)
            continue
        extrait.valide = True
        extrait.sauver(dossier)
        print(f"{identifiant} : valide")
    return 0


# --------------------------------------------------------------------------
# publier
# --------------------------------------------------------------------------
def commande_publier(args) -> int:
    cfg = configuration.charger()
    dossier = _dossier_extraits(cfg)
    plateformes = cfg.publication["plateformes"]

    extraits = Extrait.charger_tous(dossier)
    if args.id:
        extraits = [e for e in extraits if e.id in args.id]

    a_publier = [
        e
        for e in extraits
        if e.chemin_rendu
        and (e.valide or not cfg.publication.get("validation_humaine", True))
    ]

    if not a_publier:
        print("Rien a publier. Valide d'abord des extraits : "
              "python -m src.cli valider <id>")
        return 0

    code_sortie = 0
    for extrait in a_publier:
        variantes = _charger_variantes(dossier, extrait)
        print(f"\n=== {extrait.id} ===")

        # Le televersement vers le stockage objet n'est necessaire que pour
        # Instagram, mais il sert aussi d'archive : on le fait une fois.
        if plateformes.get("instagram") and not extrait.url_publique:
            print("  televersement vers le stockage objet…")
            extrait.url_publique = storage.televerser(Path(extrait.chemin_rendu))
            print(f"  {extrait.url_publique}")
            extrait.sauver(dossier)

        for nom, actif in plateformes.items():
            if not actif or nom in extrait.publications:
                continue
            try:
                module = _connecteur(nom)
                identifiant = module.publier(
                    extrait, variantes[nom], **_options(cfg, nom)
                )
                extrait.publications[nom] = identifiant
                extrait.sauver(dossier)
                suffixe = (
                    "  -> depose dans tes brouillons TikTok"
                    if nom == "tiktok"
                    and cfg.publication.get("tiktok_mode", "brouillon") == "brouillon"
                    else ""
                )
                print(f"  {nom:<10} OK  {identifiant}{suffixe}")
            except ErreurPublication as erreur:
                code_sortie = 1
                print(f"  {nom:<10} ECHEC  {erreur}", file=sys.stderr)
            except Exception:  # noqa: BLE001 - on veut continuer les autres plateformes
                code_sortie = 1
                print(f"  {nom:<10} ERREUR INATTENDUE", file=sys.stderr)
                traceback.print_exc()

    return code_sortie


def _connecteur(nom: str):
    from .publish import instagram, tiktok, youtube

    return {"instagram": instagram, "tiktok": tiktok, "youtube": youtube}[nom]


def _options(cfg, nom: str) -> dict:
    """Options de publication propres a chaque plateforme, lues dans config.yaml."""
    if nom == "tiktok":
        return {"mode": cfg.publication.get("tiktok_mode", "brouillon")}
    if nom == "youtube":
        return {"visibilite": cfg.publication.get("youtube_visibilite", "private")}
    return {}


# --------------------------------------------------------------------------
# auth-youtube
# --------------------------------------------------------------------------
def commande_auth_youtube(args) -> int:
    """Deroule le consentement OAuth et affiche le refresh token a coller dans .env."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    from .config import secret
    from .publish.youtube import PORTEES

    flux = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": secret("YOUTUBE_CLIENT_ID"),
                "client_secret": secret("YOUTUBE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        },
        scopes=PORTEES,
    )
    identifiants = flux.run_local_server(port=0, prompt="consent")
    print("\nColle cette ligne dans automation/.env :\n")
    print(f"YOUTUBE_REFRESH_TOKEN={identifiants.refresh_token}")
    return 0


# --------------------------------------------------------------------------
# auth-tiktok
# --------------------------------------------------------------------------
def commande_auth_tiktok(args) -> int:
    """Deroule le consentement TikTok et affiche les deux jetons a coller."""
    from .config import _charger_env
    from .publish.tiktok import parcours_autorisation

    _charger_env(configuration.RACINE / ".env")

    charge = parcours_autorisation(mode=args.mode, port=args.port)

    heures = int(charge.get("expires_in", 0)) // 3600
    jours = int(charge.get("refresh_expires_in", 0)) // 86400
    print("\nColle ces deux lignes dans automation/.env :\n")
    print(f"TIKTOK_ACCESS_TOKEN={charge['access_token']}")
    print(f"TIKTOK_REFRESH_TOKEN={charge['refresh_token']}")
    print(f"\nPortees accordees : {charge.get('scope', '?')}")
    print(f"Jeton d'acces valable {heures} h, rafraichissement valable {jours} jours.")
    print("Ensuite, `python -m src.tokens` renouvelle l'acces sans repasser par ici.")
    return 0


# --------------------------------------------------------------------------
def principal(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        prog="shorts", description="Chaine video longue -> shorts publies"
    )
    sous = analyseur.add_subparsers(dest="commande", required=True)

    p = sous.add_parser("preparer", help="source -> extraits rendus, prets a valider")
    p.add_argument("cible", help="URL YouTube, identifiant de video, ou chemin local")
    p.set_defaults(fonction=commande_preparer)

    p = sous.add_parser("revue", help="liste les extraits et leur etat")
    p.add_argument("--detail", action="store_true", help="affiche les metadonnees")
    p.set_defaults(fonction=commande_revue)

    p = sous.add_parser("valider", help="autorise la publication d'un ou plusieurs extraits")
    p.add_argument("ids", nargs="+")
    p.set_defaults(fonction=commande_valider)

    p = sous.add_parser("publier", help="publie les extraits valides")
    p.add_argument("--id", nargs="*", help="restreint a ces identifiants")
    p.set_defaults(fonction=commande_publier)

    p = sous.add_parser("auth-youtube", help="genere le refresh token YouTube")
    p.set_defaults(fonction=commande_auth_youtube)

    p = sous.add_parser("auth-tiktok", help="genere les jetons TikTok")
    p.add_argument(
        "--mode",
        choices=("brouillon", "direct"),
        default="brouillon",
        help="brouillon = scope video.upload (aucun audit) ; direct = video.publish",
    )
    p.add_argument(
        "--port",
        type=int,
        default=8080,
        help="doit correspondre au Redirect URI declare sur l'application",
    )
    p.set_defaults(fonction=commande_auth_tiktok)

    args = analyseur.parse_args(argv)
    try:
        return args.fonction(args)
    except (configuration.SecretManquant, ErreurPublication) as erreur:
        # Un secret absent ou une plateforme qui refuse sont des situations
        # ordinaires de mise en place, pas des bogues : afficher la phrase
        # utile plutot qu'une pile d'appels qui la noie.
        print(f"\n{erreur}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(principal())
