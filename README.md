# Website

Quarto builds the home page and the transaction signature article.
GitHub Pages publishes the result at <https://arjunrajkumar.github.io/>.

The home page source is `pages/index.qmd`, a Quarto Markdown text file.
The article notebook is `notebooks/verifying-bitcoin-transaction-signature/index.ipynb`.
Its text comes from the existing article. It contains no new exercise code or results.
You can add Python cells in JupyterLab when you are ready.

Quarto uses the existing `styles.css` and article `style.css`.
The templates in `_quarto/home.html` and `_quarto/article.html` keep the existing layouts.
The first Bitcoin payment article and its files are copied without changes.
The sources have separate folders because Quarto writes temporary HTML beside them.
`scripts/prepare_site.py` copies the generated pages to their existing URLs inside `_site/`.
Edit the source files, not the generated HTML. The earlier HTML versions remain in Git history.

## Proof of work

In a published post or notebook, use a heading such as
`### 2026-11-03 — Finite fields`. Use the date in India. Under the heading,
write your explanation in a paragraph or a list. A heading on its own stays empty.
You can add another dated heading for a different topic on the same day.
Each day has one bar. Each topic links to the passage on the blog. Older Programming Bitcoin exercise entries link to the GitHub repository.

The chart reads the published articles each time the site builds. Programming Bitcoin exercise entries are kept in `data/programmingbitcoin-history.json`. Older passages
have invisible date and topic labels beside the original words. Removing the
passage removes its entry. The chart opens on the current calendar month, using the date in India. The small arrows select earlier months, back to the first recorded work, or return to the current month. Each view shows the whole month. All bars have the same height. Orange marks written work. Very light grey marks days with no written work, up to today. Dates before the first recorded work and future days stay empty. The bars do not show hours spent.

The build includes the history in the home page. The browser makes no extra history request. Switching months uses that same data. The page reserves space for the chart before its script runs.

## Start everything

In a new chat, say `start`. The workflow in `AGENTS.md` sets up the tools,
starts or reuses both local servers, and opens the problem notebook.

To do this yourself, run the following from the website repository:

```sh
python3.13 scripts/start_workspace.py
```

This also works on a new computer once Git, Python 3.13, and this Git clone are present.
The script creates the local environment and installs missing tools.
It opens JupyterLab with its login token handled and checks that nbdime is available.
On checkouts with publish on save enabled, it reconnects the publisher and retries queued saves.

The default notebook is the transaction signature article. To choose another notebook,
pass its path after the script name. The actual server URLs and process IDs are recorded
in `.venv/workspace/state.json`. Logs are stored in the same ignored folder.

Jupyter and Quarto run in the background. Closing a browser tab does not stop them.
To stop Jupyter, save your work and use `.venv/bin/jupyter server stop 8889`,
using the actual port from the state file if it differs. Stop the recorded Quarto
preview process when you no longer need the preview.

In JupyterLab, click **Notebook Git diff** to compare the notebook with the last Git commit.

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

Startup installs `jupyterlab-spellchecker`. While you edit a text cell, it marks spelling errors. Right-click a marked word to choose a correction. It also checks Python comments. It does not change your words automatically. The dictionaries are local. Use **Settings → Settings Editor → Spellchecker** to change the language or mark style. If the extension was installed while Jupyter was running, save your work and restart Jupyter once. Reload the notebook tab after the restart.

Run any Python cells in JupyterLab before saving. The build uses saved outputs.
Quarto does not run notebook code during a local or published build (`execute.enabled: false`).

## Build without a server

```sh
quarto render
```

Generated pages go into `_site/`. Git ignores this folder and the local tools.

## Publish

To enable publishing from Jupyter on a new checkout, run this once:

```sh
python3.13 scripts/start_workspace.py --publish-on-save --no-browser
```

Open a published post in JupyterLab. Edit it and press **Cmd + S**. Jupyter autosaves
also count. The workspace listens for successful saves and commits the changed notebook
on `main`. It pushes that commit to GitHub. The site builds from the saved outputs.
Future workspace starts reconnect the publisher automatically.

This applies to tracked `notebooks/<post>/index.ipynb` files listed in the committed
`project.render` section of `_quarto.yml`. A new post needs its notebook, render entry,
URL mapping, and homepage link committed and pushed together once.
The playground and homepage use the manual Git workflow.

For Programming Bitcoin, work in each chapter's own notebook. For Chapter 2, run:

```sh
python3.13 scripts/start_workspace.py notebooks/programmingbitcoin/book/code-ch02/Chapter2.ipynb
```

Choose the chapter folder and notebook that you need. Startup checks both repositories
for updates and enables publishing on this laptop. Jupyter saves for Python files and
chapter notebooks update [Arjun's fork](https://github.com/arjunrajkumar/programmingbitcoin/).
Each chapter notebook has its own Python session. Do not combine chapter imports in one notebook.

The former combined notebook is saved as `notebooks/programmingbitcoin/archive.ipynb`.
It is no longer published. Its saved work is also in Git history. The old public URL
forwards to GitHub. Older startup commands that name the combined index open Chapter 1.

To pause automatic publication, run `touch .venv/workspace/pause-publishing`.
To resume, run `rm .venv/workspace/pause-publishing` and save the post again.
Use the publisher log under `.venv/workspace/publish-<Jupyter port>.log` to check a save.
Changed saves wait locally if GitHub is unavailable. If local and remote branches differ,
review `git status` and reconcile them. The helper retries the queued save.

The `Publish Quarto site` workflow builds the site and publishes it to GitHub Pages.
It uses the same pinned Quarto version as the local preview.
Check the workflow result in the repository's Actions tab.

GitHub Pages uses the GitHub Actions publishing source.
The first Bitcoin payment article remains plain HTML, CSS, and JavaScript.
Quarto copies that article and its files without changes.

## Recreate the tools

The tools use Python 3.13. From this repository:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-preview.txt
```

References: [Quarto with JupyterLab](https://quarto.org/docs/tools/jupyter-lab.html)
and [Quarto HTML settings](https://quarto.org/docs/output-formats/html-basics.html).
