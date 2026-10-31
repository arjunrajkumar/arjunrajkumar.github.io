# Website instructions

## Communication

- Use short, direct sentences and common words.
- Use ASD-STE100 Simplified Technical English for reports and status messages.
- Keep the author's supplied post text unchanged unless a change is approved.
- Ask before correcting spelling, grammar, or technical claims in supplied text.

## Start the notebook workspace

When Arjun says `start`, `start the notebook`, or asks to resume this workspace,
complete the setup yourself. The final state must be a working problem notebook
open in his browser, with JupyterLab, nbdime, and the Quarto preview ready.
Do not stop after giving commands. If he explicitly asks to do the steps himself,
guide him one step at a time instead.

### Find the project and preserve work

- This website repository is `arjunrajkumar/arjunrajkumar.github.io`.
  It is separate from the learning repository `arjunrajkumar/exploring-bitcoin`.
- Find the existing checkout by its Git remote. Do not assume an old computer's path.
  From the learning checkout, first check the sibling `arjunrajkumar.github.io` folder.
- If there is no checkout, clone `https://github.com/arjunrajkumar/arjunrajkumar.github.io.git`
  into the user's projects folder. Use a sibling folder when starting from the learning repository.
- Read this file and `README.md`. Check `git status` and fetch origin.
  Fast-forward only when the checkout is clean and only behind.
  Preserve local edits, branches, notebook outputs, and checkpoints.
- Use the notebook requested by the user. The current default is
  `notebooks/verifying-bitcoin-transaction-signature/index.ipynb`.
  Do not infer a different problem from another chat.

### Prepare a new computer

- Check that Git and Python 3.13 are available. Install missing prerequisites from
  their official sources or an existing trusted package manager.
  On a Mac with Homebrew, the Python command is `brew install python@3.13`.
  If Homebrew is absent, use the official Python installer or install Homebrew
  from its official instructions. Do not substitute a newer Python without checking compatibility.
- From the website repository, run:

  ```sh
  python3.13 scripts/start_workspace.py --no-browser
  ```

- The script creates `.venv` when needed and installs the pinned packages from
  `requirements-preview.txt`: Quarto, JupyterLab, nbdime, and process inspection support.
  Do not replace an existing environment or change system Python silently.
- For an existing setup, `.venv/bin/python scripts/start_workspace.py --no-browser`
  also works. Pass a repository-relative notebook path to open a different existing notebook.
- Setup does not require a Quarto or Jupyter account. GitHub login is needed only
  for repository operations that require authentication, such as pushing changes.

### Start the servers and open the notebook

- The script reuses servers for this checkout. Otherwise it starts JupyterLab on
  `127.0.0.1:8889` and the Quarto preview on `127.0.0.1:8765`.
  If another application uses a port, it chooses a free port and reports the actual URLs.
  Never stop another project's server to free a port.
- A confirmed Quarto preview that does not respond can be restarted. Do not stop
  Jupyter or its kernels without preserving the user's active work first.
- The script checks that the notebook exists and that nbdime works in the running server.
  If nbdime was installed after that server started, save the user's work, restart
  that Jupyter server, and run startup again. Do not disable authentication to avoid login.
- Read `.venv/workspace/state.json` for the actual notebook URL, preview URL, process
  IDs, and Jupyter runtime file. Logs remain under `.venv/workspace/`.
- Use the available browser tool to open the notebook in the user's browser.
  Handle the local Jupyter token login when needed. The runtime file contains the
  token; use it only for the matching local Jupyter server. Do not print it, commit
  it, paste it into chat, or put a token-bearing URL in the final response.
- Open the Quarto preview in another tab. Leave the notebook selected and ready to edit.
  Verify the notebook title, Python kernel, and `Notebook Git diff` button.
  Keep the notebook tab open after the task. Leave both server processes running.
- Do not run exercise cells, contact the Bitcoin node, change article text, or
  commit or publish content as part of `start`.
