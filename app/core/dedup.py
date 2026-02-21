import hashlib

def make_dedup_key(*parts: str) -> str:
    raw = "|".join([p or "" for p in parts])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:48]
