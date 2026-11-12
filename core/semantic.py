"""Semantic search: find documents by meaning, not just matching words.

Each document is split into small chunks. Every chunk is turned into a vector
(a list of 768 numbers) by the local embedding model. Chunks about similar
topics get similar vectors, so a question can be matched to the closest chunks
even if it uses different words.
"""
import re

import numpy as np
import ollama

from core.db import connect
from core.search import SearchResult, search_files

EMBED_MODEL = "nomic-embed-text"
CHUNK_WORDS = 150     # about one paragraph
OVERLAP_WORDS = 30    # so a sentence cut in half still appears whole in one chunk
MIN_SCORE = 0.55      # below this a match is usually unrelated


def split_into_chunks(text, chunk_words=CHUNK_WORDS, overlap=OVERLAP_WORDS):
    """Split text into overlapping chunks. Returns a list of (page, chunk_text)."""
    parts = re.split(r"\n--- Page (\d+) ---\n", text)
    if len(parts) == 1:
        pages = [(None, parts[0])]
    else:
        # parts = [before, "1", page1_text, "2", page2_text, ...]
        pages = [(None, parts[0])] + [
            (int(parts[i]), parts[i + 1]) for i in range(1, len(parts) - 1, 2)
        ]

    chunks = []
    step = max(1, chunk_words - overlap)
    for page, page_text in pages:
        words = page_text.split()
        for start in range(0, len(words), step):
            piece = " ".join(words[start:start + chunk_words])
            if len(piece) >= 20:
                chunks.append((page, piece))
            if start + chunk_words >= len(words):
                break
    return chunks


def _embed(texts):
    """Turn texts into normalized vectors (so a dot product = cosine similarity)."""
    response = ollama.embed(model=EMBED_MODEL, input=texts)
    vectors = np.asarray(response.embeddings, dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.maximum(norms, 1e-12)


def ensure_embeddings(files, progress=None, batch_size=32):
    """Create vectors for documents that don't have them yet. Returns how many were added."""
    with connect() as conn:
        done = {r[0] for r in conn.execute("SELECT DISTINCT text_hash FROM chunks")}

    todo = {}
    for f in files:
        if f.text.strip() and f.text_hash and f.text_hash not in done:
            todo.setdefault(f.text_hash, f)  # identical files are embedded once

    for i, (digest, f) in enumerate(todo.items(), start=1):
        if progress:
            progress(i / len(todo), f.name)
        chunks = split_into_chunks(f.text)
        if not chunks:
            continue
        rows = []
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            # nomic-embed-text expects this prefix on documents
            vectors = _embed([f"search_document: {text}" for _, text in batch])
            for (page, text), vector in zip(batch, vectors):
                rows.append((digest, len(rows), page, text, vector.tobytes()))
        with connect() as conn:
            conn.executemany(
                "INSERT INTO chunks (text_hash, chunk_no, page, text, embedding) VALUES (?, ?, ?, ?, ?)",
                rows,
            )
    return len(todo)


def top_chunks(files, query, limit=None, file_types=()):
    """Score every chunk of the given files against the query, best first.
    Returns dicts with: file, page, text, score."""
    wanted = {t.lower().lstrip(".") for t in file_types}
    by_hash = {}
    for f in files:
        if f.text_hash and (not wanted or f.extension in wanted):
            by_hash.setdefault(f.text_hash, []).append(f)
    if not by_hash:
        return []

    hashes = list(by_hash)
    rows = []
    with connect() as conn:
        for start in range(0, len(hashes), 500):  # SQLite limits the number of ? per query
            group = hashes[start:start + 500]
            rows += conn.execute(
                f"SELECT text_hash, page, text, embedding FROM chunks "
                f"WHERE text_hash IN ({','.join('?' * len(group))})",
                group,
            ).fetchall()
    if not rows:
        return []

    matrix = np.vstack([np.frombuffer(r["embedding"], dtype=np.float32) for r in rows])
    question = _embed([f"search_query: {query}"])[0]
    scores = matrix @ question

    order = np.argsort(-scores)
    if limit:
        order = order[:limit]
    return [
        {
            "file": by_hash[rows[i]["text_hash"]][0],
            "page": rows[i]["page"],
            "text": rows[i]["text"],
            "score": float(scores[i]),
        }
        for i in order
    ]


def semantic_search(files, query, file_types=(), limit=15):
    """Best-matching files by meaning. One result per file (its best chunk)."""
    best = {}
    for c in top_chunks(files, query, file_types=file_types):
        if c["score"] < MIN_SCORE:
            break
        key = c["file"].text_hash
        if key not in best:
            best[key] = c
        if len(best) >= limit:
            break

    results = []
    for c in best.values():
        # Identical copies of a document share vectors; report every copy
        for f in files:
            if f.text_hash == c["file"].text_hash and (
                not file_types or f.extension in {t.lower() for t in file_types}
            ):
                results.append(SearchResult(
                    file=f, score=0, snippet=c["text"][:220], page=c["page"],
                    relevance=c["score"],
                ))
    return results


def hybrid_search(files, file_types, keywords, use_semantic=True):
    """Combine keyword matches and meaning-based matches into one ranked list."""
    keyword_results = {str(r.file.path): r for r in search_files(files, file_types, keywords)}
    if not use_semantic or not keywords:
        return list(keyword_results.values())

    merged = {}
    for r in semantic_search(files, " ".join(keywords), file_types):
        merged[str(r.file.path)] = r

    for key, kr in keyword_results.items():
        if key in merged:
            merged[key].matched = kr.matched
            if kr.snippet:
                merged[key].snippet, merged[key].page = kr.snippet, kr.page
        else:
            kr.relevance = None
            merged[key] = kr

    def rank(r):
        semantic = r.relevance or 0
        keyword_bonus = 0.25 if r.matched else 0
        return semantic + keyword_bonus + min(r.score, 30) / 300

    return sorted(merged.values(), key=rank, reverse=True)


def is_embed_model_available():
    try:
        return any(m.model.startswith(EMBED_MODEL) for m in ollama.list().models)
    except Exception:
        return False
