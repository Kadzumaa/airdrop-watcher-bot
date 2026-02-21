import json
import logging
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import select, desc

from app.core.config import ADMIN_CHAT_ID
from app.data.db import SessionLocal
from app.data.models import Project, Signal
from app.bot.formatter import format_signal_card_ru
from app.bot.keyboards import project_actions_kb

router = Router()
logging.basicConfig(level=logging.INFO)

def _is_allowed_chat_id(chat_id: int) -> bool:
    if not ADMIN_CHAT_ID:
        return True
    return str(chat_id) == str(ADMIN_CHAT_ID)

def _is_allowed(msg: types.Message) -> bool:
    return _is_allowed_chat_id(msg.chat.id)

@router.message(Command("start"))
async def cmd_start(msg: types.Message):
    logging.info(f"USER CHAT ID: {msg.chat.id}")
    if not _is_allowed(msg):
        return
    await msg.answer(
        "✅ Бот запущен.\n\n"
        "Команды:\n"
        "/watch <name> — добавить проект\n"
        "/project <name> — карточка проекта\n"
        "/digest — последние сигналы\n"
        "/mute <name> — замьютить проект\n"
        "/unmute <name> — размьютить проект\n"
        "/setdocs <name> <url> — привязать docs\n"
        "/setcg <name> <coingecko_id> — привязать CoinGecko id\n"
    )

@router.message(Command("watch"))
async def cmd_watch(msg: types.Message):
    if not _is_allowed(msg):
        return
    name = msg.text.replace("/watch", "").strip()
    if not name:
        await msg.answer("Напиши: /watch ProjectName")
        return

    async with SessionLocal() as s:
        q = await s.execute(select(Project).where(Project.name == name))
        p = q.scalar_one_or_none()
        if p is None:
            p = Project(name=name, status="watch", chain="", links_json="{}")
            s.add(p)
            await s.commit()
            await msg.answer(f"➕ Добавил в кэш: {name}")
        else:
            await msg.answer(f"ℹ️ Уже в кэше: {name}")

@router.message(Command("project"))
async def cmd_project(msg: types.Message):
    if not _is_allowed(msg):
        return
    name = msg.text.replace("/project", "").strip()
    if not name:
        await msg.answer("Напиши: /project ProjectName")
        return

    async with SessionLocal() as s:
        q = await s.execute(select(Project).where(Project.name == name))
        p = q.scalar_one_or_none()
        if not p:
            await msg.answer("Не найдено в кэше. Сначала /watch <name>")
            return

        links = json.loads(p.links_json or "{}")

        sq = await s.execute(
            select(Signal)
            .where(Signal.project_name == name)
            .order_by(desc(Signal.created_at))
            .limit(1)
        )
        last = sq.scalar_one_or_none()

        payload = json.loads(last.evidence_json or "{}") if last else {}
        payload.setdefault("links", links)

        conf = float(last.confidence) if last else 3.0
        tier_score = float(payload.get("tier_score", 3.0))

        source = "Система"
        event_type = "Сводка проекта"
        if last:
            if last.signal_type == "dropsearn":
                source = "DropsEarn"
                event_type = "Найдена активность"
            elif last.signal_type == "docs":
                source = "Официальные Docs"
                event_type = "Ключевые слова в документации"
            elif last.signal_type == "funding":
                source = "DefiLlama"
                event_type = "Инвестиционный раунд"
            elif last.signal_type == "market":
                source = "CoinGecko"
                event_type = "Сильное движение рынка (24ч)"

        text = format_signal_card_ru(
            project_name=p.name,
            chain=p.chain,
            source=source,
            event_type=event_type,
            confidence=conf,
            payload=payload,
            project_tier_score=tier_score,
        )

        await msg.answer(text, reply_markup=project_actions_kb(p.name), parse_mode="Markdown")

@router.message(Command("digest"))
async def cmd_digest(msg: types.Message):
    if not _is_allowed(msg):
        return
    async with SessionLocal() as s:
        sq = await s.execute(select(Signal).order_by(desc(Signal.created_at)).limit(10))
        rows = sq.scalars().all()
        if not rows:
            await msg.answer("Пока нет сигналов. Они появятся после первого цикла проверки.")
            return
        out = ["📰 Последние сигналы:"]
        for r in rows:
            out.append(f"• {r.project_name} — {r.signal_type} — {r.title}")
        await msg.answer("\n".join(out))

@router.message(Command("mute"))
async def cmd_mute(msg: types.Message):
    if not _is_allowed(msg):
        return
    name = msg.text.replace("/mute", "").strip()
    if not name:
        await msg.answer("Напиши: /mute ProjectName")
        return

    async with SessionLocal() as s:
        q = await s.execute(select(Project).where(Project.name == name))
        p = q.scalar_one_or_none()
        if not p:
            await msg.answer("Не найдено в кэше.")
            return
        p.muted = 1
        await s.commit()
        await msg.answer(f"🔇 Замьючено: {name}")

