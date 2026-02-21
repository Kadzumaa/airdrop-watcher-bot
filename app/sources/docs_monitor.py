import asyncio, requests, re

async def check_docs_for_keywords(url: str, keywords: list[str]) -> list[str]:
    def _fetch():
        r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code != 200:
            return []
        text = r.text.lower()
        found=[]
        for k in keywords:
            if re.search(r"\b" + re.escape(k.lower()) + r"\b", text):
                found.append(k)
        return found
    try:
        return await asyncio.to_thread(_fetch)
    except Exception:
        return []
