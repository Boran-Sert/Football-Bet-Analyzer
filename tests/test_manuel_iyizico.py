import asyncio
from services.payment.iyzico_provider import IyzicoProvider


async def test_iyzico():
    provider = IyzicoProvider()
    try:
        # 'pro' planı için test oturumu aç
        url = await provider.create_checkout_session(
            user_id="test_user_123", user_email="test@example.com", plan_id="pro"
        )
        print(f"✅ Başarılı! Ödeme Sayfası: {url}")
    except Exception as e:
        print(f"❌ Hata: {e}")


if __name__ == "__main__":
    asyncio.run(test_iyzico())
