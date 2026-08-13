import { imageSize } from 'image-size';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

/**
 * TOUTES LES PHOTOGRAPHIES DU SITE SONT DECRITES ICI.
 *
 * Pour ajouter une photo : deposez le fichier dans public/images/, puis
 * ajoutez une ligne dans la serie voulue. Rien d'autre.
 *
 * Les dimensions de l'image sont lues automatiquement dans le fichier au
 * moment de la construction du site : il n'y a plus de data-w / data-h a
 * relever a la main, et la mosaique ne peut plus se deformer.
 * Les numeros (01, 02...) et les compteurs de chaque serie sont eux aussi
 * calcules tout seuls, a partir de l'ordre de cette liste.
 */
export type PhotoInput = {
  /** Nom du fichier dans public/images/ */
  file: string;
  /** Legende affichee sous la photo et dans la visionneuse */
  cap: string;
  /** Lieu et date, par exemple 'Rouen-Amiens · 10.11.25' */
  meta: string;
  /** Description pour les lecteurs d'ecran et les moteurs de recherche */
  alt: string;
};

export type SerieInput = {
  /** Identifiant utilise dans l'adresse (#hockey) et le menu */
  id: string;
  /** Chiffre romain affiche devant le titre */
  numeral: string;
  title: string;
  /** Libelle court, pour la barre de navigation */
  short: string;
  /** Villes ou lieux, affiches sur la vignette de la serie */
  place: string;
  /** Periode affichee a droite du titre de galerie */
  period: string;
  /** Image de couverture de la serie, dans public/images/ */
  cover: string;
  photos: PhotoInput[];
};

