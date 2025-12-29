# RSI & MFI Crypto Scanner Bot

Bu bot, Bybit borsasındaki USDT paritelerini tarayarak RSI ve MFI indikatörlerine göre potansiyel Long ve Short fırsatlarını tespit eder ve Telegram üzerinden sinyal gönderir.

## Özellikler

- **Borsa:** Bybit (Perpetual Futures)
- **Zaman Dilimi:** 15 Dakika (15m)
- **Strateji:**
  - **LONG:** RSI < 20 ve MFI < 25
  - **SHORT:** RSI > 80 ve MFI > 80
- **Filtreler:**
  - 24 Saatlik Hacim (Likidite kontrolü için)
  - VWAP (Trend teyidi için hesaplanır)
- **Bildirimler:** Telegram

## Kurulum

1. Projeyi klonlayın:
   ```bash
   git clone https://github.com/kullaniciadi/rsi_mfi_scanner_bot.git
   cd rsi_mfi_scanner_bot
   ```

2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. `.env` dosyasını oluşturun:
   `.env.example` dosyasının adını `.env` olarak değiştirin ve içerisine gerekli bilgileri girin.
   ```
   BYBIT_API_KEY=your_api_key
   BYBIT_API_SECRET=your_api_secret
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```

## Kullanım

Botu başlatmak için proje ana dizininde şu komutu çalıştırın:

```bash
python -m src.main
```

Bot her 15 dakikada bir tarama yapacak ve uygun coinler için Telegram'a mesaj gönderecektir.

## Sorumluluk Reddi

Bu yazılım sadece eğitim ve bilgilendirme amaçlıdır. Yatırım tavsiyesi değildir. Kripto para piyasası yüksek risk içerir.
