# Droits et conformité

Ce document existe parce que la question « dériver des shorts depuis de vraies
vidéos YouTube » recouvre trois situations très différentes, dont une seule
est sans risque. Le choix se fait dans `config.yaml`, clé `source.mode`.

## Les trois cas

| Cas | `source.mode` | Risque | Verdict |
|---|---|---|---|
| **A** — tes propres vidéos | `proprietaire` | aucun | ✅ Recommandé |
| **B** — vidéos tierces sous Creative Commons | `creative_commons` | faible, attribution obligatoire | ✅ Utilisable |
| **C** — vidéos tierces sous licence YouTube standard | *non implémenté* | élevé | ❌ Non couvert |

### Cas A — tes propres vidéos

Tu détiens les droits. Rien ne s'oppose à découper, recadrer, sous-titrer et
republier ailleurs. C'est le mode par défaut de la configuration, et de loin
le meilleur usage de cette chaîne : une vidéo longue de 15 minutes donne 5 à
8 shorts, ce qui multiplie la portée d'un travail déjà fait.

**Une seule précaution** : la musique. Si ta vidéo YouTube contient une piste
sous licence YouTube Audio Library, cette licence ne te suit pas
automatiquement sur TikTok ou Instagram. Choisis des extraits sans musique de
fond, ou remplace la piste.

### Cas B — Creative Commons

YouTube propose un filtre de recherche « Creative Commons » : les vidéos
concernées sont sous **CC BY 3.0**, qui autorise explicitement la
redistribution et les œuvres dérivées, **à condition de créditer l'auteur**.

Le code applique deux garde-fous :

1. `src/ingest.py` interroge l'API YouTube Data pour lire le champ
   `status.license` **avant tout téléchargement**, et refuse de continuer si
   la valeur n'est pas `creativeCommon` ;
2. la ligne d'attribution est générée automatiquement et ajoutée à la
   description publiée (`Source.attribution`).

Ce qui reste à ta charge : vérifier que la personne qui a publié la vidéo
avait bien le droit de la placer sous CC. Une vidéo marquée CC qui contient
un extrait de match sous droits reste problématique — le tag de licence
n'assainit pas le contenu qu'il recouvre.

### Cas C — vidéos tierces sous licence standard

C'est le cas que la chaîne **n'implémente délibérément pas**, pour trois
raisons cumulatives :

1. **Les CGU de YouTube l'interdisent.** Elles prohibent l'accès au contenu
   « par tout moyen autre que les pages de lecture du service, le lecteur
   intégrable, ou d'autres moyens explicitement autorisés ». Télécharger une
   vidéo tierce sort de ce cadre, indépendamment de ce que tu en fais ensuite.
2. **Le droit d'auteur s'applique.** Une œuvre dérivée d'une œuvre protégée
   nécessite l'autorisation de l'ayant droit. L'exception de courte citation
   en droit français est étroite : elle suppose un caractère critique ou
   pédagogique, une longueur proportionnée, et le crédit de l'auteur. Un short
   de 60 secondes republié pour lui-même n'y entre pas.
3. **Ça ne marche pas techniquement.** Content ID et les systèmes équivalents
   de Meta et TikTok détectent le contenu réutilisé, y compris recadré,
   sous-titré et ré-encodé. Les issues vont de la démonétisation au blocage
   et, en cas de récidive, à la fermeture du compte.

Le troisième point est celui qui devrait emporter la décision même en mettant
le droit de côté : bâtir une audience sur un compte qui peut disparaître pour
strike est un mauvais investissement.

**Si tu veux malgré tout exploiter du contenu tiers**, la voie propre est la
licence directe : beaucoup de créateurs et de clubs accordent une autorisation
écrite pour une demande précise. Un accord par courriel qui nomme la vidéo,
l'usage et la durée suffit. Passe alors en mode `fichier` avec le master qu'on
t'aura transmis, et garde l'écrit.

---

## Déclaration de contenu généré par IA

Les trois plateformes imposent désormais de signaler les contenus générés ou
significativement modifiés par IA.

Ce que fait cette chaîne :

| Traitement | Contenu synthétique ? |
|---|---|
| Découpe temporelle | non |
| Recadrage 9:16, fond flou | non |
| Sous-titres transcrits automatiquement | non |
| Titre et description rédigés par un modèle | non — c'est du texte d'accompagnement, pas le média |

**Aucune étape ne fabrique d'image ou de voix.** Le champ `is_aigc` est donc à
`false` dans `src/publish/tiktok.py`, ce qui est correct en l'état.

Si tu ajoutes plus tard une voix de synthèse, un avatar, ou des plans générés,
passe ce champ à `true` et active l'équivalent chez Meta (*Paramètres avancés →
contenu généré par IA*). La sanction pour non-déclaration est plus lourde que
le coût de la déclaration.

---

## Données personnelles

La photographie de sport implique des personnes identifiables. Le passage de
la photo au short vidéo ne change pas les règles, mais élargit la diffusion :

- **Droit à l'image** : la publication d'une personne identifiable nécessite
  son accord, sauf exceptions (personnalité publique dans l'exercice de sa
  fonction, événement d'actualité, foule où personne n'est individualisé).
  Une compétition sportive publique entre généralement dans le cadre de
  l'actualité, mais un portrait isolé en gros plan beaucoup moins.
- **Mineurs** : accord des représentants légaux, sans exception.
- **Accréditations** : les conditions d'accréditation des clubs et fédérations
  restreignent souvent l'usage commercial des images. Relis celles qui
  t'ont été délivrées avant de faire tourner la chaîne sur ces rushes.

La chaîne n'automatise aucune de ces vérifications — elles supposent un
jugement que le code ne peut pas rendre. C'est l'une des raisons pour
lesquelles la porte de validation humaine est activée par défaut.

---

## Récapitulatif décisionnel

```
La vidéo source est-elle la tienne ?
├── oui  ──▶ mode `proprietaire`. Vérifier seulement la musique.
└── non
    ├── Licence CC BY sur YouTube ?
    │   ├── oui ──▶ mode `creative_commons`. Attribution automatique.
    │   └── non
    │       ├── Autorisation écrite de l'ayant droit ?
    │       │   ├── oui ──▶ mode `fichier`. Conserver l'écrit.
    │       │   └── non ──▶ ne pas publier.
```
