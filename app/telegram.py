import httpx
from app.config import settings


async def send_message(text: str):
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_channel_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        return r.json()
