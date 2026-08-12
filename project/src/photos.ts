export type Photo = {
  id: string
  src: string
  alt: string
}

export type Category = {
  slug: string
  label: string
}

/**
 * Les categories du site. Le `slug` doit correspondre au nom du dossier dans
 * src/assets/photos/ ET a l'URL (/gallery/<slug>).
 */
export const CATEGORIES: Category[] = [
  { slug: 'football', label: 'Football' },
  { slug: 'basketball', label: 'Basketball' },
  { slug: 'handball', label: 'Handball' },
  { slug: 'boxing', label: 'Boxe' }
]

/**
 * Vite lit le contenu de src/assets/photos/<categorie>/ au moment du build et
 * remplace chaque fichier trouve par son URL finale. Il n'y a donc rien a
 * declarer a la main : deposer une image dans le bon dossier suffit a la faire
 * apparaitre dans la galerie.
 */
const files = import.meta.glob(
  './assets/photos/*/*.{jpg,jpeg,png,webp,avif,JPG,JPEG,PNG,WEBP,AVIF}',
  { eager: true, import: 'default', query: '?url' }
) as Record<string, string>

const prettify = (fileName: string) =>
  fileName
    .replace(/\.[^.]+$/, '')
    .replace(/[-_]+/g, ' ')
    .trim()

const byName = (a: Photo, b: Photo) =>
  a.id.localeCompare(b.id, 'fr', { numeric: true, sensitivity: 'base' })

const buildIndex = () => {
  const index: Record<string, Photo[]> = {}

  for (const [path, src] of Object.entries(files)) {
    const [, slug, fileName] = path.match(/\/photos\/([^/]+)\/([^/]+)$/) ?? []
    if (!slug || !fileName) continue

    const label = CATEGORIES.find((c) => c.slug === slug)?.label ?? slug
    const photos = index[slug] ?? (index[slug] = [])
    photos.push({ id: fileName, src, alt: `${label} - ${prettify(fileName)}` })
  }

  // Tri naturel sur le nom de fichier : nommer les photos 01-..., 02-...
  // permet donc de choisir l'ordre d'affichage.
  for (const photos of Object.values(index)) photos.sort(byName)

  return index
}

const index = buildIndex()

export const photosFor = (slug: string): Photo[] => index[slug] ?? []

export const coverFor = (slug: string): Photo | undefined => photosFor(slug)[0]

export const labelFor = (slug: string): string =>
  CATEGORIES.find((c) => c.slug === slug)?.label ?? slug
