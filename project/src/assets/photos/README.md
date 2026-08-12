# Comment ajouter des photos

Depose simplement tes fichiers dans le dossier de la categorie voulue :

| Categorie  | Dossier                            | URL du site           |
| ---------- | ---------------------------------- | --------------------- |
| Football   | `src/assets/photos/football/`      | `/gallery/football`   |
| Basketball | `src/assets/photos/basketball/`    | `/gallery/basketball` |
| Handball   | `src/assets/photos/handball/`      | `/gallery/handball`   |
| Boxe       | `src/assets/photos/boxing/`        | `/gallery/boxing`     |

Il n'y a **aucune liste a mettre a jour** : les photos presentes dans ces
dossiers sont detectees automatiquement au moment du build (`src/photos.ts`).

## Bonnes pratiques

- **Formats acceptes** : `.jpg`, `.jpeg`, `.png`, `.webp`, `.avif`.
- **Ordre d'affichage** : les photos sont triees par nom de fichier. Pour
  choisir l'ordre, prefixe-les : `01-match.jpg`, `02-tribune.jpg`, etc.
- **Photo de couverture** : la premiere photo de la categorie (dans cet ordre)
  sert automatiquement de vignette sur la page d'accueil.
- **Poids** : exporte en 2000 px de large maximum et en qualite ~80%, soit
  environ 300 a 600 Ko par photo. Les fichiers bruts d'appareil photo (8 Mo et
  plus) rendent le site lent a charger et le depot lourd.
- **Noms de fichiers** : evite les accents et les espaces (`psg-om-2024.jpg`
  plutot que `PSG OM été.jpg`).

## Ajouter une nouvelle categorie

1. Cree le dossier `src/assets/photos/<slug>/`.
2. Ajoute la categorie dans `CATEGORIES` (`src/photos.ts`).
3. Ajoute le lien dans le menu (`src/App.vue`).