- Report the notebook and preview links without tokens. Report a real blocker if
  setup or browser access fails; do not claim that the notebook is open without checking it.

For manual use, omit `--no-browser`. The script opens an authenticated notebook
tab in the default browser. An agent should use `--no-browser` and the browser tool
so it can verify the final screen.

If the user requests a new problem notebook, preserve the existing notebooks.
Create only the requested structure and blank code cells; do not write exercise
solutions. Add its render target and public URL mapping when a blog preview is requested.

Setup references: [Python](https://www.python.org/downloads/),
[Homebrew Python 3.13](https://formulae.brew.sh/formula/python@3.13),
[Jupyter login](https://jupyter-server.readthedocs.io/en/latest/operators/security.html),
and [nbdime](https://nbdime.readthedocs.io/en/latest/extensions.html).

## Design references

- Read `styles.css`, `pages/index.qmd`, `_quarto/home.html`, and `first_bitcoin_payment/style.css` before changing the design.
- Use the homepage and `first_bitcoin_payment/` as the design references for new pages.
- Keep the same Open Sans font, white background, text colour, link colours, and simple layout.
- Reuse `styles.css` for shared typography and colours. Add page-specific CSS only where needed.
- Do not introduce a separate visual style for each new post.
- Use 16px body text with a 1.4 line height.
- Match article titles to the “Satoshi sends Hal Finney 10 bitcoins” heading: 1.15em, bold, line height 1.4, and zero margin.
- Use 1.15em bold section headings. Use 16px paragraph spacing, 0.5rem between list items, and 2rem between major sections.
- Use the homepage's 800px reading width for text posts. The first payment page is wider to display its data columns.
- Match the first payment page's top “Home” link: 14px, regular weight, and 24px below it.
- Leave 30px below an article header, or 24px on screens up to 700px wide.
- Use “Home”, not “Back to home”. Do not add article footers unless requested.
- Keep links underlined. On the homepage, link the topic words rather than the whole sentence.
- For the signature post, the homepage text is: Verifying a [Bitcoin transaction signature (Python)]. Include “(Python)” in the link.

## Signature verification post

- Keep the original wording, numbers, and technical claims unless a change is approved.
- Begin with the introductory text without a “Goal” heading. Then show My plan (without AI, before coding), Coding (with AI help), and What I learnt in full.
- Follow the homepage's plain text layout. Use grey backgrounds for the byte examples in What I learnt, with byte values before explanatory labels. Do not add other boxes, arrows, tabs, expandable sections, or a row of section links.
- Reuse the shared homepage heading and list rules in `styles.css`. Keep section headings in normal case at 1.15em and content at 16px.
- Use the same solid bullet markers and 0.5rem item spacing as the homepage for What I learnt. Keep the plan numbered to show its order.
- Keep paragraphs at the full reading width without extra panel padding.
- Disable automatic word hyphenation on text posts. Let the transaction ID wrap as needed, without cutting off text or adding horizontal scrolling.
- Do not add a work-in-progress label or rename the code link without approval.
- Update the homepage learning-time total only when Arjun gives a new value.

## Editing and publishing

- Edit the home page in `pages/index.qmd` and the signature article in `notebooks/verifying-bitcoin-transaction-signature/index.ipynb`.
- Quarto builds into `_site/`. Do not edit or commit generated HTML.
- The first Bitcoin payment article remains in `first_bitcoin_payment/` and is copied without changes.
- Pushes to `main` run `.github/workflows/publish.yml` to build and publish GitHub Pages.
- Use saved notebook outputs. Do not run learning code during publication.
- Check Git status before edits and preserve existing work.
- Keep drafts local while Arjun is reviewing them. Commit and publish when he asks.
- Check the page in the browser after changes. Check section order, visible text, and links.
- Check that long transaction IDs wrap without causing horizontal scrolling.
- Keep the original article text intact when moving sections or changing markup.
- Stage only the requested files. Do not commit credentials, previews, logs, or temporary files.
- Report whether changes are local, committed, or published.
