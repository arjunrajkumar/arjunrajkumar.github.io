"""Give the generated pages their existing public URLs."""

import json
import re
from pathlib import Path
from shutil import copytree

import yaml

from learning_notes import article_notes

root = Path(__file__).resolve().parents[1]
site = root / "_site"
pages = {
    "pages/index.html": "index.html",
    "pages/why-bitcoin.html": "why-bitcoin/index.html",
    "notebooks/proving-knowledge-of-a-secret/index.html":
        "proving-knowledge-of-a-secret/index.html",
    "notebooks/elliptical-curves/index.html": "elliptical-curves/index.html",
    "notebooks/division-in-a-finite-field/index.html": "division-in-a-finite-field/index.html",
    "notebooks/finite-fields-in-cryptography/index.html": "finite-fields-in-cryptography/index.html",
    "notebooks/verifying-bitcoin-transaction-signature/index.html":
        "verifying-bitcoin-transaction-signature/index.html",
    "notebooks/deconstructing-a-payment-transaction/index.html":
        "deconstructing-a-payment-transaction/index.html",
}
for source, target in pages.items():
    rendered = site / source
    # A single-page build can run before the other page has been rendered.
    if not rendered.exists():
        continue
    destination = site / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    html = rendered.read_text()
    # Keep the original pages' standards mode after Quarto's HTML processing.
    if not html.lstrip().lower().startswith("<!doctype html>"):
        html = "<!doctype html>\n" + html
    destination.write_text(html)
    # Relative links to notebook figures must also work at the public URL.
    resources = rendered.with_name(rendered.stem + "_files")
    if resources.is_dir():
        copytree(resources, destination.parent / resources.name, dirs_exist_ok=True)

# Read only pages in the current render list. Old preview files can outlive a post.
targets = yaml.safe_load((root / "_quarto.yml").read_text())["project"]["render"]
notes = []
for target in targets:
    source = str(Path(target).with_suffix(".html"))
    public = pages.get(source, source)
    rendered = site / source
    if public != "index.html" and rendered.is_file():
        url = "/" + public.removesuffix("index.html")
        notes.extend(article_notes(rendered.read_text(), url))

# Keep dated exercise work from the chapter notebooks and archived workbook.
notes.extend(json.loads((root / "data" / "programmingbitcoin-history.json").read_text()))

# Existing bookmarks must still reach the chapter work.
book_url = "https://github.com/arjunrajkumar/programmingbitcoin/"
redirect = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Programming Bitcoin</title>
<meta http-equiv="refresh" content="0; url={book_url}">
<link rel="canonical" href="{book_url}">
</head>
<body><p><a href="{book_url}">Programming Bitcoin exercises on GitHub</a></p></body>
</html>
'''
for old_url in ("programmingbitcoin/index.html", "notebooks/programmingbitcoin/index.html"):
    destination = site / old_url
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(redirect)

assets = site / "assets"
assets.mkdir(exist_ok=True)
# Keep this file available for older cached chart scripts.
(assets / "proof-of-work.json").write_text(json.dumps(notes, ensure_ascii=False) + "\n")

# Escape HTML delimiters so a note cannot close the JSON script element.
history = json.dumps(notes, ensure_ascii=False, separators=(",", ":"))
for character, escaped in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e")):
    history = history.replace(character, escaped)
pattern = r'<script id="proof-history" type="application/json">.*?</script>'
for name in ("index.html", "pages/index.html"):
    homepage = site / name
    if not homepage.exists():
        continue
    html, count = re.subn(
        pattern,
        lambda _: f'<script id="proof-history" type="application/json">{history}</script>',
        homepage.read_text(),
        flags=re.S,
    )
    if count != 1:
        raise ValueError(f"Expected one learning-history element in {name}, found {count}")
    homepage.write_text(html)
