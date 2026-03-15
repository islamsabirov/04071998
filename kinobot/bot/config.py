import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    bot_token: str
    admin_ids: list[int]
    required_channel: str
    db_url: str
    # Web-server (Payme/Click webhook uchun)
    webhook_host: str          # masalan: https://mybot.onrender.com
    web_port: int
    # Payme
    payme_merchant_id: str
    payme_key: str
    # Click
    click_service_id: str
    click_merchant_id: str
    click_secret_key: str


def _parse_admin_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    ids: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            continue
    return ids


def get_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise RuntimeError("BOT_TOKEN muhit o'zgaruvchisida ko'rsatilmagan!")

    return Settings(
        bot_token=token,
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
        required_channel=os.getenv("REQUIRED_CHANNEL", "").strip(),
        db_url=os.getenv("DB_URL", "sqlite+aiosqlite:///./bot.db"),
        webhook_host=os.getenv("WEBHOOK_HOST", "").strip().rstrip("/"),
        web_port=int(os.getenv("PORT", "8080")),
        payme_merchant_id=os.getenv("PAYME_MERCHANT_ID", ""),
        payme_key=os.getenv("PAYME_KEY", ""),
        click_service_id=os.getenv("CLICK_SERVICE_ID", ""),
        click_merchant_id=os.getenv("CLICK_MERCHANT_ID", ""),
        click_secret_key=os.getenv("CLICK_SECRET_KEY", ""),
    )


settings = get_settings()

