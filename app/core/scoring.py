from __future__ import annotations

def clamp(x: float, lo: float = 0.0, hi: float = 5.0) -> float:
    return max(lo, min(hi, float(x)))

def score_signal_confidence(base: float, bonuses: list[float] | None = None) -> float:
    s = float(base)
    for b in (bonuses or []):
        s += float(b)
    return clamp(s)

def project_tier_score(
    has_funding: bool,
    has_top_investor: bool,
    has_official_docs_signal: bool,
    has_github: bool,
    has_market_token: bool,
) -> float:
    s = 2.8
    if has_funding:
        s += 0.6
    if has_top_investor:
        s += 0.6
    if has_official_docs_signal:
        s += 0.8
    if has_github:
        s += 0.3
    if has_market_token:
        s += 0.2
    return clamp(s)

def is_top_investor(name: str) -> bool:
    if not name:
        return False
    n = name.lower()
    tops = [
        "a16z","andreessen","paradigm","sequoia","polychain","binance labs",
        "coinbase ventures","pantera","dragonfly","multicoin","jump","lightspeed",
        "framework","galaxy","delphi","electric capital"
    ]
    return any(t in n for t in tops)
