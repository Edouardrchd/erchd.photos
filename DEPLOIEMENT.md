# Mise en ligne — Portfolio Edouard Richard

## Ce qui est livré

| Fichier | Rôle |
|---|---|
| `index.html` | Le site entier : HTML statique, styles inline, JavaScript natif en fin de page. Aucune dépendance : pas de React, pas de Babel, pas de script CDN, pas de build. |
| `photos/` | Les photos, en chemins relatifs `photos/xxx.jpg`. |

Seules ressources externes : les quatre familles Google Fonts (Big Shoulders Display, Instrument Serif, Space Mono, Archivo). Pour supprimer cette dépendance, auto-héberger les `woff2` et remplacer le `<link>` par des `@font-face` avec `font-display: swap`.

Les fichiers `support.js`, `image-slot.js` et les deux `.dc.html` sont les sources de conception : **ne pas les déployer**.

## Déploiement

1. Copier `index.html` + `photos/` dans la racine publique.
2. Déployer : Cloudflare Pages, Netlify, Vercel, GitHub Pages, ou FTP (`/www`).
3. Domaine + HTTPS.

## Étape suivante : variantes d'images

`index.html` porte déjà les attributs `srcset` attendus, au format `photos/nom-800.webp 800w` (puis `-1400`, `-2000` quand la largeur d'origine le permet). Le fichier d'origine reste dans `src` comme repli, et un gestionnaire d'erreur en fin de page retire `srcset` si la variante n'existe pas encore : le site fonctionne donc avant génération.

À générer avec sharp, sans jamais agrandir :

```
sharp(src).resize({ width: 800, withoutEnlargement: true }).webp({ quality: 82 })
```

Largeurs d'origine actuelles : 409 à 1200 px. Aucune photo n'atteint 1400 px, donc seule la variante 800w est déclarée, et seulement sur six images (er-fb-01, er-fb-02, er-bx-01, er-bx-02, er-bx-07, er-py-01). Pour un portfolio professionnel, ré-exporter les fichiers depuis les originaux en 1600–2400 px de large avant de générer les variantes.

## Réglages serveur

- `photos/*` : `Cache-Control: public, max-age=31536000, immutable`
- `index.html` : `Cache-Control: no-cache`
- Brotli/gzip sur HTML et JSON
- `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`
- CSP autorisant `fonts.googleapis.com` et `fonts.gstatic.com`
- Ajouter `robots.txt` et `sitemap.xml`

## À compléter dans `index.html`

- `og:url` et `og:image` : remplacer les chemins relatifs par des URL absolues du domaine.
- Liens sociaux : Instagram et Linktree pointent encore sur `https://instagram.com/` et `https://linktr.ee/` (en-tête), et le lien « Instagram » du pied de page sur `#`.
- Favicon.

## Contenu

- Textes : figés dans le HTML, éditables directement dans le fichier.
- Cadres : chaque cadre porte en dur le ratio réel de son fichier (`aspect-ratio`), donc aucun recadrage et aucun décalage au chargement.
- Ajouter une photo : déposer le fichier dans `photos/`, dupliquer un bloc `<figure data-photo>` et renseigner `src`, `width`, `height`, `alt`, l'`aspect-ratio` du cadre, et les champs `data-num` / `data-lieu` / `data-date`.
- Nommage : `er-fb-*` football, `er-bk-*` basketball, `er-bx-*` boxe, `er-hk-*` hockey, `er-hb-*` handball, `er-py-*` paysage, `er-burst-*` tirages du hero.
