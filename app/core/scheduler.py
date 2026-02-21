import json, os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import CHECK_INTERVAL_MINUTES, ENABLE_DEFILLAMA, ENABLE_COINGECKO, ENABLE_DROPSEARN, ENABLE_DOCS_MONITOR
from app.core.dedup import make_dedup_key
from app.core.scoring import score_signal_confidence, project_tier_score, is_top_investor
from app.data.db import SessionLocal
from app.data.models import Project, Signal

from app.sources.defillama import fetch_defillama_raises
from app.sources.dropsearn import fetch_dropsearn_tasks
from app.sources.coingecko import fetch_coingecko_market
from app.sources.docs_monitor import check_docs_for_keywords

KEYWORDS = ["airdrop","retrodrop","testnet","incentivized","points","rewards","snapshot","claim","eligibility"]

def _tier_letter(score: float) -> str:
    if score >= 4.3: return "A"
    if score >= 3.6: return "B"
    return "C"

async def _send(bot, chat_id: str, text: str):
    try:
        await bot.send_message(chat_id, text, parse_mode="Markdown", disable_web_page_preview=False)
    except Exception:
        await bot.send_message(chat_id, text)

async def poll_and_notify(bot):
    admin_chat_id = os.getenv("ADMIN_CHAT_ID","").strip()
    if not admin_chat_id:
        return

    # DropsEarn discovery
    if ENABLE_DROPSEARN:
        try:
            tasks = await fetch_dropsearn_tasks(limit=25)
            async with SessionLocal() as s:
                for t in tasks:
                    name = t["project"]
                    q = await s.execute(select(Project).where(Project.name == name))
                    p = q.scalar_one_or_none()
                    if p is None:
                        p = Project(name=name, status="watch", chain=t.get("chain",""), links_json=json.dumps(t.get("links",{})))
                        s.add(p)
                        await s.commit()

                    dedup = make_dedup_key(name, "dropsearn", t.get("url",""), t.get("task",""))
                    exists = (await s.execute(select(Signal).where(Signal.dedup_key == dedup))).scalar_one_or_none()
                    if exists:
                        continue

                    links = t.get("links", {}) or {}
                    payload = {"activity": {"what": t.get("task",""), "url": t.get("url","")}, "links": links}
                    confidence = score_signal_confidence(3.2)

                    tier_score = project_tier_score(
                        has_funding=False,
                        has_top_investor=False,
                        has_official_docs_signal=False,
                        has_github=bool(links.get("github")),
                        has_market_token=bool(links.get("coingecko_id")),
                    )

                    sig = Signal(
                        project_name=name,
                        signal_type="dropsearn",
                        title="Активность (DropsEarn)",
                        url=t.get("url",""),
                        evidence_json=json.dumps({**payload, "tier_score": tier_score}, ensure_ascii=False),
                        confidence=confidence,
                        dedup_key=dedup,
                    )
                    s.add(sig)
                    await s.commit()

                    if _tier_letter(tier_score) in ("A","B") and not p.muted:
                        from app.bot.formatter import format_signal_card_ru
                        text = format_signal_card_ru(
                            project_name=name,
                            chain=p.chain,
                            source="DropsEarn",
                            event_type="Найдена активность",
                            confidence=confidence,
                            payload=payload,
                            project_tier_score=tier_score,
                        )
                        await _send(bot, admin_chat_id, text)
        except Exception:
            pass

    # Load projects
    async with SessionLocal() as s:
        projects = (await s.execute(select(Project))).scalars().all()

    # Per-project checks
    for p in projects:
        if p.muted:
            continue
        links = json.loads(p.links_json or "{}")

        if ENABLE_DOCS_MONITOR and links.get("docs"):
            try:
                found = await check_docs_for_keywords(links["docs"], KEYWORDS)
                if found:
                    dedup = make_dedup_key(p.name, "docs", links["docs"], ",".join(sorted(found)))
                    async with SessionLocal() as s:
                        exists = (await s.execute(select(Signal).where(Signal.dedup_key == dedup))).scalar_one_or_none()
                        if not exists:
                            payload = {"official": {"found": found, "where": "Docs/Blog", "url": links["docs"]}, "links": links}
                            confidence = score_signal_confidence(3.6, [0.6, min(1.0, 0.2*len(set(found)))])
                            tier_score = project_tier_score(
                                has_funding=False,
                                has_top_investor=False,
                                has_official_docs_signal=True,
                                has_github=bool(links.get("github")),
                                has_market_token=bool(links.get("coingecko_id")),
                            )
                            sig = Signal(project_name=p.name, signal_type="docs",
                                         title="Официальные ключевые слова в docs", url=links["docs"],
                                         evidence_json=json.dumps({**payload, "tier_score": tier_score}, ensure_ascii=False),
                                         confidence=confidence, dedup_key=dedup)
                            s.add(sig)
                            await s.commit()

                            if _tier_letter(tier_score) in ("A","B"):
                                from app.bot.formatter import format_signal_card_ru
                                text = format_signal_card_ru(
                                    project_name=p.name,
                                    chain=p.chain,
                                    source="Официальные Docs",
                                    event_type="Ключевые слова в документации",
                                    confidence=confidence,
                                    payload=payload,
                                    project_tier_score=tier_score,
                                )
                                await _send(bot, admin_chat_id, text)
            except Exception:
                pass

        if ENABLE_COINGECKO and links.get("coingecko_id"):
            try:
                m = await fetch_coingecko_market(links["coingecko_id"])
                if m and m.get("change_24h_pct") is not None and abs(m["change_24h_pct"]) >= 15:
                    dedup = make_dedup_key(p.name, "market", str(int(m["change_24h_pct"])))
                    async with SessionLocal() as s:
                        exists = (await s.execute(select(Signal).where(Signal.dedup_key == dedup))).scalar_one_or_none()
                        if not exists:
                            payload = {"market": m, "links": links}
                            confidence = score_signal_confidence(3.0, [1.0])
                            tier_score = project_tier_score(
                                has_funding=False,
                                has_top_investor=False,
                                has_official_docs_signal=False,
                                has_github=bool(links.get("github")),
                                has_market_token=True,
                            )
                            sig = Signal(project_name=p.name, signal_type="market",
                                         title=f"Движение рынка {m['change_24h']}", url=links.get("website",""),
                                         evidence_json=json.dumps({**payload, "tier_score": tier_score}, ensure_ascii=False),
                                         confidence=confidence, dedup_key=dedup)
                            s.add(sig)
                            await s.commit()

                            if _tier_letter(tier_score) in ("A","B"):
                                from app.bot.formatter import format_signal_card_ru
                                text = format_signal_card_ru(
                                    project_name=p.name,
                                    chain=p.chain,
                                    source="CoinGecko",
                                    event_type="Сильное движение рынка (24ч)",
                                    confidence=confidence,
                                    payload=payload,
                                    project_tier_score=tier_score,
                                )
                                await _send(bot, admin_chat_id, text)
            except Exception:
                pass

    # DefiLlama funding
    if ENABLE_DEFILLAMA:
        try:
            raises = await fetch_defillama_raises(limit=30)
        except Exception:
            raises = []

        if raises:
            async with SessionLocal() as s:
                for r in raises:
                    name = (r.get("name") or "").strip()
                    if not name:
                        continue
                    q = await s.execute(select(Project).where(Project.name == name))
                    p = q.scalar_one_or_none()
                    if not p or p.muted:
                        continue

                    inv = r.get("investors") or []
                    has_top = any(is_top_investor(x) for x in inv)

                    dedup = make_dedup_key(name, "funding", r.get("date",""), str(r.get("amount","")), ",".join(inv))
                    exists = (await s.execute(select(Signal).where(Signal.dedup_key == dedup))).scalar_one_or_none()
                    if exists:
                        continue

                    payload = {
                        "funding": {"round": r.get("round",""), "amount": r.get("amount",""), "fdv": None, "investors": inv},
                        "links": json.loads(p.links_json or "{}")
                    }

                    confidence = score_signal_confidence(3.4, [0.6 if has_top else 0.2])
                    tier_score = project_tier_score(
                        has_funding=True,
                        has_top_investor=has_top,
                        has_official_docs_signal=False,
                        has_github=bool(payload["links"].get("github")),
                        has_market_token=bool(payload["links"].get("coingecko_id")),
                    )

                    sig = Signal(project_name=name, signal_type="funding",
                                 title="Инвестиционный раунд", url=r.get("url",""),
                                 evidence_json=json.dumps({**payload, "tier_score": tier_score}, ensure_ascii=False),
                                 confidence=confidence, dedup_key=dedup)
                    s.add(sig)
                    await s.commit()

                    if _tier_letter(tier_score) in ("A","B"):
                        from app.bot.formatter import format_signal_card_ru
                        text = format_signal_card_ru(
                            project_name=name,
                            chain=p.chain,
                            source="DefiLlama",
                            event_type="Найден инвестиционный раунд",
                            confidence=confidence,
                            payload=payload,
                            project_tier_score=tier_score,
                        )
                        await _send(bot, admin_chat_id, text)

async def start_scheduler(bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(poll_and_notify, "interval", minutes=CHECK_INTERVAL_MINUTES, args=[bot], max_instances=1, coalesce=True)
    scheduler.start()
