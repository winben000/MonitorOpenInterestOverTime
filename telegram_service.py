import aiohttp
import logging
from typing import Optional
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TOPIC_ID

async def send_telegram_message(message: str) -> bool:
    """Send a message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram bot token or chat ID not configured. Skipping Telegram message.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    # Add topic_id if available
    if TOPIC_ID:
        payload['message_thread_id'] = TOPIC_ID
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if response.status != 200:
                    logging.error(f"Telegram API error: {result}")
                    return False
                else:
                    logging.info("Telegram message sent successfully")
                    return True
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")
        return False

def format_open_interest_alert(alert_data: dict) -> str:
    """Format open interest alert for Telegram message"""
    symbol = alert_data['symbol']
    exchange = alert_data['exchange']
    percentage_change = alert_data['percentage_change']
    current_oi = alert_data['current_oi']
    previous_oi = alert_data['previous_oi']
    alert_type = alert_data['alert_type']
    severity = alert_data['severity']
    timestamp = alert_data['timestamp']
    avg_oi = alert_data.get('avg_oi', 0.0)  # Get average OI, default to 0 if not provided
    
    # Emoji based on alert type and severity
    if alert_type.startswith("avg_"):
        # Average-based alerts
        base_type = alert_type[4:]  # Remove "avg_" prefix
        if base_type == "spike":
            if severity == "high":
                emoji = "🚨"
            elif severity == "medium":
                emoji = "⚠️"
            else:
                emoji = "📈"
        else:  # drop
            if severity == "high":
                emoji = "🔻"
            elif severity == "medium":
                emoji = "📉"
            else:
                emoji = "🔽"
    else:
        # Regular alerts
        if alert_type == "spike":
            if severity == "high":
                emoji = "🚨"
            elif severity == "medium":
                emoji = "⚠️"
            else:
                emoji = "📈"
        else:  # drop
            if severity == "high":
                emoji = "🔻"
            elif severity == "medium":
                emoji = "📉"
            else:
                emoji = "🔽"
    
    # Determine alert title based on type
    if alert_type.startswith("avg_"):
        alert_title = "OPEN INTEREST AVERAGE DEVIATION ALERT"
        base_type = alert_type[4:]  # Remove "avg_" prefix
        type_display = f"AVERAGE {base_type.upper()}"
    else:
        alert_title = "OPEN INTEREST ALERT"
        type_display = alert_type.upper()
    
    message = f"{emoji} <b>{alert_title}</b> {emoji}\n\n"
    message += f"<b>Token:</b> {symbol}\n"
    message += f"<b>Exchange:</b> {exchange.upper()}\n"
    message += f"<b>Change:</b> {percentage_change:+.2f}%\n"
    message += f"<b>Current OI:</b> ${current_oi:,.0f}\n"
    message += f"<b>Previous OI:</b> ${previous_oi:,.0f}\n"
    message += f"<b>Avg OI:</b> ${avg_oi:,.0f}\n"
    message += f"<b>Type:</b> {type_display}\n"
    message += f"<b>Severity:</b> {severity.upper()}\n"
    message += f"<b>Time:</b> {timestamp}\n\n"
    
    if percentage_change > 50:
        message += "🔥 <b>EXTREME VOLATILITY DETECTED!</b> 🔥\n"
    elif percentage_change > 30:
        message += "⚡ <b>HIGH VOLATILITY DETECTED!</b> ⚡\n"
    
    return message

def format_summary_message(alerts: list, total_symbols: int) -> str:
    """Format a summary message for multiple alerts"""
    if not alerts:
        return "✅ <b>Open Interest Monitor</b>\n\nNo significant changes detected."
    
    message = "📊 <b>OPEN INTEREST MONITORING SUMMARY</b>\n\n"
    message += f"🔍 Monitored Symbols: {total_symbols}\n"
    message += f"🚨 Alerts Generated: {len(alerts)}\n\n"
    
    # Group alerts by exchange
    exchange_alerts = {}
    for alert in alerts:
        exchange = alert['exchange']
        if exchange not in exchange_alerts:
            exchange_alerts[exchange] = []
        exchange_alerts[exchange].append(alert)
    
    for exchange, exchange_alert_list in exchange_alerts.items():
        message += f"<b>{exchange.upper()}</b>:\n"
        for alert in exchange_alert_list[:5]:  # Show top 5 per exchange
            emoji = "🚨" if alert['percentage_change'] > 30 else "⚠️"
            current_oi = alert.get('current_oi', 0)
            avg_oi = alert.get('avg_oi', 0)
            message += f"  {emoji} {alert['symbol']}: {alert['percentage_change']:+.1f}% (OI: ${current_oi:,.0f}, Avg: ${avg_oi:,.0f})\n"
        message += "\n"
    
    return message 