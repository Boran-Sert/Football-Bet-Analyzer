"""Telegram bildirim istemcisi — Kritik sistem olaylarinda admin uyarisi gonderir."""

import logging
from clients.base_client import BaseAPIClient
from core.config import settings

logger = logging.getLogger(__name__)


class TelegramClient(BaseAPIClient):
    """Telegram Bot API uzerinden bildirim gonderir."""

    def __init__(self):
        token = settings.TELEGRAM_BOT_TOKEN or ""
        super().__init__(
            base_url=f"https://api.telegram.org/bot{token}",
            timeout=10.0,
            max_retries=2,
        )
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)

    def _build_headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    async def send_alert(self, message: str) -> bool:
        """Telegram'a uyari mesaji gonderir. Hata durumunda sessizce False doner."""
        if not self.enabled:
            logger.warning("Telegram bildirimi atlanamadi: BOT_TOKEN veya CHAT_ID yapilandirilmamis.")
            return False
        try:
            response = await self._request(
                "POST",
                "/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": f"⚠️ SPORTS-ANALYZER ALERT\n\n{message}",
                    "parse_mode": "HTML",
                },
            )
            return response.status_code == 200
        except Exception as e:
            logger.error("Telegram bildirim hatasi: %s", str(e))
            return False


# Singleton instance
telegram_client = TelegramClient()
