import asyncio, requests

async def fetch_github_activity(repo: str) -> dict | None:
    # repo like "org/name"
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    def _fetch():
        r = requests.get(url, timeout=30, headers={"Accept":"application/vnd.github+json"})
        if r.status_code != 200:
            return None
        j = r.json()
        return {"tag": j.get("tag_name"), "name": j.get("name"), "url": j.get("html_url")}
    return await asyncio.to_thread(_fetch)
