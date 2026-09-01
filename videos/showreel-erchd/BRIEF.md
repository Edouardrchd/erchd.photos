---
workflow: general-video
flow: automation
storyboard: no
message: "Edouard Richard photographie le sport de tout près — 19 vues, 4 séries, une seule poussée de caméra."
destination: instagram-reels
aspect: 1080x1920
language: fr
length: 10s
angle: showreel
---

## Intent

Bande-annonce de 10 secondes du portfolio d'Edouard Richard, photographe
sportif à Rouen. Elle doit donner en un coup d'œil : le nom, le niveau de
regard, l'étendue des séries (hockey, basket, football, boxe) et l'adresse du
site. Ton : éditorial, argentique, sec — l'inverse d'un diaporama de mariage.
Le film reprend la direction « planche contact » du site : chrome achromatique,
la couleur ne vient que des photographies.

## Assets

- `assets/photos/hero.jpg` — accueil-mobile.jpg du site, ouverture plein cadre.
- `assets/photos/s1-hockey.jpg` — « Filé sur un joueur lancé », Rouen–Amiens.
- `assets/photos/s2-basket.jpg` — « Tir en suspension », Caen.
- `assets/photos/s3-foot.jpg` — « Frappe depuis le corner », Caen–Paris 13.
- `assets/photos/s4-boxe.jpg` — « Montée sur le ring », Gala.
- `assets/thumbs/t01…t16.jpg` — la planche contact de la scène 6.
- `assets/fonts/` — Instrument Serif, Jost, IBM Plex Mono embarqués.
- `design.md` — palette et typographie extraites de `src/styles/global.css`.

## Customizations

- Zoom demandé explicitement : la poussée en Z est le courant du film, pas un
  effet ponctuel. Toutes les coupes sont des zoom-through de même signe.

## Notes

- `https://edouardrichard.mypixieset.com/` est injoignable depuis cet
  environnement (politique réseau) : aucune capture du site en ligne. Le film
  est monté sur les photographies du dépôt, qui sont la même matière.
- Chiffres tirés de `src/data/series.ts` : 19 vues, 4 séries, 2024–2026.
  Ne rien inventer.
- Pas de bande-son : non demandée. À proposer après visionnage.
- `series.ts` déclare `SITE = https://edouardvisuals.com`. La carte de fin
  affiche l'adresse Pixieset fournie dans la demande.
