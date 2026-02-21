import asyncio, requests

async def fetch_coingecko_market(coingecko_id: str) -> dict | None:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency":"usd", "ids": coingecko_id}
    def _fetch():
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            return None
        arr = r.json()
        if not arr:
            return None
        x = arr[0]
        return {
            "price": x.get("current_price"),
            "market_cap": x.get("market_cap"),
            "fdv": x.get("fully_diluted_valuation"),
            "volume_24h": x.get("total_volume"),
            "change_24h_pct": x.get("price_change_percentage_24h"),
            "change_24h": f"{x.get('price_change_percentage_24h'):.2f}%" if x.get("price_change_percentage_24h") is not None else None,
        }
    return await asyncio.to_thread(_fetch)
