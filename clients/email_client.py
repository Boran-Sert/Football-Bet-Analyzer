"""E-posta gonderim istemcisi (Resend)."""

import logging
import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class EmailClient:
    """Resend API uzerinden asenkron e-posta gonderir."""

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.base_url = "https://api.resend.com/emails"

    async def send_verification_email(self, to_email: str, verify_url: str) -> bool:
        """Kullaniciya dogrulama e-postasi gonderir.

        Not: Gercek uygulamada 'from' adresi dogrulanmis bir domain olmalidir.
        Test ortaminda onboarding@resend.dev kullanilabilir.
        """
        if not self.api_key:
            logger.warning("RESEND_API_KEY bulunamadi, e-posta gonderilmeyecek.")
            return False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "from": "Acme <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "Football-Better: Lutfen hesabinizi dogrulayin",
            "html": f"""
            <h2>Football-Better'a Hos Geldiniz!</h2>
            <p>Hesabinizi aktif hale getirmek ve analizlere ulasmak icin lutfen asagidaki baglantiya tiklayin:</p>
            <a href="{verify_url}" style="padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Hesabimi Dogrula</a>
            <p>Bu baglanti 24 saat gecerlidir.</p>
            """
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, headers=headers, json=payload, timeout=10.0)
                if response.status_code in (200, 201):
                    logger.info("Dogrulama e-postasi gonderildi: %s", to_email)
                    return True
                else:
                    logger.error("E-posta gonderim hatasi: %s - %s", response.status_code, response.text)
                    return False
        except Exception as exc:
            logger.error("E-posta servisine erisilemedi: %s", exc)
            return False

email_client = EmailClient()
