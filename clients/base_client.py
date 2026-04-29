"""Temel asenkron HTTP istemcisi.

Retry, timeout ve hata yonetimi iceren soyut sinif.
Tum dis API istemcileri bunu miras alir.
"""

import logging
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger(__name__)

# Varsayilan retry ve timeout ayarlari
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # saniye: 2, 4, 8


class APIClientError(Exception):
    """Dis API istegi sirasinda olusan hata."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class QuotaExhaustedError(APIClientError):
    """API kota limiti asildi."""
    pass


class BaseAPIClient(ABC):
    """Soyut asenkron HTTP istemcisi.

    Alt siniflar `base_url` ve `_build_headers()` saglamalidir.
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        verify_ssl: bool = True,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl

    @abstractmethod
    def _build_headers(self) -> dict[str, str]:
        """Alt sinif ozel header'lar saglar."""
        ...

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Retry mantikli HTTP istegi.

        Returns:
            httpx.Response nesnesi.

        Raises:
            QuotaExhaustedError: 429 alindiginda.
            APIClientError: Diger HTTP hatalarinda.
        """
        import asyncio

        url = f"{self.base_url}{path}" if self.base_url else path
        headers = self._build_headers()
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
                    response = await client.request(
                        method, url, params=params, headers=headers, **kwargs,
                    )

                # Kota asimi
                if response.status_code == 429:
                    raise QuotaExhaustedError(
                        f"API kota limiti asildi: {url}",
                        status_code=429,
                    )

                # Desteklenmeyen parametre (422) — retry yapma, direkt firsat
                if response.status_code == 422:
                    raise APIClientError(
                        f"API 422 hatasi (desteklenmeyen parametre): {url}",
                        status_code=422,
                    )

                response.raise_for_status()

                # Basarili — kota bilgilerini logla
                remaining = response.headers.get("x-requests-remaining")
                if remaining is not None:
                    logger.info(
                        "API kota durumu — kalan: %s, kullanilan: %s",
                        remaining,
                        response.headers.get("x-requests-used", "?"),
                    )

                return response

            except QuotaExhaustedError:
                raise  # Retry yapma, direkt firsat

            except httpx.HTTPStatusError as exc:
                last_error = exc
                # 422 gibi detay gerektiren hatalarda govdeyi de logla
                try:
                    error_detail = exc.response.json()
                except Exception:
                    error_detail = exc.response.text

                if attempt < self.max_retries:
                    wait = RETRY_BACKOFF_FACTOR ** attempt
                    logger.warning(
                        "API istegi basarisiz (%d/%d): %s | Detay: %s",
                        attempt, self.max_retries, str(exc), error_detail
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error("API istegi tamamen basarisiz: %s | Detay: %s", str(exc), error_detail)

            except httpx.RequestError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    wait = RETRY_BACKOFF_FACTOR ** attempt
                    logger.warning("API baglanti hatasi (%d/%d): %s", attempt, self.max_retries, str(exc))
                    await asyncio.sleep(wait)
                else:
                    logger.error("API baglanti hatasi tamamen basarisiz: %s", str(exc))

        raise APIClientError(
            f"API istegi {self.max_retries} denemeden sonra basarisiz: {last_error}",
        )

    async def get(self, path: str, params: dict | None = None) -> httpx.Response:
        """GET istegi gonderir."""
        return await self._request("GET", path, params=params)
