import asyncio, requests

URL = "https://api.llama.fi/raises"

def _normalize_items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("raises", "data", "items", "results"):
            v = data.get(key)
            if isinstance(v, list):
                return v
        for v in data.values():
            if isinstance(v, list):
                return v
    return []

async def fetch_defillama_raises(limit: int = 50) -> list[dict]:
    def _fetch():
        r = requests.get(URL, timeout=30)
        r.raise_for_status()
        data = r.json()
        items = _normalize_items(data)
        out = []
        for item in items[:limit]:
            out.append({
                "name": (item.get("name") or "").strip(),
                "date": item.get("date", ""),
                "round": item.get("round", ""),
                "amount": item.get("amount", ""),
                "amount_usd": item.get("amountUsd") or item.get("amount_usd"),
                "lead": item.get("leadInvestors") or item.get("leadInvestor") or item.get("lead") or None,
                "investors": item.get("investors") or [],
                "url": item.get("url", ""),
            })
        return out
    try:
        return await asyncio.to_thread(_fetch)
    except Exception:
        return []
