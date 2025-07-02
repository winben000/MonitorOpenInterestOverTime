# Open Interest Monitor

A real-time cryptocurrency open interest monitoring system that tracks open interest spikes on Binance and Bybit exchanges and sends alerts via Telegram.

## Features

- 🔍 **Real-time Monitoring**: Tracks open interest changes for specified tokens
- 📊 **Multi-Exchange Support**: Monitors both Binance and Bybit
- 🚨 **Smart Alerts**: Sends Telegram notifications when open interest spikes exceed threshold
- ⚡ **Configurable**: Customizable monitoring intervals and spike thresholds
- 📱 **Telegram Integration**: Instant notifications with detailed alert information
- 🎯 **Token-Specific Monitoring**: Monitor individual tokens or multiple tokens simultaneously

## Prerequisites

- Python 3.8+
- Telegram Bot Token
- Binance API Key (optional)
- Bybit API Key (optional)

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd OpenInterest
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the OpenInterest directory:
   ```env
   # API Keys (optional for public data)
   binance_api_key=your_binance_api_key
   binance_api_secret=your_binance_api_secret
   bybit_api_key=your_bybit_api_key
   bybit_api_secret=your_bybit_api_secret

   # Telegram Configuration (required)
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   TOPIC_ID=your_topic_id
   ```

## Configuration

### Environment Variables

- `SPIKE_THRESHOLD`: Percentage change threshold for alerts (default: 30.0%)
- `MONITORING_INTERVAL`: Monitoring cycle in seconds (default: 900 seconds = 15 minutes)
- `DATA_RETENTION_HOURS`: How long to keep historical data (default: 24 hours)

### Token Configuration

Create JSON files to specify which tokens to monitor:

**Single Token:**
```json
{
  "exchange": "bybit",
  "symbol": "BTC/USDT"
}
```

**Multiple Tokens:**
```json
{
  "exchange": "bybit",
  "symbols": [
    "BTCUSDT",
    "ETHUSDT",
    "SAHARAUSDT"
  ]
}
```

## Usage

### Basic Usage

**Monitor specific tokens:**
```bash
python3 monitor.py --config tokens_config.json
```

**Monitor single token:**
```bash
python3 monitor.py --config btc.json
```

**Monitor with default token list:**
```bash
python3 monitor.py
```

### Example Token Configurations

**tokens_config.json** (multiple tokens):
```json
{
  "exchange": "bybit",
  "symbols": [
    "MILKUSDT",
    "HUSDT",
    "MOREUSDT",
    "SAHARAUSDT",
    "DMCUSDT",
    "MAVUSDT",
    "CUDISUSDT"
  ]
}
```

**mav.json** (single token):
```json
{
  "exchange": "bybit",
  "symbol": "MAV/USDT"
}
```

### Running Multiple Monitors

**Option 1: Single monitor for multiple tokens (recommended)**
```bash
python3 monitor.py --config tokens_config.json
```

**Option 2: Individual monitors for each token**
```bash
python3 monitor.py --config milk.json &
python3 monitor.py --config h.json &
python3 monitor.py --config more.json &
# ... etc
```

**Option 3: Use the provided script**
```bash
./run_all_monitors.sh
```

## Telegram Alerts

### Individual Alert Format
```
🚨 OPEN INTEREST ALERT 🚨

Token: MAVUSDT
Exchange: bybit
Change: +45.67%
Current OI: 1,234,567
Previous OI: 847,123
Type: SPIKE
Severity: HIGH
Time: 2025-07-02 10:45:23

⚡ HIGH VOLATILITY DETECTED! ⚡
```

### Summary Alert Format
```
📊 OPEN INTEREST MONITORING SUMMARY

🔍 Monitored Symbols: 7
🚨 Alerts Generated: 2

BYBIT:
  🚨 MILKUSDT: +45.7%
  ⚠️ HUSDT: +32.1%
```

### Severity Levels
- **LOW**: 1-30% change
- **MEDIUM**: 30-50% change  
- **HIGH**: 50%+ change

## Project Structure

```
OpenInterest/
├── monitor.py              # Main monitoring script
├── config.py               # Configuration settings
├── models.py               # Data models
├── exchange_service.py     # Exchange API services
├── telegram_service.py     # Telegram alert service
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .env                   # Environment variables
├── tokens_config.json     # Example multi-token config
├── mav.json              # Example single token config
├── run_all_monitors.sh   # Script to run multiple monitors
└── test_*.py             # Test scripts
```

## API Endpoints Used

### Binance
- Open Interest: `/fapi/v1/openInterest`
- 24hr Ticker: `/fapi/v1/ticker/24hr`
- Funding Rate: `/fapi/v1/fundingRate`

### Bybit
- Open Interest: `/v5/market/open-interest`
- Tickers: `/v5/market/tickers`
- Funding History: `/v5/market/funding/history`

## Logging

The monitor creates detailed logs in:
- Console output
- `open_interest_monitor.log` file

Log levels include:
- INFO: Normal operations
- WARNING: API errors for individual tokens
- ERROR: Critical errors

## Data Storage

Historical data is stored in:
- `open_interest_data.json`: Historical open interest data
- Data is automatically cleaned up after 24 hours

## Troubleshooting

### Common Issues

1. **Telegram not sending messages**
   - Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correct
   - Ensure the bot has permission to send messages to the chat

2. **API rate limits**
   - Increase `MONITORING_INTERVAL` to reduce API calls
   - Add API keys for higher rate limits

3. **Token not found**
   - Verify token symbols are correct for the exchange
   - Check if the token has futures trading available

### Testing

Run the test scripts to verify setup:
```bash
python3 test_token_loading.py
python3 test_token_names.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and informational purposes only. Cryptocurrency trading involves risk, and past performance does not guarantee future results. Always do your own research and consider consulting with a financial advisor before making investment decisions.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details 