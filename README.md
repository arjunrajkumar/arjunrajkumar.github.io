# Website

## AI reply

Quarto builds the home page and the transaction signature article.
GitHub Pages publishes the result at <https://arjunrajkumar.github.io/>.

The home page source is `pages/index.qmd`, a Quarto Markdown text file.
The article notebook is `notebooks/verifying-bitcoin-transaction-signature/index.ipynb`.
Its text comes from the existing article. It contains no new exercise code or results.
You can add Python cells in JupyterLab when you are ready.

Quarto uses the existing `styles.css` and article `style.css`.
The templates in `_quarto/home.html` and `_quarto/article.html` keep the existing layouts.
The first Bitcoin payment article and other pages are copied without changes so their links work.
The sources have separate folders because Quarto writes temporary HTML beside them.
`scripts/prepare_site.py` copies the generated pages to their existing URLs inside `_site/`.
Edit the source files, not the generated HTML. The earlier HTML versions remain in Git history.

## Open the preview

From this repository, activate the local Python environment:

```sh
source .venv/bin/activate
```

Start the preview:

```sh
quarto preview --host 127.0.0.1 --port 8765 --no-browser
```

Open <http://127.0.0.1:8765/> for the home page.
Open <http://127.0.0.1:8765/verifying-bitcoin-transaction-signature/> for the article.
Quarto updates the preview when you save either source file.
Press `Ctrl+C` in the terminal to stop it.

## Edit the sources

Edit `pages/index.qmd` in a text editor to change the home page.
You can also open it in JupyterLab with its text editor.

In another terminal, activate the same environment and start JupyterLab:

```sh
source .venv/bin/activate
jupyter lab notebooks/verifying-bitcoin-transaction-signature/index.ipynb
```

Double-click a text cell to edit it. Press `Shift+Enter` to show the formatted text.
Save the notebook to update the Quarto preview.

Run any Python cells in JupyterLab before saving. This trial uses saved outputs.
Quarto does not run notebook code during a local or published build (`execute.enabled: false`).

## Build without a server

```sh
quarto render
```

Generated pages go into `_site/`. Git ignores this folder and the local tools.

## Publish

Preview and check your changes locally. Commit the source files and push to `main`.
The `Publish Quarto site` workflow builds the site and publishes it to GitHub Pages.
It uses the same pinned Quarto version as the local preview.
Check the workflow result in the repository's Actions tab.

GitHub Pages uses the GitHub Actions publishing source.
The first Bitcoin payment article remains plain HTML, CSS, and JavaScript.
Quarto copies that article and its files without changes.

## Recreate the tools

The trial uses Python 3.13. From this repository:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-preview.txt
```

References: [Quarto with JupyterLab](https://quarto.org/docs/tools/jupyter-lab.html)
and [Quarto HTML settings](https://quarto.org/docs/output-formats/html-basics.html).
