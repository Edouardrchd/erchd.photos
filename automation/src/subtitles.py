"""Etape 4a - Generation des sous-titres incrustes au format ASS.

Le rendu vise le standard visuel des shorts : 3 mots a l'ecran, gros, centres
au tiers bas, le mot en cours de prononciation colore. On genere donc un
evenement ASS par mot (et non par phrase), chacun affichant le groupe entier
avec un seul mot mis en avant.

ASS plutot que SRT parce que SRT ne sait pas porter de style : ni police, ni
contour, ni couleur par mot. Le fichier produit est ensuite incruste par
ffmpeg via le filtre `subtitles=`.
"""

from __future__ import annotations

from pathlib import Path

from .models import Mot

ENTETE = """[Script Info]
ScriptType: v4.00+
PlayResX: {largeur}
PlayResY: {hauteur}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{police},{taille},{couleur},&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,{contour},{ombre},5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
"""


def _horodatage(secondes: float) -> str:
    """Convertit des secondes en H:MM:SS.CC, le format attendu par ASS."""
    secondes = max(0.0, secondes)
    heures, reste = divmod(secondes, 3600)
    minutes, sec = divmod(reste, 60)
    centiemes = int(round((sec - int(sec)) * 100))
    if centiemes == 100:          # arrondi qui deborde
        sec, centiemes = int(sec) + 1, 0
    return f"{int(heures)}:{int(minutes):02d}:{int(sec):02d}.{centiemes:02d}"


def _inline(couleur_ass: str) -> str:
    """`&H00FFFFFF` (style) -> `&HFFFFFF&` (override inline dans le texte)."""
    valeur = couleur_ass.replace("&H", "").replace("&", "")
    if len(valeur) == 8:          # AABBGGRR -> on retire l'alpha
        valeur = valeur[2:]
    return f"&H{valeur}&"


def _echapper(texte: str) -> str:
    """Neutralise les caracteres qui ont un sens pour le moteur ASS."""
    return texte.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def _grouper(mots: list[Mot], par_ecran: int) -> list[list[Mot]]:
    """Decoupe la liste de mots en groupes affiches ensemble.

    Une pause de plus de 0,6 s force un nouveau groupe : sans cela, un mot
    isole apres un silence resterait colle au groupe precedent et l'affichage
    se desynchroniserait de la parole.
    """
    groupes: list[list[Mot]] = []
    courant: list[Mot] = []

    for mot in mots:
        pause = courant and (mot.debut - courant[-1].fin) > 0.6
        if pause or len(courant) >= par_ecran:
            groupes.append(courant)
            courant = []
        courant.append(mot)

    if courant:
        groupes.append(courant)
    return groupes


def generer(
    mots: list[Mot],
    destination: Path,
    reglages: dict,
    decalage: float,
    largeur: int = 1080,
    hauteur: int = 1920,
) -> Path:
    """Ecrit le fichier .ass pour un extrait.

    `decalage` est le temps de debut de l'extrait dans la video source : les
    horodatages des mots sont absolus, il faut les ramener a zero.
    """
    couleur_normale = _inline(reglages["couleur"])
    couleur_active = _inline(reglages["couleur_active"])
    y = int(hauteur * reglages["position_v"] / 100)

    lignes = [
        ENTETE.format(
            largeur=largeur,
            hauteur=hauteur,
            police=reglages["police"],
            taille=reglages["taille"],
            couleur=reglages["couleur"],
            contour=reglages["contour"],
            ombre=reglages["ombre"],
        )
    ]

    for groupe in _grouper(mots, reglages["mots_par_ecran"]):
        for index, mot in enumerate(groupe):
            debut = mot.debut - decalage
            # Le groupe reste affiche jusqu'au mot suivant : pas de clignotement
            fin = (
                groupe[index + 1].debut - decalage
                if index + 1 < len(groupe)
                else mot.fin - decalage + 0.15
            )
            if fin <= debut:
                continue

            morceaux = []
            for position, autre in enumerate(groupe):
                couleur = couleur_active if position == index else couleur_normale
                morceaux.append(f"{{\\c{couleur}}}{_echapper(autre.texte)}")
            texte = " ".join(morceaux)

            # 8 virgules exactement avant le champ Text : Layer, Start, End,
            # Style, Name, MarginL, MarginR, Effect. Une virgule de trop et
            # libass verse le reliquat dans le texte affiche.
            lignes.append(
                f"Dialogue: 0,{_horodatage(debut)},{_horodatage(fin)},Default,,0,0,0,"
                f"{{\\pos({largeur // 2},{y})}}{texte}"
            )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return destination
