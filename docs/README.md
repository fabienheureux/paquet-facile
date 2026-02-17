# Documentation sites-conformes

Documentation officielle de sites-conformes en français, construite avec Sphinx et le thème Wagtail.

## Build local

```bash
cd docs
pip install -r requirements.txt
make html
open _build/html/index.html  # Mac
```

## Structure

- `guide/` - Guides d'utilisation
- `tutoriels/` - Tutoriels pas à pas
- `reference/` - Documentation technique de référence
- `developpement/` - Documentation pour les contributeurs

## Publication

La documentation est automatiquement publiée sur GitHub Pages lors d'un push sur `main`.

## Technologies

- [Sphinx](https://www.sphinx-doc.org/)
- [sphinx-wagtail-theme](https://github.com/wagtail/sphinx-wagtail-theme)
- [MyST Parser](https://myst-parser.readthedocs.io/) - Support Markdown
