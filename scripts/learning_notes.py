"""Find dated explanations in a rendered article and link to their own words."""

from datetime import date
import re
from urllib.parse import quote

from bs4 import BeautifulSoup


DATED_HEADING = re.compile(r"(\d{4}-\d{2}-\d{2})\s+[—–-]\s+(.+)")
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def article_notes(html, url):
    article = BeautifulSoup(html, "html.parser").find("article")
    if article is None:
        return []

    headings = {id(h): h.get_text(" ", strip=True) for h in article.find_all(HEADINGS)}
    # Code, output, quotations, starter hints and bare links are not explanations.
    for tag in reversed(article.select("pre, code, .cell-output, blockquote, details, a, script, style, [hidden]")):
        tag.decompose()

    notes = []
    pending = None
    for tag in article.find_all([*HEADINGS, "p", "li"]):
        if tag.name in HEADINGS:
            match = DATED_HEADING.fullmatch(headings[id(tag)])
            pending = (*match.groups(), tag.get("id")) if match else None
            continue
        if not tag.get_text(strip=True):
            continue

        marker = tag.find("span", attrs={"data-learnt": True}, recursive=False)
        note = pending
        if marker:
            note = (marker["data-learnt"], marker.get("data-topic"), marker.get("id"))
        if note:
            day, topic, anchor = note
            if not topic or not anchor:
                raise ValueError(f"Incomplete learning note in {url}: {note}")
            date.fromisoformat(day)
            notes.append({"date": day, "topic": topic, "href": f"{url}#{quote(anchor)}"})
            pending = None
    return notes