const series: SerieInput[] = [
  {
    id: 'hockey',
    numeral: 'I',
    title: 'Hockey sur glace',
    short: 'Hockey',
    place: 'Rouen · Amiens',
    period: '2025',
    cover: 'serie-hockey.jpg',
    photos: [
      { file: 'hockey-sur-glace-01-hymne-d-avant-match.jpg', cap: 'Hymne d\'avant-match', meta: 'Rouen–Amiens · 10.11.25', alt: 'Hymne d\'avant-match — hockey sur glace, Rouen contre Amiens' },
      { file: 'hockey-sur-glace-02-les-gothiques-dans-le-couloir-d-acces.jpg', cap: 'Les Gothiques dans le couloir d\'accès', meta: 'Rouen–Amiens · 10.11.25', alt: 'Les Gothiques d\'Amiens dans le couloir d\'accès à la patinoire' },
      { file: 'hockey-sur-glace-03-portrait-en-sortie-de-glace.jpg', cap: 'Portrait en sortie de glace', meta: 'Rouen–Amiens · 10.11.25', alt: 'Portrait d\'un joueur en sortie de glace' },
      { file: 'hockey-sur-glace-04-richards-et-lemay-sur-le-banc.jpg', cap: 'Richards et Lemay sur le banc', meta: 'Rouen–Amiens · 10.11.25', alt: 'Richards et Lemay sur le banc des joueurs' },
      { file: 'hockey-sur-glace-05-file-sur-un-joueur-lance.jpg', cap: 'Filé sur un joueur lancé', meta: 'Rouen–Amiens · 10.11.25', alt: 'Filé photographique sur un joueur de hockey lancé' },
      { file: 'hockey-sur-glace-06-casque-du-meilleur-buteur.jpg', cap: 'Casque du meilleur buteur', meta: 'Rouen–Amiens · 10.11.25', alt: 'Détail du casque du meilleur buteur de la rencontre' }
    ]
  },
  {
    id: 'basket',
    numeral: 'II',
    title: 'Basketball',
    short: 'Basket',
    place: 'Rouen · Caen',
    period: '2024/2025',
    cover: 'serie-basket.jpg',
    photos: [
      { file: 'basketball-01-portrait-de-profil-fin-de-match.jpg', cap: 'Portrait de profil, fin de match', meta: 'Rouen · 14.11.25', alt: 'Portrait de profil d\'un joueur de basket en fin de match' },
      { file: 'basketball-02-un-contre-un.jpg', cap: 'Un contre un', meta: 'Rouen · 14.11.25', alt: 'Un contre un sur le parquet, l\'attaquant face à son défenseur' },
      { file: 'basketball-03-la-salle-vue-des-tribunes.jpg', cap: 'La salle, vue des tribunes', meta: 'Rouen · 14.11.25', alt: 'Vue d\'ensemble de la salle depuis les tribunes' },
      { file: 'basketball-04-entre-deux.jpg', cap: 'Entre-deux', meta: 'Caen · 24.04.24', alt: 'Entre-deux au coup d\'envoi d\'un match de basket' },
      { file: 'basketball-05-tir-en-suspension.jpg', cap: 'Tir en suspension', meta: 'Caen · 24.04.24', alt: 'Tir en suspension au-dessus d\'un défenseur, match de basket à Caen' },
      { file: 'basketball-06-balle-en-main.jpg', cap: 'Balle en main', meta: 'Rouen · 14.11.25', alt: 'Joueur de basket balle en main, face au jeu' }
    ]
  },
  {
    id: 'football',
    numeral: 'III',
    title: 'Football',
    short: 'Football',
    place: 'Caen',
    period: '2025',
    cover: 'serie-football.jpg',
    photos: [
      { file: 'football-01-frappe-depuis-le-corner.jpg', cap: 'Frappe depuis le corner', meta: 'Caen–Paris 13 · 07.11.25', alt: 'Frappe depuis le corner lors de Caen contre Paris 13' },
      { file: 'football-02-sortie-de-terrain.jpg', cap: 'Sortie de terrain', meta: 'Caen–Paris 13 · 07.11.25', alt: 'Joueur quittant la pelouse en sortie de terrain' },
      { file: 'football-03-file-sur-un-joueur-en-course.jpg', cap: 'Filé sur un joueur en course', meta: 'Caen–Paris 13 · 07.11.25', alt: 'Filé photographique sur un joueur de football en course' },
      { file: 'football-04-salut-aux-tribunes-avant-le-coup-d-envoi.jpg', cap: 'Salut aux tribunes, avant le coup d\'envoi', meta: 'Caen–Paris 13 · 07.11.25', alt: 'Joueur du Stade Malherbe saluant les tribunes avant le coup d\'envoi' }
    ]
  },
  {
    id: 'boxe',
    numeral: 'IV',
    title: 'Boxe',
    short: 'Boxe',
    place: 'Gala',
    period: '2024',
    cover: 'serie-boxe.jpg',
    photos: [
      { file: 'boxe-01-montee-sur-le-ring.jpg', cap: 'Montée sur le ring', meta: 'Gala · 14.03.24', alt: 'Boxeur montant sur le ring avant son combat' },
      { file: 'boxe-02-dans-le-tunnel.jpg', cap: 'Dans le tunnel', meta: 'Gala · 14.03.24', alt: 'Boxeur de dos dans le tunnel, veste de son équipe, avant la montée sur le ring' },
      { file: 'boxe-03-coulisses-avant-l-entree.jpg', cap: 'Coulisses, avant l\'entrée', meta: 'Gala · 14.03.24', alt: 'Coulisses d\'un gala de boxe, avant l\'entrée sur le ring' }
    ]
  }
];

/* ------------------------------------------------------------------ */

export type Photo = PhotoInput & { w: number; h: number; n: string };
export type Serie = Omit<SerieInput, 'photos'> & { photos: Photo[]; count: string };

const dir = new URL('../../public/images/', import.meta.url);

function measure(file: string) {
  try {
    const { width, height } = imageSize(readFileSync(new URL(file, dir)));
    if (!width || !height) throw new Error('dimensions introuvables');
    return { w: width, h: height };
  } catch (e) {
    throw new Error(
      `Impossible de lire les dimensions de public/images/${file}. ` +
      `Verifiez que le fichier existe et que son nom est ecrit exactement pareil ` +
      `dans src/data/series.ts (majuscules comprises).`
    );
  }
}

const pad = (n: number) => String(n).padStart(2, '0');

export const SERIES: Serie[] = series.map((s) => ({
  ...s,
  count: pad(s.photos.length),
  photos: s.photos.map((p, i) => ({ ...p, ...measure(p.file), n: pad(i + 1) }))
}));

/** Nombre total de photographies, affiche en page d'accueil. */
export const TOTAL = SERIES.reduce((n, s) => n + s.photos.length, 0);

/** L'adresse publique du site, utilisee par les apercus de lien. */
export const SITE = 'https://edouardvisuals.com';
