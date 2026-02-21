from __future__ import annotations

def _bar(value: float, maxv: float = 5.0, blocks: int = 5) -> str:
    v = max(0.0, min(maxv, float(value)))
    filled = int(round((v / maxv) * blocks))
    return "🟩" * filled + "⬜" * (blocks - filled)

def tier_from_score(project_tier_score: float) -> tuple[str, str]:
    if project_tier_score >= 4.3:
        return ("A", "🟢")
    if project_tier_score >= 3.6:
        return ("B", "🟡")
    return ("C", "⚪")

def format_signal_card_ru(
    project_name: str,
    chain: str,
    source: str,
    event_type: str,
    confidence: float,
    payload: dict,
    project_tier_score: float,
    cached_since: str | None = None,
    last_change: str | None = None,
) -> str:
    tier_letter, tier_emoji = tier_from_score(project_tier_score)

    lines: list[str] = []
    title = f"🟢 СИГНАЛ: {project_name}" + (f" ({chain})" if chain else "")
    lines.append(title)
    lines.append(f"**Класс проекта:** {tier_letter} {tier_emoji}")
    lines.append(f"**Уверенность сигнала:** {_bar(confidence)} {confidence:.1f}/5")
    lines.append(f"**Источник:** {source}")
    lines.append(f"**Тип события:** {event_type}")
    lines.append("")

    if payload.get("activity"):
        a = payload["activity"]
        lines.append("**🧩 Активность**")
        if a.get("what"):
            lines.append(f"**Что сделать:** {a.get('what')}")
        if a.get("url"):
            lines.append(f"**Ссылка:** {a.get('url')}")
        lines.append("")

    if payload.get("funding"):
        f = payload["funding"]
        lines.append("**💰 Инвестиции и фонды**")
        if f.get("round"):
            lines.append(f"**Раунд:** {f.get('round')}")
        if f.get("amount"):
            lines.append(f"**Сумма:** {f.get('amount')}")
        if f.get("fdv"):
            lines.append(f"**Оценка / FDV:** {f.get('fdv')}")
        inv = f.get("investors") or []
        if inv:
            lines.append(f"**Фонды:** {', '.join(inv[:12])}")
        lines.append("")

    if payload.get("market"):
        m = payload["market"]
        lines.append("**📊 Рыночные данные**")
        if m.get("market_cap") is not None:
            lines.append(f"**Капитализация:** {m.get('market_cap')}")
        if m.get("fdv") is not None:
            lines.append(f"**FDV:** {m.get('fdv')}")
        if m.get("volume_24h") is not None:
            lines.append(f"**Объём 24ч:** {m.get('volume_24h')}")
        if m.get("change_24h") is not None:
            lines.append(f"**Δ за 24ч:** {m.get('change_24h')}")
        if m.get("price") is not None:
            lines.append(f"**Цена:** {m.get('price')}")
        lines.append("")

    if payload.get("official"):
        o = payload["official"]
        lines.append("**📄 Официальные признаки ретродропа**")
        if o.get("found"):
            lines.append(f"**Найдено:** {', '.join(o.get('found'))}")
        if o.get("where"):
            lines.append(f"**Источник:** {o.get('where')}")
        if o.get("url"):
            lines.append(f"**Ссылка:** {o.get('url')}")
        lines.append("")

    links = payload.get("links", {}) or {}
    link_parts = []
    mapping = [
        ("website", "🌐", "Сайт"),
        ("docs", "📘", "Docs"),
        ("x", "🐦", "X"),
        ("discord", "💬", "Discord"),
        ("github", "💻", "GitHub"),
    ]
    for k, emoji, label in mapping:
        if links.get(k):
            link_parts.append(f"{emoji} {label}: {links[k]}")
    if link_parts:
        lines.append("**🔗 Ссылки проекта**")
        lines.extend(link_parts)
        lines.append("")

    if cached_since or last_change:
        if cached_since:
            lines.append(f"**📌 В кэше:** {cached_since}")
        if last_change:
            lines.append(f"**🕒 Последнее изменение:** {last_change}")

    return "\n".join(lines).strip()

def format_update_card_ru(
    project_name: str,
    change_title: str,
    before_after: str,
    source: str,
    url: str | None = None,
) -> str:
    lines = [
        f"🟡 ОБНОВЛЕНИЕ: {project_name}",
        f"**Что изменилось:** {change_title}",
        "",
        f"**Было → Стало:**\n{before_after}",
        "",
        f"**Источник:** {source}",
    ]
    if url:
        lines.append(f"**Ссылка:** {url}")
    return "\n".join(lines).strip()
