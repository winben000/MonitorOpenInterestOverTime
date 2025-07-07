import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
BINANCE_API_KEY = os.getenv("binance_api_key")
BINANCE_API_SECRET = os.getenv("binance_api_secret")
BYBIT_API_KEY = os.getenv("bybit_api_key")
BYBIT_API_SECRET = os.getenv("bybit_api_secret")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TOPIC_ID = os.getenv("TOPIC_ID")

# Open Interest Monitoring Configuration
SPIKE_THRESHOLD = 5.0  # 5% spike threshold (lowered for more sensitivity)
MONITORING_INTERVAL = 900  # 15 minutes in seconds

# Supported exchanges for open interest data
SUPPORTED_EXCHANGES = ["binance", "bybit"]

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "open_interest_monitor.log" 