import re
from dataclasses import dataclass, field

from core.scanner import FileInfo


@dataclass
class SearchResult:
    file: FileInfo
    score: int
    matched: list = field(default_factory=list)
    snippet: str = ""
    page: int | None = None
    relevance: float | None = None  # 0–1 similarity from semantic search


def _variants(keyword):
    """'cyber security' also matches 'cybersecurity' and 'cyber-security'."""
    k = keyword.lower().strip()
    return {k, k.replace(" ", ""), k.replace(" ", "-")}


def _snippet_and_page(text, position):
    """Return ~150 characters around a match and the PDF page it's on."""
    start = max(0, position - 70)
    snippet = re.sub(r"\s+", " ", text[start:position + 80]).strip()
    pages = re.findall(r"--- Page (\d+) ---", text[:position])
    page = int(pages[-1]) if pages else None
    return snippet, page


def search_files(files, file_types, keywords):
    """Filter files by type and rank them by keyword matches."""
    wanted_types = {t.lower().lstrip(".") for t in file_types}
    results = []

    for f in files:
        if wanted_types and f.extension not in wanted_types:
            continue

        name = f.name.lower()
        text = f.text.lower()
        score = 0
        matched = []
        snippet, page = "", None

        for keyword in keywords:
            variants = _variants(keyword)
            in_name = any(v in name for v in variants)
            content_hits = sum(text.count(v) for v in variants)

            if in_name or content_hits:
                matched.append(keyword)
                score += (10 if in_name else 0) + min(content_hits, 20)

                if not snippet and content_hits:
                    position = min(text.find(v) for v in variants if v in text)
                    snippet, page = _snippet_and_page(f.text, position)

        if not keywords:
            score = 1  # no keywords: file type alone decides

        if score > 0:
            results.append(SearchResult(f, score, matched, snippet, page))

    return sorted(results, key=lambda r: r.score, reverse=True)