"""Asenkron e-posta gonderim servisi.

Resend API kullanilir (ucretsiz plan: 3000 mail/ay).
rules.md Madde 1: httpx.AsyncClient ile async calisir (senkron SDK yasak).
"""

import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

_RESEND_URL = "https://api.resend.com/emails"


async def send_reset_email(to_email: str, username: str, reset_token: str) -> bool:
    """Sifre sifirlama e-postasi gonderir.

    Args:
        to_email: Alici e-posta adresi.
        username: Kullanici adi (e-posta iceriginde kullanilir).
        reset_token: JWT sifirlama token'i.

    Returns:
        True ise basarili, False ise hata olustu.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY tanimli degil, e-posta gonderilemedi.")
        return False

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;
                padding: 32px; background: #f9fafb; border-radius: 12px;">

        <h2 style="color: #111827; margin-bottom: 8px;">
            Sifre Sifirlama Talebi
        </h2>

        <p style="color: #4b5563; font-size: 15px;">
            Merhaba <strong>{username}</strong>,
        </p>

        <p style="color: #4b5563; font-size: 15px;">
            Hesabiniz icin bir sifre sifirlama talebi aldik.
            Asagidaki butona tiklayarak yeni sifrenizi belirleyebilirsiniz.
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{reset_link}"
               style="background: #2563eb; color: white; padding: 14px 32px;
                      border-radius: 8px; text-decoration: none; font-weight: bold;
                      font-size: 16px;">
                Sifremi Sifirla
            </a>
        </div>

        <p style="color: #9ca3af; font-size: 13px;">
            Bu baglanti {settings.RESET_TOKEN_EXPIRE_MINUTES} dakika icerisinde
            gecerliligini yitirecektir.
        </p>

        <p style="color: #9ca3af; font-size: 13px;">
            Eger bu talebi siz yapmadiysa bu e-postayi gormezden gelebilirsiniz.
        </p>

        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />

        <p style="color: #d1d5db; font-size: 11px; text-align: center;">
            Football SaaS &mdash; Canli Oran Analiz Sistemi
        </p>
    </div>
    """

    payload = {
        "from": "Football SaaS <noreply@resend.dev>",
        "to": [to_email],
        "subject": "Sifre Sifirlama Talebi",
        "html": html_body,
    }

    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(_RESEND_URL, json=payload, headers=headers, timeout=10)

        if resp.status_code in (200, 201):
            logger.info("Sifre sifirlama e-postasi gonderildi: %s", to_email)
            return True

        logger.error("Resend API hatasi (%s): %s", resp.status_code, resp.text)
        return False

    except httpx.HTTPError as exc:
        logger.exception("E-posta gonderim hatasi: %s", exc)
        return False
