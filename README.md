# Football Bet Analyzer

Bu uygulama, yaklaşan futbol maçlarının canlı oranlarını geçmiş sezonlardaki benzer oran profilleriyle karşılaştırarak analiz eder. Ayrıca lig puan durumlarını dinamik olarak gösterir.

## Özellikler

- **Canlı Oran Analizi:** Yaklaşan maçların oranlarını geçmiş verilerle kıyaslar.
- **Benzerlik Motoru:** Öklid mesafesi (Euclidean Distance) kullanarak en benzer geçmiş maçları bulur.
- **Lig Puan Durumu:** Güncel (2025-2026) ve geçmiş sezon puan durumlarını otomatik hesaplar.
- **Akıllı Takım Eşleştirme:** Farklı veri kaynaklarındaki (API vs CSV) takım isimlerini otomatik eşleştirir ve puan tablosunda vurgular.
- **Responsive Tasarım:** Mobil, tablet ve masaüstü uyumlu, modern ve karanlık tema odaklı arayüz.
- **Güvenli Mimari:** API anahtarları ve dosya erişimleri için güvenlik bariyerleri içerir.

## Kurulum

1. Depoyu klonlayın:
   ```bash
   git clone https://github.com/Boran-Sert/Football-Bet-Analyzer.git
   cd Football-Bet-Analyzer
   ```

2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. `.env` dosyası oluşturun ve The Odds API anahtarınızı ekleyin:
   ```env
   ODDS_API_KEY=your_api_key_here
   ```

4. Uygulamayı çalıştırın:
   ```bash
   streamlit run app.py
   ```

## Proje Yapısı

- `app.py`: Ana uygulama ve sayfa akışı.
- `data_fetcher.py`: Veri çekme katmanı (CSV & API).
- `data_processor.py`: Veri işleme ve puan durumu hesaplama.
- `ui_helpers.py`: Stil, CSS ve takım eşleştirme yardımcıları.
- `analyzer.py`: Oran benzerlik motoru.
- `config.py`: Konfigürasyon ve sabitler.

## Teknolojiler

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [The Odds API](https://the-odds-api.com/)

## Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.
