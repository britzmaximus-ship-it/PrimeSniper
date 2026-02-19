import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def send(msg: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_USER_ID:
        return
    try:
        requests.post(
            TELEGRAM_API,
            json={
                "chat_id": TELEGRAM_USER_ID,
                "text": msg[:3900],
                "disable_web_page_preview": True
            },
            timeout=15,
        )
    except Exception:
        pass