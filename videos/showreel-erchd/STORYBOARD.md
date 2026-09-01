---
project: showreel-erchd
aspect: 1080x1920
duration: 10.0
mode: autonomous
message: "Edouard Richard photographie le sport de tout près — 19 vues, 4 séries, une seule poussée de caméra."
current: z-forward
---

# Planche 01 — showreel 10 s

**Courant du film :** Z avant (poussée). Toutes les coutures sont des
zoom-through de même signe — `d(scale)/dt > 0` des deux côtés de chaque coupe.
Aucun fondu enchaîné. Un seul vecteur réservé est dépensé : l'élévation du
logotype sur la carte de fin, à une frontière de chapitre.

**Deux plans :** le plan photographique porte la caméra (il est l'objet
porteur à travers chaque coupe) ; le plan typographique est une surimpression
qui a sa propre entrée en cascade. Séparation volontaire : une typo qui grossit
de 1,14 à 1,36 sort du cadre et se dégrade.

## Frame 1 — Ouverture
- `src`: index.html § scene-open · `data-start` 0.00 · durée 2.30
- **Motion**: rules `camera-push` + `waterfall-entry`. Photo plein cadre,
  échelle 1.00 → 1.09 (`power2.out`) puis 1.09 → 1.26 (`power3.in`) : la sortie
  accélère dans la coupe. Nom en deux lignes, cascade 90 ms.
- **Beat**: « Edouard Richard — photographe sportif, Rouen »

## Frames 2–5 — Les quatre séries
- `src`: index.html § scene-hockey / basket / foot / boxe
- `data-start` 2.30 / 3.30 / 4.30 / 5.30 · durée 1.00 chacune
- **Motion**: rule `zoom-through`. Entrée à 1.14 → 1.21 (`power3.out`, reprise
  à mi-vol), sortie 1.21 → 1.36 (`power3.in`). Même signe, aucun rebond.
- **Beat**: chiffre romain, titre de série, légende réelle et lieu/date tirés
  de `series.ts`. Le tirage est encadré, pas plein cadre : les sources font
  1000×1500, le plein cadre les ferait fondre.

## Frame 6 — La planche contact
- `src`: index.html § scene-sheet · `data-start` 6.30 · durée 1.85
- **Motion**: route `staged reveals` puis `camera with intent`.
  16 vignettes arrivent en cascade (0 → 0,90 s), **immobilité 0,25 s**
  (la virgule dramatique), puis la caméra pousse dans une cellule
  1.16 → 1.52 avec recentrage.
- **Beat**: « 19 vues — 4 séries — 2024 / 2026 »

## Frame 7 — Carte de fin
- `src`: index.html § scene-end · `data-start` 8.15 · durée 1.85
- **Motion**: la poussée continue en fond (1.05 → 1.12, `power2.out` : le signe
  Z reste positif), le logotype s'élève — vecteur réservé « élévation »,
  dépensé sur une frontière de chapitre.
- **Beat**: logotype, métier, adresse du site.

## Décisions d'exécution

- **Un seul fichier.** `lint` avertit que la piste 1 porte 7 éléments et suggère
  des sous-compositions. Refusé ici : la continuité des vecteurs (la vitesse
  d'échelle doit se raccorder de part et d'autre de chaque coupe) vit dans la
  timeline maîtresse. Sur 10 s et 7 plans, la découper coûte plus qu'elle ne
  rapporte. Avertissement assumé, zéro erreur.
- **Zone de sécurité 9:16.** L'UI Instagram / TikTok masque les ~270 px du bas
  et une colonne à droite. Aucun texte utile sous `y = 1650`, ni à droite de
  `x = 930`.
- **Deux plans, pas un.** La caméra (poussée en Z) porte le plan
  photographique ; la typographie est une surimpression fixe. Faire grossir la
  typo avec la caméra la sort du cadre et la ramollit.
- **Pas de recadrage automatique agressif.** Les tirages sont redimensionnés
  puis recadrés au centre par `object-fit: cover` — la composition d'origine du
  photographe est préservée autant que le format 9:16 le permet.
- **Aucun appel réseau au rendu.** GSAP est dans `vendor/`, les trois polices
  sont en `.woff2` dans `assets/fonts/`, le grain est un PNG déterministe
  (PRNG à graine fixe). Le rendu est reproductible hors ligne.
