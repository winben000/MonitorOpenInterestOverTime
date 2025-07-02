import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import sys

from config import SPIKE_THRESHOLD, MONITORING_INTERVAL, DATA_RETENTION_HOURS
from models import OpenInterestData, OpenInterestAlert, OpenInterestDataEncoder
from exchange_service import OpenInterestAggregator
from telegram_service import send_telegram_message, format_open_interest_alert, format_summary_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('open_interest_monitor.log'),
        logging.StreamHandler()
    ]
)

class OpenInterestMonitor:
    """Monitor open interest changes and generate alerts"""
    
    def __init__(self, token_json_path=None):
        self.token_list = self.load_token_list(token_json_path) if token_json_path else None
        self.token_names = self.extract_token_names(token_json_path) if token_json_path else None
        self.aggregator = OpenInterestAggregator(self.token_list)
        self.historical_data = defaultdict(list)  # symbol -> list of historical data
        self.alerts_sent = set()  # Track sent alerts to avoid duplicates
        self.data_file = "open_interest_data.json"
        self.alerts_file = "open_interest_alerts.json"
        
        if self.token_list:
            logging.info(f"Monitoring specific tokens: {self.token_list}")
        else:
            logging.info("Monitoring default token list")
        
        # Load existing data if available
        self.load_historical_data()
    
    def load_token_list(self, json_path):
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                logging.info(f"Loaded token config: {data}")
                
                # Support both single symbol and list of symbols
                if isinstance(data, dict) and 'symbol' in data:
                    symbol = data['symbol']
                    # Convert to Bybit/CCXT format if needed
                    if symbol.endswith("/USDT:USDT"):
                        symbol = symbol.replace("/USDT:USDT", "USDT")
                    elif symbol.endswith(":USDT"):
                        symbol = symbol.replace(":USDT", "USDT")
                    result = [symbol.replace('/', '')]
                    logging.info(f"Extracted single symbol: {result}")
                    return result
                elif isinstance(data, dict) and 'symbols' in data:
                    result = [s.replace('/', '').replace(":USDT", "USDT").replace("/USDT:USDT", "USDT") for s in data['symbols']]
                    logging.info(f"Extracted symbols list: {result}")
                    return result
                elif isinstance(data, list):
                    result = [s.replace('/', '').replace(":USDT", "USDT").replace("/USDT:USDT", "USDT") for s in data]
                    logging.info(f"Extracted symbols from list: {result}")
                    return result
                else:
                    logging.warning(f"Unknown JSON structure: {type(data)}")
        except Exception as e:
            logging.error(f"Error loading token list from {json_path}: {e}")
        return None
    
    def extract_token_names(self, json_path):
        """Extract token names for display purposes"""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                
                # Support both single symbol and list of symbols
                if isinstance(data, dict) and 'symbol' in data:
                    symbol = data['symbol']
                    # Extract just the token name (before /USDT or /USDT:USDT)
                    if '/' in symbol:
                        token_name = symbol.split('/')[0]
                    else:
                        token_name = symbol.replace('USDT', '').replace(':', '')
                    return [token_name]
                elif isinstance(data, dict) and 'symbols' in data:
                    token_names = []
                    for symbol in data['symbols']:
                        if '/' in symbol:
                            token_name = symbol.split('/')[0]
                        else:
                            token_name = symbol.replace('USDT', '').replace(':', '')
                        token_names.append(token_name)
                    return token_names
                elif isinstance(data, list):
                    token_names = []
                    for symbol in data:
                        if '/' in symbol:
                            token_name = symbol.split('/')[0]
                        else:
                            token_name = symbol.replace('USDT', '').replace(':', '')
                        token_names.append(token_name)
                    return token_names
        except Exception as e:
            logging.error(f"Error extracting token names from {json_path}: {e}")
        return None
    
    def load_historical_data(self):
        """Load historical data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for symbol, records in data.items():
                        self.historical_data[symbol] = []
                        for record in records:
                            # Convert timestamp string back to datetime
                            if isinstance(record['timestamp'], str):
                                record['timestamp'] = datetime.fromisoformat(record['timestamp'])
                            self.historical_data[symbol].append(OpenInterestData(**record))
                logging.info(f"Loaded historical data for {len(self.historical_data)} symbols")
        except Exception as e:
            logging.error(f"Error loading historical data: {e}")
    
    def save_historical_data(self):
        """Save historical data to file"""
        try:
            data_to_save = {}
            for symbol, records in self.historical_data.items():
                data_to_save[symbol] = [
                    {
                        'symbol': record.symbol,
                        'exchange': record.exchange,
                        'open_interest': record.open_interest,
                        'open_interest_value': record.open_interest_value,
                        'timestamp': record.timestamp.isoformat(),
                        'price': record.price,
                        'volume_24h': record.volume_24h,
                        'funding_rate': record.funding_rate
                    }
                    for record in records
                ]
            
            with open(self.data_file, 'w') as f:
                json.dump(data_to_save, f, indent=2, cls=OpenInterestDataEncoder)
        except Exception as e:
            logging.error(f"Error saving historical data: {e}")
    
    def cleanup_old_data(self):
        """Remove data older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=DATA_RETENTION_HOURS)
        
        for symbol in list(self.historical_data.keys()):
            self.historical_data[symbol] = [
                record for record in self.historical_data[symbol]
                if record.timestamp > cutoff_time
            ]
            
            # Remove symbol if no data left
            if not self.historical_data[symbol]:
                del self.historical_data[symbol]
    
    def calculate_percentage_change(self, current: float, previous: float) -> float:
        """Calculate percentage change between two values"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100
    
    def detect_spikes(self, symbol: str, current_data: OpenInterestData) -> Optional[OpenInterestAlert]:
        """Detect if there's a significant spike in open interest"""
        if symbol not in self.historical_data or len(self.historical_data[symbol]) < 2:
            return None
        
        # Get the most recent previous data point
        previous_data = self.historical_data[symbol][-1]
        
        # Calculate percentage change
        percentage_change = self.calculate_percentage_change(
            current_data.open_interest, 
            previous_data.open_interest
        )
        
        # Check if change exceeds threshold
        if abs(percentage_change) >= SPIKE_THRESHOLD:
            # Determine alert type and severity
            alert_type = "spike" if percentage_change > 0 else "drop"
            
            if abs(percentage_change) >= 50:
                severity = "high"
            elif abs(percentage_change) >= 30:
                severity = "medium"
            else:
                severity = "low"
            
            # Create alert
            alert = OpenInterestAlert(
                symbol=symbol,
                exchange=current_data.exchange,
                current_oi=current_data.open_interest,
                previous_oi=previous_data.open_interest,
                percentage_change=percentage_change,
                timestamp=current_data.timestamp,
                alert_type=alert_type,
                severity=severity
            )
            
            return alert
        
        return None
    
    def process_exchange_data(self, exchange_data) -> List[OpenInterestAlert]:
        """Process data from a single exchange and detect spikes"""
        alerts = []
        
        if not exchange_data.success:
            logging.warning(f"Failed to get data from {exchange_data.exchange}: {exchange_data.error}")
            return alerts
        
        for oi_data in exchange_data.data:
            symbol = oi_data.symbol
            
            # Add current data to historical data
            self.historical_data[symbol].append(oi_data)
            
            # Keep only last 10 data points per symbol
            if len(self.historical_data[symbol]) > 10:
                self.historical_data[symbol] = self.historical_data[symbol][-10:]
            
            # Detect spikes
            alert = self.detect_spikes(symbol, oi_data)
            if alert:
                # Check if we've already sent an alert for this symbol recently
                alert_key = f"{symbol}_{alert.alert_type}_{alert.severity}"
                if alert_key not in self.alerts_sent:
                    alerts.append(alert)
                    self.alerts_sent.add(alert_key)
                    
                    # Remove from sent alerts after 1 hour to allow new alerts
                    asyncio.create_task(self.remove_alert_from_sent(alert_key))
        
        return alerts
    
    async def remove_alert_from_sent(self, alert_key: str, delay: int = 3600):
        """Remove alert from sent set after delay"""
        await asyncio.sleep(delay)
        self.alerts_sent.discard(alert_key)
    
    async def send_alerts(self, alerts: List[OpenInterestAlert]):
        """Send alerts to Telegram"""
        if not alerts:
            return
        
        for alert in alerts:
            try:
                # Convert alert to dict for formatting
                alert_dict = {
                    'symbol': alert.symbol,
                    'exchange': alert.exchange,
                    'percentage_change': alert.percentage_change,
                    'current_oi': alert.current_oi,
                    'previous_oi': alert.previous_oi,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'timestamp': alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                message = format_open_interest_alert(alert_dict)
                await send_telegram_message(message)
                
                logging.info(f"Sent alert for {alert.symbol} on {alert.exchange}: {alert.percentage_change:+.2f}%")
                
            except Exception as e:
                logging.error(f"Error sending alert for {alert.symbol}: {e}")
    
    async def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            logging.info("Starting monitoring cycle...")
            
            # Fetch data from all exchanges
            exchange_data = self.aggregator.get_all_exchange_data()
            
            all_alerts = []
            total_symbols = 0
            
            # Process data from each exchange
            for exchange_name, exchange_data_obj in exchange_data.items():
                alerts = self.process_exchange_data(exchange_data_obj)
                all_alerts.extend(alerts)
                total_symbols += len(exchange_data_obj.data) if exchange_data_obj.success else 0
            
            # Send individual alerts
            await self.send_alerts(all_alerts)
            
            # Send summary message
            if all_alerts:
                summary_message = format_summary_message(
                    [alert.__dict__ for alert in all_alerts], 
                    total_symbols
                )
                await send_telegram_message(summary_message)
            
            # Save data and cleanup
            self.save_historical_data()
            self.cleanup_old_data()
            
            logging.info(f"Monitoring cycle completed. Processed {total_symbols} symbols, generated {len(all_alerts)} alerts")
            
        except Exception as e:
            error_message = f"Error in monitoring cycle: {e}"
            logging.error(error_message)
            await send_telegram_message(f"❌ <b>Open Interest Monitor Error</b>\n\n{error_message}")
    
    async def start_monitoring(self):
        """Start continuous monitoring"""
        logging.info("Starting Open Interest Monitor...")
        logging.info(f"Monitoring interval: {MONITORING_INTERVAL} seconds")
        logging.info(f"Spike threshold: {SPIKE_THRESHOLD}%")
        
        # Send startup message
        if self.token_names:
            if len(self.token_names) == 1:
                token_display = f"Open Interest For {self.token_names[0].upper()} Monitor Started"
            else:
                token_display = f"Open Interest For {', '.join(self.token_names).upper()} Monitor Started"
        else:
            token_display = "Open Interest Monitor Started"
        
        startup_message = f"🚀 <b>{token_display}</b>\n\n"
        startup_message += f"📊 Monitoring interval: {MONITORING_INTERVAL} seconds\n"
        startup_message += f"🚨 Spike threshold: {SPIKE_THRESHOLD}%\n"
        startup_message += f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await send_telegram_message(startup_message)
        
        while True:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(MONITORING_INTERVAL)
            except KeyboardInterrupt:
                logging.info("Monitoring stopped by user")
                break
            except Exception as e:
                logging.error(f"Unexpected error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Open Interest Monitor')
    parser.add_argument('--config', type=str, help='Path to JSON config file with token symbols')
    parser.add_argument('token_json_path', nargs='?', help='Path to JSON file with token symbols (deprecated, use --config)')
    
    args = parser.parse_args()
    
    # Use --config if provided, otherwise fall back to positional argument
    token_json_path = args.config or args.token_json_path
    
    monitor = OpenInterestMonitor(token_json_path)
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main()) 