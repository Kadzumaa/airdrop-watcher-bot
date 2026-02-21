from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def project_actions_kb(project_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔇 Мьют", callback_data=f"mute:{project_name}"),
         InlineKeyboardButton(text="🔔 Анмьют", callback_data=f"unmute:{project_name}")],
        [InlineKeyboardButton(text="📌 Показать проект", callback_data=f"show:{project_name}")],
    ])
