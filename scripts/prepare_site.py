"""Give the generated pages their existing public URLs."""

import json
from pathlib import Path

import yaml

from learning_notes import article_notes

root = Path(__file__).resolve().parents[1]
site = root / "_site"
pages = {
    "pages/index.html": "index.html",
    "notebooks/programmingbitcoin/index.html": "programmingbitcoin/index.html",
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

assets = site / "assets"
assets.mkdir(exist_ok=True)
(assets / "proof-of-work.json").write_text(json.dumps(notes, ensure_ascii=False) + "\n")
