"""Web fallback: pulls clean text from trusted study sites when the PDF can't answer."""

import re
from urllib.parse import urlparse

from langchain_core.documents import Document

ALLOWED_SITES = [
    "geeksforgeeks.org",
    "javatpoint.com",
    "tutorialspoint.com",
    "programiz.com",
    "wikipedia.org",
    "w3schools.com",
    "scaler.com",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def _ddgs_search(query, max_results=4):
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
    site_filter = " OR ".join(f"site:{s}" for s in ALLOWED_SITES)
    full = f"{query} ({site_filter})"
    with DDGS() as ddgs:
        return list(ddgs.text(full, max_results=max_results))


def _fetch_text(url, max_chars=4500):
    import requests
    from bs4 import BeautifulSoup

    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": USER_AGENT})
        if r.status_code != 200 or not r.text:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
            tag.decompose()
        main = soup.find("article") or soup.find("main") or soup.body or soup
        text = main.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text[:max_chars]
    except Exception as e:
        print(f"[web_search] fetch failed for {url}: {e}")
        return ""


def web_search_docs(query, max_results=3):
    try:
        results = _ddgs_search(query, max_results=max_results + 2)
    except Exception as e:
        print(f"[web_search] search failed: {e}")
        return []

    docs = []
    for r in results:
        url = r.get("href") or r.get("url") or ""
        if not url:
            continue
        host = urlparse(url).netloc.lower()
        if not any(site in host for site in ALLOWED_SITES):
            continue
        title = r.get("title") or host
        snippet = r.get("body") or ""
        body = _fetch_text(url) or snippet
        if len(body) < 200:
            continue
        docs.append(
            Document(
                page_content=f"{title}\n\n{body}",
                metadata={"source": url, "page": "web", "title": title, "host": host},
            )
        )
        if len(docs) >= max_results:
            break
    return docs
