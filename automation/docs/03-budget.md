# Budget et alternatives

Chiffres relevés en août 2026, hors taxes. Ils bougent — vérifie avant de
t'engager sur un abonnement annuel.

## Hypothèse de travail

4 vidéos sources par mois, 20 minutes chacune, 5 shorts extraits par vidéo,
soit **20 shorts publiés par mois** sur trois plateformes.

## Chaîne recommandée : ~5 € / mois

| Poste | Solution | Coût mensuel |
|---|---|---|
| Transcription | faster-whisper, local | 0 € |
| Sélection + rédaction | API Anthropic, Claude Opus 5 | ~3 € |
| Montage | ffmpeg, local | 0 € |
| Stockage / diffusion | Cloudflare R2 | ~0,50 € |
| Publication | API officielles | 0 € |
| **Total** | | **~4 €** |

### Détail du poste Anthropic

Le coût est presque entièrement dans la sélection, qui ingère la transcription
complète.

- Transcription de 20 min ≈ 3 000 mots ≈ 4 500 tokens en entrée.
- Sélection : 1 appel par vidéo, ~6 000 tokens entrée / 2 000 sortie.
- Rédaction : 1 appel par extrait, ~800 tokens entrée / 600 sortie.

Aux tarifs Opus 5 (5 $ / MTok en entrée, 25 $ / MTok en sortie) :

```
Sélection   : 4 vidéos × (6 000 × 5 + 2 000 × 25) / 1e6   ≈ 0,32 $
Rédaction   : 20 shorts × (800 × 5 + 600 × 25) / 1e6      ≈ 0,38 $
                                                    Total ≈ 0,70 $/mois
```

Moins d'un euro. Le budget de 3 € plus haut garde une marge confortable pour
les itérations et les extraits écartés.

> Si tu veux réduire encore : `claude-sonnet-5` sur l'étape de rédaction
> divise ce poste par deux environ. Garde Opus sur la **sélection**, qui est
> l'étape où le jugement compte : c'est elle qui détermine si le short tient
> debout hors contexte.

### Détail du poste R2

20 shorts × ~15 Mo = 300 Mo par mois. Stockage à 0,015 $/Go/mois, egress
gratuit. En supprimant les fichiers après publication (`storage.supprimer`),
le coût reste sous le seuil de facturation la plupart des mois.

---

## Variantes selon ce que tu veux éviter

### Sans machine à faire tourner : ~55 € / mois

Si tu ne veux pas gérer ffmpeg ni un serveur, une API de rendu vidéo remplace
l'étape de montage.

| Service | Tarif d'entrée | Ce qu'il apporte |
|---|---|---|
| **JSON2Video** | 16,95 $/mois (Hobby), 49 $ pour 200 min HD | sous-titres + TTS inclus dans les crédits |
| **Shotstack** | 49 $/mois pour 200 min | moteur de rendu solide, pas d'IA intégrée |
| **Creatomate** | 54 $/mois (~143 min en 720p) | éditeur visuel, TTS facturé en plus |

Pour ce cas d'usage, **JSON2Video** est le meilleur rapport : le sous-titrage
automatique et la synthèse vocale sont compris dans les crédits de rendu, là
où Creatomate facture le TTS séparément et Shotstack ne le propose pas.

Mais il faut voir ce que ça coûte vraiment : **~50 €/mois pour éviter
d'installer ffmpeg**, alors que le rendu local est gratuit, plus rapide sur
une machine correcte, et sans limite de minutes. L'API de rendu se justifie si
tu passes à une centaine de shorts par mois, ou si la chaîne doit tourner sur
un environnement où tu ne peux pas installer de binaire.

### Sans gérer les connexions aux plateformes : 149 € / mois et plus

Les agrégateurs remplacent les trois connecteurs par une seule API. Ils
portent leur propre validation Meta/TikTok, ce qui supprime l'App Review et
l'audit de ton côté — c'est leur vraie valeur.

| Service | Entrée de gamme | Remarque |
|---|---|---|
| **Upload-Post** | 149 $/mois (1 profil) | palier gratuit sans carte pour tester |
| **Ayrshare** | 149 $/mois (1 profil) | volumes élevés = supplément 300 $/mois |
| **Blotato** | abonnement forfaitaire | une clé, endpoint unique, serveur MCP |

**Pour un seul compte, ce n'est pas rentable** : 149 $/mois pour éviter deux
formulaires qu'on remplit une fois. L'arbitrage s'inverse si tu gères les
comptes de plusieurs clubs ou clients — là, l'agrégateur évite de multiplier
les App Reviews.

### Transcription hébergée : +0,50 € / mois

Si tu ne veux pas faire tourner Whisper en local :

| Service | Tarif | Note |
|---|---|---|
| **AssemblyAI** | à partir de 0,0025 $/min (~0,15 $/h) | le moins cher, horodatage au mot inclus |
| **OpenAI Whisper API** | 0,006 $/min (0,36 $/h) | traitement par lots uniquement |
| **Deepgram Nova-3** | 0,0043 $/min (~0,26 $/h) | rapide, bonne ponctuation |

Sur 80 minutes d'audio par mois : entre 0,20 € et 0,50 €. Le coût n'est pas le
critère — c'est le temps de mise en route et le fait de ne pas mobiliser ta
machine. Attention toutefois : les options supplémentaires (diarisation,
détection de sujets) multiplient le tarif affiché par deux à quatre.

---

## Ce que coûte vraiment la chaîne

Le budget monétaire est marginal. Les deux coûts réels sont ailleurs :

1. **Le temps de validation des plateformes** : 2 à 6 semaines pour Meta,
   1 à 3 pour TikTok. Rien ne les accélère, d'où le conseil de lancer les
   demandes le premier jour.
2. **Ton temps de relecture.** Compte 2 à 3 minutes par short pour visionner
   le rendu et corriger la légende. Sur 20 shorts, c'est une heure par mois —
   plus que tout le reste réuni. C'est aussi le poste sur lequel il ne faut
   pas économiser au début : c'est là que tu affines l'angle éditorial dans
   `config.yaml`, et un prompt bien calé fait gagner ce temps ensuite.
