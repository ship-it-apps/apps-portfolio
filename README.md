# apps-portfolio

Site vitrine de SHIP IT servi par GitHub Pages sur https://apps.shipit.group.

## ⚠️ URL figées — ne jamais renommer, déplacer, rediriger ni supprimer

Ces fichiers sont appelés en dur par les apps iOS et les fiches App Store :

| Fichier | Pourquoi |
|---|---|
| `<app>/support.html` | Lien Support dans les apps et l’App Store |
| `<app>/legal/index.html`, `privacy.html`, `terms.html` | CGU et confidentialité embarquées (paramètre `?lang=xx` géré par le script de la page) |
| `css/style.css` | Feuille de style des pages support et légales |
| `assets/icons/*.png` | Icônes utilisées par ces pages |
| `ik/bareme.json` | Barème kilométrique lu par l’app IK |
| `CNAME`, `.nojekyll` | Domaine et désactivation de Jekyll |

`<app>` = `zen24`, `scalequest`, `mijo`, `ik`, `pip`, `first`. Riffo (ex Guitar Scale Quest, toujours sous `scalequest`) référence aussi
`https://ship-it-apps.github.io/apps-portfolio/scalequest/legal/{terms,privacy}.html` : le site doit rester
sur GitHub Pages, dans ce dépôt.

Le build refuse d’écrire dans ces chemins. Avant chaque mise en ligne :

```bash
python3 _build/check_frozen.py          # aucun fichier figé modifié par rapport à main
python3 _build/check_frozen.py --live   # après déploiement : chaque URL figée répond 200
```

## Pages générées

Tout le reste (accueil, pages app, blogs, articles, sitemap, flux RSS) est généré par `_build/build.py` à partir de :

- `_build/content_apps.py` — textes des pages app (EN/FR), couleurs, captures, liens App Store ;
- `_build/content_posts.py` — articles de blog (une entrée par langue, reliées par `key`).

```bash
python3 _build/build.py            # régénère le site (Pillow facultatif, pour les images de partage)
python3 _build/build.py --strict   # échoue s’il reste des TODO (à utiliser avant publication)
```

### Langues

- Anglais = langue par défaut, aux URL historiques (`/`, `/zen24/`, `/zen24/blog/…`).
- Français sous `/fr/` (`/fr/`, `/fr/zen24/`, `/fr/zen24/blog/…`). IK n’existe qu’en français, à `/ik/`.
- Au premier passage, le site affiche la langue du navigateur si elle existe, sinon l’anglais.
  Le choix via le sélecteur EN/FR (ou `?lang=fr`) est mémorisé. Les robots ne sont jamais redirigés.
- Chaque page déclare ses traductions (hreflang + x-default) et le sitemap les reprend.

Ajouter une langue : l’ajouter à `LANGS` dans `build.py` (et à la liste `S` du script de langue),
puis ajouter les blocs `i18n[<langue>]` des apps et les articles traduits.

### Ajouter un article

Ajouter un `dict` dans `POSTS` (`content_posts.py`), régénérer, vérifier, committer.
