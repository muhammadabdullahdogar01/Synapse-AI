import hashlib
from collections import defaultdict


def file_hash(path, chunk_size=1024 * 1024):
    """SHA-256 fingerprint of a file's contents (read in 1 MB chunks)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(files):
    """Return groups of files with identical content (oldest file first)."""
    # Files with different sizes can't be identical, so only hash same-size files
    by_size = defaultdict(list)
    for f in files:
        try:
            by_size[f.path.stat().st_size].append(f)
        except OSError:
            continue

    groups = []
    for size, same_size in by_size.items():
        if len(same_size) < 2 or size == 0:
            continue
        by_hash = defaultdict(list)
        for f in same_size:
            try:
                by_hash[file_hash(f.path)].append(f)
            except OSError:
                continue
        for group in by_hash.values():
            if len(group) > 1:
                groups.append(sorted(group, key=lambda f: f.modified))

    # Biggest wasted space first
    return sorted(groups, key=lambda g: g[0].size_kb * (len(g) - 1), reverse=True)