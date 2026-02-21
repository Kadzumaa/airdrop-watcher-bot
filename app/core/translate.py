# Free-first: in v1 we keep translation as a pluggable component.
# Default: passthrough (no translation). Later we can add Argos Translate offline.
async def translate_to_ru(text: str) -> str:
    return text
