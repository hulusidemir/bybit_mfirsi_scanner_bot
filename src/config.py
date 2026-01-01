import os
from dotenv import load_dotenv

load_dotenv()

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Trading Settings
TIMEFRAME = '15m'
RSI_PERIOD = 14
MFI_PERIOD = 14

# Thresholds
RSI_OVERSOLD = 20
MFI_OVERSOLD = 25
RSI_OVERBOUGHT = 80
MFI_OVERBOUGHT = 80

# Parabolic SAR Settings
PSAR_ENABLED = True
PSAR_AF = 0.02
PSAR_MAX = 0.2
PSAR_CONSECUTIVE_BARS = 10  # Number of bars the price must be below (for LONG) or above (for SHORT) the PSAR

# TD Sequential Settings
TD_SEQ_ENABLED = True

# Filters
MIN_24H_VOLUME_USDT = 5000000  # Minimum 5 Million USDT volume to ensure liquidity

# Alert Settings
ALERT_COOLDOWN_MINUTES = 60  # Minutes to wait before sending another alert for the same coin
