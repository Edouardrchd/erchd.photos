# design.md — vérité de marque

Source : `src/styles/global.css` du site (thème « Nuit », par défaut) et
`src/data/series.ts`. Ces valeurs sont **strictes** : hex, familles de police,
rapports de graisse. L'application à l'échelle vidéo est libre.

## Concept

« Planche contact ». Chrome achromatique, la couleur ne vient QUE des
photographies. Le film est une planche qu'on traverse : une seule poussée de
caméra continue de la première image à l'adresse finale.

## Palette

| Rôle             | Hex       | Usage vidéo                                 |
| ---------------- | --------- | ------------------------------------------- |
| `--bg`           | `#0A0B0C` | fond de scène, unique, jamais de dégradé    |
| `--bg2`          | `#111315` | fond de cellule / planche                   |
| `--bg3`          | `#191B1D` | vide de cellule                             |
| `--ink`          | `#EDEAE3` | titres, logotype                            |
| `--ink2`         | `#9C9A93` | données mono, légendes                      |
| `--ink3`         | `#5E5D58` | chiffres romains, filets secondaires        |
| `--rule`         | `#212326` | filets, bordures de cadre (2px en vidéo)    |
| `--rule2`        | `#33373A` | filets accentués                            |
| `--on-photo`     | `#F4F2EC` | texte posé sur une image (toujours + voile) |

Pas d'accent coloré : l'accent du site est l'encre elle-même (`--acc: --ink`).

## Typographie

| Rôle    | Famille            | Vidéo                                    |
| ------- | ------------------ | ---------------------------------------- |
| Display | Instrument Serif   | italique pour le nom, 84–150px           |
| Sans    | Jost 300/400/500   | sur-titres capitales espacées, 22–30px   |
| Données | IBM Plex Mono 400  | rails, légendes, compteurs, 22–28px      |

Fichiers `.woff2` embarqués dans `assets/fonts/` — aucun appel réseau au rendu.

## Courbes

- `--e`  `cubic-bezier(.22,1,.28,1)` → GSAP `power4.out` (entrées)
- `--e2` `cubic-bezier(.65,0,.35,1)` → GSAP `power3.in` (sorties)

## À ne pas faire

- Aucun dégradé linéaire plein cadre (bandes visibles en H.264).
- Aucune teinte colorée ajoutée aux photographies.
- Aucun texte posé sur une photo sans voile sombre dessous.
- Aucune donnée inventée : 19 vues, 4 séries, chiffres tirés de `series.ts`.
