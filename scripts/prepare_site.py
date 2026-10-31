"""Give the generated pages their existing public URLs."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
site = root / "_site"
pages = {
    "pages/index.html": "index.html",
    "notebooks/verifying-bitcoin-transaction-signature/index.html":
        "verifying-bitcoin-transaction-signature/index.html",
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
