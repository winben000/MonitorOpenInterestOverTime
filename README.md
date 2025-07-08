# Open Interest Monitor

A real-time cryptocurrency open interest monitoring system that tracks open interest spikes on Binance and Bybit exchanges and sends alerts via Telegram. The enhanced version also sends regular data reports every 15 minutes.

## Features

- 🔍 **Real-time Monitoring**: Tracks open interest changes for specified tokens
- 📊 **Multi-Exchange Support**: Monitors both Binance and Bybit
- 🚨 **Smart Alerts**: Sends Telegram notifications when open interest spikes exceed threshold
- 📱 **Regular Reports**: Sends comprehensive data reports every 15 minutes
- ⚡ **Configurable**: Customizable monitoring intervals and spike thresholds
- 📱 **Telegram Integration**: Instant notifications with detailed alert information
- 🎯 **Token-Specific Monitoring**: Monitor individual tokens or multiple tokens simultaneously
- 🔄 **Persistent Operation**: TMux-based sessions that survive disconnections
- 🛡️ **Auto-restart**: Automatic recovery from failures

## Prerequisites

- Python 3.8+
- Telegram Bot Token
- Binance API Key (optional)
- Bybit API Key (optional)
- TMux (for persistent operation)

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

### Enhanced Scheduler (Recommended)

The enhanced scheduler provides regular data reports every 15 minutes plus spike alerts:

```bash
# Start enhanced monitor
chmod +x start_enhanced_scheduler.sh
./start_enhanced_scheduler.sh

# Check status
python3 enhanced_tmux_scheduler.py status

# Attach to session
python3 enhanced_tmux_scheduler.py attach

# Stop monitor
python3 enhanced_tmux_scheduler.py stop

# Restart monitor
python3 enhanced_tmux_scheduler.py restart
```

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

### Individual Token Monitoring

Use the specific token monitoring script:

```bash
# List available tokens
./monitor_specific_token.sh list

# Start monitoring a specific token
./monitor_specific_token.sh start milk
./monitor_specific_token.sh start h
./monitor_specific_token.sh start mav

# Check status
./monitor_specific_token.sh status milk

# View logs
./monitor_specific_token.sh logs milk

# Stop monitoring
./monitor_specific_token.sh stop milk

# Create new token config
./monitor_specific_token.sh create btc
```

## Telegram Notifications

### Regular Data Reports (Every 15 minutes)
```
📊 Open Interest Regular Report

⏰ Time: 2025-07-02 15:30:00
🕐 Uptime: 2d 5h 30m
📈 Monitored Tokens: 7

MILKUSDT
  📊 Current OI: 2.45M (+12.3%)
  📈 Avg OI (24h): 2.18M
  💰 Price: $0.1234
  📊 Volume 24h: 15.67M
  💸 Funding: 0.0123%

HUSDT
  📊 Current OI: 1.23M (-5.2%)
  📈 Avg OI (24h): 1.30M
  💰 Price: $0.0456
  📊 Volume 24h: 8.90M

📊 Summary
Total OI Value: 7.35M
Next report in: 15 minutes
```

### Spike Alert Format
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

### Severity Levels
- **LOW**: 1-30% change
- **MEDIUM**: 30-50% change  
- **HIGH**: 50%+ change

## TMux Session Management

### Session Information
- **Enhanced Session**: `enhanced_openinterest_scheduler` (recommended)
- **Individual Sessions**: `oi-milk`, `oi-h`, `oi-mav`, etc.
- **Runs**: Every 15 minutes
- **Persistent**: Survives disconnections
- **Auto-restart**: On failures

### TMux Commands

```bash
# List all sessions
tmux list-sessions

# Attach to enhanced session
tmux attach-session -t enhanced_openinterest_scheduler

# Attach to specific token session
tmux attach-session -t oi-milk

# Detach from session
# Press Ctrl+B, then D

# Kill a session
tmux kill-session -t oi-milk

# Kill all sessions
tmux kill-server
```