@router.message(Command("unmute"))
async def cmd_unmute(msg: types.Message):
    if not _is_allowed(msg):
        return
    name = msg.text.replace("/unmute", "").strip()
    if not name:
        await msg.answer("Напиши: /unmute ProjectName")
        return

    async with SessionLocal() as s:
        q = await s.execute(select(Project).where(Project.name == name))
        p = q.scalar_one_or_none()
        if not p:
            await msg.answer("Не найдено в кэше.")
            return
        p.muted = 0
        await s.commit()
        await msg.answer(f"🔔 Размьючено: {name}")

@router.message(Command("setdocs"))
async def set_docs(msg: types.Message):
    if not _is_allowed(msg):
        return
    parts = msg.text.split()
    if len(parts) < 3:
        await msg.answer("Пример: /setdocs ZKsync https://docs.xyz")
        return
    name, url = parts[1], parts[2]

    async with SessionLocal() as s:
        q = await s.execute(select(Project).where(Project.name == name))
        p = q.scalar_one_or_none()
        if not p:
            await msg.answer("Сначала добавь проект /watch <name>")
            return

        links = json.loads(p.links_json or "{}")
        links["docs"] = url
        p.links_json = json.dumps(links, ensure_ascii=False)
        await s.commit()
        await msg.answer("Docs добавлены ✅")

@router.message(Command("setcg"))
async def set_cg(msg: types.Message):
    if not _is_allowed(msg):
        return
    parts = msg.text.split()
    if len(parts) < 3:
        await msg.answer("Пример: /setcg Arbitrum arbitrum")
        return
    name, cg = parts[1], parts[2]

    async with SessionLocal() as s:
        q = await s.execute(select(Project).where(Project.name == name))
        p = q.scalar_one_or_none()
        if not p:
            await msg.answer("Сначала добавь проект /watch <name>")
            return

        links = json.loads(p.links_json or "{}")
        links["coingecko_id"] = cg
        p.links_json = json.dumps(links, ensure_ascii=False)
        await s.commit()
        await msg.answer("CoinGecko подключен ✅")

@router.callback_query()
async def callbacks(cb: types.CallbackQuery):
    if not _is_allowed_chat_id(cb.message.chat.id):
        await cb.answer("Недоступно", show_alert=True)
        return

    data = cb.data or ""
    if ":" not in data:
        await cb.answer()
        return

    action, name = data.split(":", 1)

    async with SessionLocal() as s:
        q = await s.execute(select(Project).where(Project.name == name))
        p = q.scalar_one_or_none()
        if not p:
            await cb.answer("Не найдено")
            return

        if action == "mute":
            p.muted = 1
            await s.commit()
            await cb.answer("Замьючено ✅")
            return

        if action == "unmute":
            p.muted = 0
            await s.commit()
            await cb.answer("Размьючено ✅")
            return

        if action == "show":
            links = json.loads(p.links_json or "{}")
            sq = await s.execute(
                select(Signal)
                .where(Signal.project_name == name)
                .order_by(desc(Signal.created_at))
                .limit(1)
            )
            last = sq.scalar_one_or_none()
            payload = json.loads(last.evidence_json or "{}") if last else {}
            payload.setdefault("links", links)

            conf = float(last.confidence) if last else 3.0
            tier_score = float(payload.get("tier_score", 3.0))

            source = "Система"
            event_type = "Сводка проекта"
            if last:
                if last.signal_type == "dropsearn":
                    source = "DropsEarn"
                    event_type = "Найдена активность"
                elif last.signal_type == "docs":
                    source = "Официальные Docs"
                    event_type = "Ключевые слова в документации"
                elif last.signal_type == "funding":
                    source = "DefiLlama"
                    event_type = "Инвестиционный раунд"
                elif last.signal_type == "market":
                    source = "CoinGecko"
                    event_type = "Сильное движение рынка (24ч)"

            text = format_signal_card_ru(
                project_name=p.name,
                chain=p.chain,
                source=source,
                event_type=event_type,
                confidence=conf,
                payload=payload,
                project_tier_score=tier_score,
            )
            await cb.message.answer(text, reply_markup=project_actions_kb(p.name), parse_mode="Markdown")
            await cb.answer()
            return

    await cb.answer()

@router.message()
async def fallback(msg: types.Message):
    if not _is_allowed(msg):
        return
    await msg.answer("Напиши команду, например: /start или /watch <name>")


