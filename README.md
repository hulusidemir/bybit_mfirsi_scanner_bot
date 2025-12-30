# RSI & MFI Crypto Scanner Bot

This bot scans USDT pairs on the Bybit exchange to identify potential Long and Short opportunities based on RSI and MFI indicators, sending signals via Telegram.

## Features

- **Exchange:** Bybit (Perpetual Futures)
- **Timeframe:** 15 Minutes (15m)
- **Strategy:**
  - **LONG:** RSI < 20 and MFI < 25
  - **SHORT:** RSI > 80 and MFI > 80
- **Filters:**
  - **Dynamic Volume Filter:** Fetches fresh market data on every scan and only analyzes coins with 24h Volume > 5M USDT (configurable).
  - **VWAP:** Calculated for trend confirmation.
- **Notifications:** Telegram

## Installation

1. Clone the project:
   ```bash
   git clone https://github.com/hulusidemir/rsi_mfi_scanner_bot.git
   cd rsi_mfi_scanner_bot
   ```

2. Install required libraries:
   ```bash
   pip install -r requirements.txt
   ```

3. Create the `.env` file:
   Rename `.env.example` to `.env` and fill in the required information.
   ```
   BYBIT_API_KEY=your_api_key
   BYBIT_API_SECRET=your_api_secret
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```

## Usage

To start the bot, run the following command in the project root directory:

```bash
python -m src.main
```

The bot will scan every 15 minutes and send messages to Telegram for suitable coins.

## Disclaimer

This software is for educational and informational purposes only. It is not investment advice. The cryptocurrency market involves high risk.