### Session Windows and Panes
- `Ctrl+B, C` - Create new window
- `Ctrl+B, N` - Next window
- `Ctrl+B, P` - Previous window
- `Ctrl+B, %` - Split vertically
- `Ctrl+B, "` - Split horizontally
- `Ctrl+B, arrow keys` - Navigate between panes

## Monitoring and Logs

### View Logs
```bash
# Enhanced scheduler logs
tail -f enhanced_scheduler.log

# TMux scheduler logs
tail -f enhanced_tmux_scheduler.log

# Monitor logs
tail -f open_interest_monitor.log

# Real-time monitoring
tail -f enhanced_scheduler.log -f enhanced_tmux_scheduler.log
```

### Check Status
```bash
# Check enhanced monitor status
python3 enhanced_tmux_scheduler.py status

# Check all tmux sessions
tmux list-sessions

# Check specific token status
./monitor_specific_token.sh status milk
```

## Server Setup

### Ubuntu Server Setup

1. **Upload files to server:**
   ```bash
   scp -r OpenInterest/ ubuntu@your-server-ip:/home/ubuntu/
   ```

2. **SSH into server and setup:**
   ```bash
   ssh ubuntu@your-server-ip
   cd OpenInterest
   ```

3. **Install dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install tmux python3-pip
   pip3 install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   nano .env
   # Fill in your Telegram bot token and chat ID
   ```

5. **Start enhanced monitor:**
   ```bash
   chmod +x start_enhanced_scheduler.sh
   ./start_enhanced_scheduler.sh
   ```

### SystemD Service (Optional)

For automatic startup on boot:

```bash
# Create systemd service
sudo nano /etc/systemd/system/openinterest.service
```

Add this content:
```ini
[Unit]
Description=OpenInterest Monitor
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/OpenInterest
ExecStart=/home/ubuntu/OpenInterest/start_enhanced_scheduler.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable openinterest
sudo systemctl start openinterest
sudo systemctl status openinterest
```

## Project Structure

```
OpenInterest/
├── monitor.py                    # Main monitoring script
├── enhanced_scheduler.py         # Enhanced scheduler with regular reports
├── enhanced_tmux_scheduler.py    # TMux manager for enhanced scheduler
├── start_enhanced_scheduler.sh   # Startup script for enhanced monitor
├── monitor_specific_token.sh     # Individual token monitoring script
├── config.py                     # Configuration settings
├── models.py                     # Data models
├── exchange_service.py           # Exchange API services
├── telegram_service.py           # Telegram alert service
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── .env                          # Environment variables
├── tokens_config.json            # Multi-token configuration
├── mav.json                      # Single token configuration
├── milk.json, h.json, etc.       # Individual token configs
├── enhanced_scheduler.log        # Enhanced scheduler logs
├── enhanced_tmux_scheduler.log   # TMux scheduler logs
├── open_interest_monitor.log     # Main monitoring logs
└── open_interest_data.json       # Historical data storage
```

## Troubleshooting

### Common Issues

#### 1. Enhanced Monitor Not Starting
```bash
# Check if files exist
ls -la enhanced_scheduler.py enhanced_tmux_scheduler.py

# Check Python dependencies
python3 -c "import schedule, requests, ccxt"

# Check tmux installation
which tmux
```

#### 2. No Regular Reports
```bash
# Check if enhanced monitor is running
python3 enhanced_tmux_scheduler.py status

# Check logs
tail -f enhanced_scheduler.log

# Restart if needed
python3 enhanced_tmux_scheduler.py restart
```

#### 3. Permission Issues
```bash
# Fix permissions
chmod +x *.sh
chmod 644 .env
```

#### 4. Session Not Starting
```bash
# Check if tmux is installed
which tmux

# Check Python dependencies
python3 -c "import schedule, requests, ccxt"

# Check environment file
ls -la .env
```

## API Endpoints Used

- **Binance**: Public API for open interest data
- **Bybit**: Public API for open interest data
- **Telegram Bot API**: For sending notifications

## License

This project is for educational and personal use. Please ensure compliance with exchange API terms of service. 