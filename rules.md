# SAAS BACKEND MİMARİSİ VE KODLAMA STANDARTLARI (KATI KURALLAR)

## 1. Sistem Tasarımı ve Veri Akışı Kırmızı Çizgileri
- **Dış API Yasağı:** `routers/` (kullanıcı istekleri) katmanından **KESİNLİKLE** 3rd party veri sağlayıcılarına (örneğin API-Football vs.) istek atılmayacaktır. Tüm kullanıcı istekleri SADECE MongoDB veya Redis üzerinden karşılanacaktır.
- **Veri Tazeleme (Cron Jobs):** Dış API'lerden veri çekme, güncelleme ve veritabanına yazma işlemleri SADECE `tasks/` klasöründeki `APScheduler` görevleri tarafından, önceden belirlenmiş saatlerde yapılacaktır. Kullanıcı eylemi veri güncellemeyi tetikleyemez.
- **Headless & Async:** Uygulama %100 asenkron (async/await) çalışmalıdır. `motor` (Asenkron MongoDB), `redis.asyncio` ve `httpx` (Asenkron HTTP) kullanılacaktır. Senkron kütüphaneler (`requests`, `pymongo`) yasaktır.

## 2. Katmanlı Mimari (Layered Architecture) Dosya Yapısı
Projeye eklenen her kod aşağıdaki klasör sınırlarına uymak zorundadır:
- `core/`: Uygulama ayarları (`pydantic-settings`), DB ve Redis bağlantı nesneleri.
- `schemas/` (veya `models/`): Pydantic v2 DTO (Data Transfer Object) modelleri. İstek ve yanıt şemaları buradadır. DB modelleri ve API yanıtları kesinlikle ayrılacaktır.
- `repositories/`: Veritabanı sorgularının (MongoDB) yapıldığı TEK yerdir. `motor` kütüphanesi sadece burada kullanılır. Verileri dict veya Pydantic model olarak döndürür.
- `services/`: İş mantığı (OOP). Bahis analizi, oran hesaplaması burada yapılır. Bu katman asla HTTP Request objesi (FastAPI Request) almaz, DB bağlantısını bilmez (sadece Repository kullanır).
- `utils/`: Önbellekleme (Caching decorator'ları), şifreleme veya tarih/saat manipülasyon araçları.
- `routers/`: FastAPI endpointleri. Sadece HTTP isteğini alır, Pydantic ile doğrular, Service katmanına paslar ve HTTP yanıtı (JSON) döner.
- `tasks/`: Arka plan işçileri ve cron job'lar.

## 3. Bağımlılık Enjeksiyonu (Dependency Injection - SOLID)
- `routers/` katmanında `services/` katmanını çağırırken kesinlikle `Depends()` kullanılacaktır. Global nesne (singleton) import etmek yasaktır.
- Örnek: `def get_match(match_id: str, service: MatchService = Depends(get_match_service)):`

## 4. Önbellekleme (Caching) ve Performans
- `services/` içindeki okuma (GET) metodlarının sonuçları, `utils/cache.py` içindeki özel bir decorator (örneğin `@cache_response(ttl=3600)`) ile Redis'te önbelleklenmelidir.
- Yanıtlar önce Redis'te aranmalı, yoksa MongoDB'ye (Repository'ye) gidilmelidir.

## 5. Güvenlik ve Hata Yönetimi
- **Rate Limiting:** `routers/` katmanındaki tüm açık endpointlerde Redis tabanlı IP sınırlandırması olacaktır.
- **Exception Handling:** Ham veritabanı hataları veya Python Traceback'leri asla kullanıcıya (frontend'e) dönülmeyecektir. Her zaman standart HTTP HTTPException (400, 404, 500) formatında, temiz JSON dönülecektir.
- Çevresel değişkenler (ENV) `core/config.py` içinde Pydantic `BaseSettings` ile doğrulanacaktır.