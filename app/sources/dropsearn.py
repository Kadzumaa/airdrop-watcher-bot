import asyncio, requests
from bs4 import BeautifulSoup

BASE = "https://dropsearn.com"

async def fetch_dropsearn_tasks(limit: int=30) -> list[dict]:
    # Free-first but scraping is brittle; we keep it light and cached by scheduler interval.
    def _fetch():
        r = requests.get(BASE, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tasks=[]
        # Heuristic: pick first N cards/rows with links
        # If site changes layout, we still won't crash—just return empty.
        for a in soup.select("a[href]"):
            href = a.get("href","")
            text = " ".join(a.get_text(" ", strip=True).split())
            if not href or not text:
                continue
            if "http" not in href:
                if href.startswith("/"):
                    url = BASE + href
                else:
                    url = BASE + "/" + href
            else:
                url = href
            # very rough filter to avoid nav links
            if len(text) < 6:
                continue
            if "login" in href or "privacy" in href or "terms" in href:
                continue
            # Create pseudo-project name from leading words (v1)
            project = text.split("—")[0].split("|")[0].strip()
            if len(project) < 3 or len(project) > 40:
                continue
            task = text[:140]
            tasks.append({
                "project": project,
                "task": task,
                "url": url,
                "chain": "",
                "links": {"website": "", "docs": "", "x": "", "discord": "", "github": ""}
            })
            if len(tasks) >= limit:
                break
        # Deduplicate by (project, url)
        seen=set()
        out=[]
        for t in tasks:
            k=(t["project"], t["url"])
            if k in seen:
                continue
            seen.add(k)
            out.append(t)
        return out
    try:
        return await asyncio.to_thread(_fetch)
    except Exception:
        return []
