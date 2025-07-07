import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import sys
import csv
import pandas as pd

from config import SPIKE_THRESHOLD, MONITORING_INTERVAL
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
        self.historical_averages = {}  # symbol -> historical average
        self.last_15min_averages = {}  # symbol -> last 15-min average
        self.last_15min_window = {}    # symbol -> (start, end) of last 15-min window
        self.last_15min_avg_per_symbol = {}  # symbol -> (last_window_end, last_avg)
        
        if self.token_list:
            logging.info(f"Monitoring specific tokens: {self.token_list}")
        else:
            logging.info("Monitoring default token list")
        
        # Load existing data if available
        self.load_historical_data()
        self.calculate_historical_averages()
    
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
    
    def calculate_percentage_change(self, current: float, previous: float) -> float:
        """Calculate percentage change between two values"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100
    
    def detect_spikes(self, symbol: str, current_data: OpenInterestData) -> Optional[OpenInterestAlert]:
        """Detect if there's a significant spike or drop in open interest"""
        if symbol not in self.historical_data or len(self.historical_data[symbol]) < 2:
            return None
        
        # Get the most recent previous data point
        previous_data = self.historical_data[symbol][-1]
        
        # Calculate percentage change using USD values
        percentage_change = self.calculate_percentage_change(
            current_data.open_interest_value, 
            previous_data.open_interest_value
        )
        
        # Check if change exceeds threshold (both increase and decrease)
        if abs(percentage_change) >= SPIKE_THRESHOLD:
            # Determine alert type and severity
            alert_type = "spike" if percentage_change > 0 else "drop"
            
            if abs(percentage_change) >= 50:
                severity = "high"
            elif abs(percentage_change) >= 30:
                severity = "medium"
            else:
                severity = "low"
            
            # Create alert using USD values
            alert = OpenInterestAlert(
                symbol=symbol,
                exchange=current_data.exchange,
                current_oi=current_data.open_interest_value,
                previous_oi=previous_data.open_interest_value,
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
            
            # Also check for deviation from historical average
            avg_oi = self.historical_averages.get(symbol, 0.0)
            if avg_oi > 0:
                avg_percentage_change = self.calculate_percentage_change(
                    oi_data.open_interest_value, 
                    avg_oi
                )
                
                if abs(avg_percentage_change) >= SPIKE_THRESHOLD:
                    # Create average-based alert
                    avg_alert_type = "spike" if avg_percentage_change > 0 else "drop"
                    avg_severity = "high" if abs(avg_percentage_change) >= 50 else "medium" if abs(avg_percentage_change) >= 30 else "low"
                    
                    avg_alert = OpenInterestAlert(
                        symbol=symbol,
                        exchange=oi_data.exchange,
                        current_oi=oi_data.open_interest_value,
                        previous_oi=avg_oi,  # Using average as "previous"
                        percentage_change=avg_percentage_change,
                        timestamp=oi_data.timestamp,
                        alert_type=f"avg_{avg_alert_type}",
                        severity=avg_severity
                    )
                    
                    avg_alert_key = f"{symbol}_avg_{avg_alert_type}_{avg_severity}"
                    if avg_alert_key not in self.alerts_sent:
                        alerts.append(avg_alert)
                        self.alerts_sent.add(avg_alert_key)
                        asyncio.create_task(self.remove_alert_from_sent(avg_alert_key))
        
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
                # Get the historical average for this symbol
                avg_oi = self.historical_averages.get(alert.symbol, 0.0)
                
                # Convert alert to dict for formatting
                alert_dict = {
                    'symbol': alert.symbol,
                    'exchange': alert.exchange,
                    'percentage_change': alert.percentage_change,
                    'current_oi': alert.current_oi,  # This will be updated to use USD value
                    'previous_oi': alert.previous_oi,  # This will be updated to use USD value
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'timestamp': alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    'avg_oi': avg_oi  # This will be updated to use USD value
                }
                
                message = format_open_interest_alert(alert_dict)
                await send_telegram_message(message)
                
                logging.info(f"Sent alert for {alert.symbol} on {alert.exchange}: {alert.percentage_change:+.2f}%")
                
            except Exception as e:
                logging.error(f"Error sending alert for {alert.symbol}: {e}")
    
    def calculate_historical_averages(self):
        """Calculate the historical average open interest for each symbol from all data."""
        for symbol, records in self.historical_data.items():
            if records:
                # Use open_interest_value (USD) instead of open_interest (contracts)
                avg = sum(r.open_interest_value for r in records) / len(records)
                self.historical_averages[symbol] = avg
            else:
                self.historical_averages[symbol] = 0.0

    def calculate_15min_average(self, symbol: str, now: datetime) -> float:
        """Calculate the average open interest for the last 15 minutes for a symbol."""
        window_start = now - timedelta(minutes=15)
        records = [r for r in self.historical_data[symbol] if r.timestamp >= window_start and r.timestamp <= now]
        if records:
            return sum(r.open_interest_value for r in records) / len(records)
        return 0.0

    async def send_average_spike_alert(self, symbol: str, old_avg: float, new_avg: float, ratio: float):
        # Get current OI and historical average OI
        current_oi = 0.0
        historical_avg_oi = self.historical_averages.get(symbol, 0.0)
        
        # Try to get the latest current OI from historical data
        if symbol in self.historical_data and self.historical_data[symbol]:
            current_oi = self.historical_data[symbol][-1].open_interest_value
        
        message = (
            f"🚨 <b>OPEN INTEREST AVERAGE SPIKE ALERT</b> 🚨\n\n"
            f"<b>Token:</b> {symbol}\n"
            f"<b>Current OI:</b> ${current_oi:,.0f}\n"
            f"<b>Historical Avg OI:</b> ${historical_avg_oi:,.0f}\n"
            f"<b>Old Avg OI:</b> ${old_avg:,.2f}\n"
            f"<b>New 15-min Avg OI:</b> ${new_avg:,.2f}\n"
            f"<b>Spike Ratio:</b> {ratio:.2f}x\n"
            f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🔥 <b>New average is more than 50x the old average!</b> 🔥"
        )
        await send_telegram_message(message)

    async def send_15min_spike_alert(self, symbol: str, old_avg: float, new_avg: float, ratio: float, window_start, window_end):
        # Get current OI and historical average OI
        current_oi = 0.0
        historical_avg_oi = self.historical_averages.get(symbol, 0.0)
        
        # Try to get the latest current OI from historical data
        if symbol in self.historical_data and self.historical_data[symbol]:
            current_oi = self.historical_data[symbol][-1].open_interest_value
        
        message = (
            f"🚨 <b>15-MIN OPEN INTEREST AVERAGE SPIKE</b> 🚨\n\n"
            f"<b>Token:</b> {symbol}\n"
            f"<b>Current OI:</b> ${current_oi:,.0f}\n"
            f"<b>Historical Avg OI:</b> ${historical_avg_oi:,.0f}\n"
            f"<b>Old 15-min Avg OI:</b> ${old_avg:,.2f}\n"
            f"<b>New 15-min Avg OI:</b> ${new_avg:,.2f}\n"
            f"<b>Spike Ratio:</b> {ratio:.2f}x\n"
            f"<b>Window:</b> {window_start.strftime('%Y-%m-%d %H:%M:%S')} - {window_end.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🔥 <b>New 15-min average is more than 50x the previous window!</b> 🔥"
        )
        await send_telegram_message(message)

    def get_latest_15min_averages(self):
        """Return dict: symbol -> (window_start, window_end, avg) for the latest 15-min window."""
        result = {}
        for symbol, records in self.historical_data.items():
            if not records:
                continue
            sorted_records = sorted(records, key=lambda r: r.timestamp)
            # Get the latest record's window
            last_ts = sorted_records[-1].timestamp
            window_start = last_ts.replace(minute=(last_ts.minute // 15) * 15, second=0, microsecond=0)
            window_end = window_start + timedelta(minutes=15)
            window_records = [r.open_interest_value for r in sorted_records if r.timestamp >= window_start and r.timestamp < window_end]
            if window_records:
                avg = sum(window_records) / len(window_records)
                result[symbol] = (window_start, window_end, avg)
        return result

    async def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            logging.info("Starting monitoring cycle...")
            # Fetch data from all exchanges
            exchange_data = self.aggregator.get_all_exchange_data()
            all_alerts = []
            total_symbols = 0
            now = datetime.now()
            # Process data from each exchange
            for exchange_name, exchange_data_obj in exchange_data.items():
                alerts = self.process_exchange_data(exchange_data_obj)
                all_alerts.extend(alerts)
                total_symbols += len(exchange_data_obj.data) if exchange_data_obj.success else 0
            # Send individual alerts
            await self.send_alerts(all_alerts)
            # Send summary message
            if all_alerts:
                # Add average OI data to alert dicts for summary
                alert_dicts = []
                for alert in all_alerts:
                    alert_dict = alert.__dict__.copy()
                    alert_dict['avg_oi'] = self.historical_averages.get(alert.symbol, 0.0)
                    alert_dicts.append(alert_dict)
                
                summary_message = format_summary_message(
                    alert_dicts, 
                    total_symbols
                )
                await send_telegram_message(summary_message)
            # --- Update 15-min averages CSV ---
            self.export_15min_averages_to_csv()
            # --- Compare new 15-min average to previous and alert if >50x ---
            latest_averages = self.get_latest_15min_averages()
            for symbol, (window_start, window_end, new_avg) in latest_averages.items():
                last_entry = self.last_15min_avg_per_symbol.get(symbol)
                if last_entry:
                    last_window_end, old_avg = last_entry
                    # Only compare if this is a new window
                    if window_end > last_window_end and old_avg > 0:
                        ratio = new_avg / old_avg
                        if ratio > 50:
                            await self.send_15min_spike_alert(symbol, old_avg, new_avg, ratio, window_start, window_end)
                # Update last seen window and avg
                self.last_15min_avg_per_symbol[symbol] = (window_end, new_avg)
            # Save data (no cleanup - keep data forever)
            self.save_historical_data()
            # Recalculate historical averages
            self.calculate_historical_averages()
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
        
        # Add current OI and average OI info if monitoring specific tokens
        if self.token_names and len(self.token_names) == 1:
            symbol = self.token_list[0] if self.token_list else None
            if symbol:
                current_oi = 0.0
                avg_oi = self.historical_averages.get(symbol, 0.0)
                # Try to get the latest current OI from historical data
                if symbol in self.historical_data and self.historical_data[symbol]:
                    current_oi = self.historical_data[symbol][-1].open_interest_value
                
                startup_message += f"\n📈 <b>Current OI:</b> ${current_oi:,.0f}"
                startup_message += f"\n📊 <b>Average OI:</b> ${avg_oi:,.0f}"
        
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

    def export_15min_averages_to_csv(self, output_file='open_interest_15min_averages.csv', token_list=None):
        """Export 15-min window averages for all tokens to a CSV file, appending and deduplicating."""
        rows = []
        # Use self.token_list if set, else token_list argument, else all tokens
        if self.token_list:
            symbols_to_process = self.token_list
        elif token_list:
            symbols_to_process = token_list
        else:
            symbols_to_process = self.historical_data.keys()
        for symbol in symbols_to_process:
            records = self.historical_data.get(symbol, [])
            if not records:
                continue
            sorted_records = sorted(records, key=lambda r: r.timestamp)
            window = []
            window_start = None
            window_end = None
            for record in sorted_records:
                ts = record.timestamp
                aligned_start = ts.replace(minute=(ts.minute // 15) * 15, second=0, microsecond=0)
                aligned_end = aligned_start + timedelta(minutes=15)
                if window_start is None:
                    window_start = aligned_start
                    window_end = aligned_end
                if ts >= window_start and ts < window_end:
                    window.append(record.open_interest_value)
                else:
                    if window and window_start is not None and window_end is not None:
                        avg = sum(window) / len(window)
                        rows.append([
                            symbol,
                            window_start.strftime('%Y-%m-%d %H:%M:%S'),
                            window_end.strftime('%Y-%m-%d %H:%M:%S'),
                            avg,
                            len(window)
                        ])
                    window = [record.open_interest_value]
                    window_start = aligned_start
                    window_end = aligned_end
            if window and window_start is not None and window_end is not None:
                avg = sum(window) / len(window)
                rows.append([
                    symbol,
                    window_start.strftime('%Y-%m-%d %H:%M:%S'),
                    window_end.strftime('%Y-%m-%d %H:%M:%S'),
                    avg,
                    len(window)
                ])
        # Read existing CSV if it exists
        columns = ['symbol', 'window_start', 'window_end', 'average_open_interest', 'count']
        if os.path.exists(output_file):
            old_df = pd.DataFrame([dict(zip(columns, [None]*len(columns)))])[:0]
        else:
            old_df = pd.DataFrame([{}])[:0]
        # New data as DataFrame
        dict_rows = [
            dict(zip(columns, row)) for row in rows
        ]
        if dict_rows:
            new_df = pd.DataFrame(dict_rows)
        else:
            new_df = pd.DataFrame([{}])[:0]
        # Concatenate and drop duplicates
        merged_df = pd.concat([old_df, new_df], ignore_index=True)
        merged_df = merged_df.drop_duplicates(subset=['symbol', 'window_start', 'window_end'], keep='last')
        merged_df = merged_df.sort_values(['symbol', 'window_start'])
        merged_df.to_csv(output_file, index=False)
        print(f"Exported 15-min averages to {output_file}")

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Open Interest Monitor')
    parser.add_argument('--config', type=str, help='Path to JSON config file with token symbols')
    parser.add_argument('token_json_path', nargs='?', help='Path to JSON file with token symbols (deprecated, use --config)')
    parser.add_argument('--export-csv', action='store_true', help='Export 15-min averages to CSV and exit')
    parser.add_argument('--token-json', type=str, help='Path to JSON file with token symbols for export')
    
    args = parser.parse_args()
    
    # Use --config if provided, otherwise fall back to positional argument
    token_json_path = args.config or args.token_json_path
    
    monitor = OpenInterestMonitor(token_json_path)
    if args.export_csv:
        token_list = None
        if args.token_json:
            token_list = monitor.load_token_list(args.token_json)
        monitor.export_15min_averages_to_csv(token_list=token_list)
        return
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main()) 