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
        # Replace with your verified Resend sender domain
        self.from_address = "Football SaaS <noreply@yourdomain.com>"

    async def _send(self, to_email: str, subject: str, html: str) -> bool:
        """Internal shared send method."""
        if not self.api_key:
            logger.warning("RESEND_API_KEY bulunamadi, e-posta gonderilmeyecek.")
            return False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"from": self.from_address, "to": [to_email], "subject": subject, "html": html}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, headers=headers, json=payload, timeout=10.0)
                if response.status_code in (200, 201):
                    logger.info("E-posta gonderildi: %s → %s", subject, to_email)
                    return True
                logger.error("E-posta hatasi: %s - %s", response.status_code, response.text)
                return False
        except Exception as exc:
            logger.error("E-posta servisine erisilemedi: %s", exc)
            return False

    async def send_verification_email(self, to_email: str, verify_url: str) -> bool:
        html = f"""
        <h2>Football SaaS'a Hos Geldiniz!</h2>
        <p>Hesabinizi aktif etmek icin asagidaki baglantiya tiklayin:</p>
        <a href="{verify_url}" style="padding:10px 20px;background:#007bff;color:#fff;
           text-decoration:none;border-radius:5px;">Hesabimi Dogrula</a>
        <p style="color:#888;font-size:13px;">Bu baglanti 24 saat gecerlidir.</p>
        """
        return await self._send(to_email, "Lutfen hesabinizi dogrulayin", html)

    # ── GAP 2: Password reset email ───────────────────────────────────────────

    async def send_password_reset_email(self, to_email: str, reset_url: str) -> bool:
        """Kullaniciya 1 saatlik sifre sifirlama linki gonderir."""
        html = f"""
        <h2>Sifre Sifirlama Talebi</h2>
        <p>Sifrenizi sifirlamak icin asagidaki baglantiya tiklayin.</p>
        <a href="{reset_url}" style="padding:10px 20px;background:#dc3545;color:#fff;
           text-decoration:none;border-radius:5px;">Sifremi Sifirla</a>
        <p style="color:#888;font-size:13px;">Bu baglanti <strong>1 saat</strong> gecerlidir.</p>
        <p style="color:#888;font-size:13px;">
          Eger bu talebi siz yapmadiysa, bu e-postayi gormezden gelin.
        </p>
        """
        return await self._send(to_email, "Sifre Sifirlama Talebi", html)


email_client = EmailClient()
