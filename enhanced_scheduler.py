#!/usr/bin/env python3
"""
Enhanced Open Interest Monitor Scheduler
Runs the open interest monitor at specified intervals and sends alerts only when there are changes
"""

import schedule
import time
import logging
import subprocess
import sys
import os
import json
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_scheduler.log'),
        logging.StreamHandler()
    ]
)

class EnhancedScheduler:
    def __init__(self, config_file: str = "tokens_config.json"):
        self.config_file = config_file
        self.data_file = "open_interest_data.json"
        self.last_report_time = None
        self.monitoring_start_time = datetime.now()
        self.previous_oi_values = {}  # Store previous OI values to detect changes
        
    def run_monitor_cycle(self):
        """Run one monitoring cycle and check for changes"""
        try:
            logging.info(f"Starting enhanced monitoring cycle with config: {self.config_file}")
            
            # Run the monitor for one cycle
            result = subprocess.run([
                sys.executable, 'monitor.py', '--config', self.config_file
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            if result.returncode == 0:
                logging.info("Monitoring cycle completed successfully")
                # Check for changes and send alerts
                self.check_for_changes()
            else:
                logging.error(f"Monitoring cycle failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logging.error("Monitoring cycle timed out")
        except Exception as e:
            logging.error(f"Error running monitoring cycle: {e}")

    def load_current_data(self) -> Dict:
        """Load current open interest data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading data: {e}")
        return {}

    def check_for_changes(self):
        """Check for changes in Open Interest and send alerts"""
        try:
            # Load current data
            data = self.load_current_data()
            if not data:
                logging.warning("No data available for change detection")
                return
            
            # Check each token for changes
            for symbol, records in data.items():
                if not records:
                    continue
                
                # Get latest record
                latest_record = records[-1]
                current_oi_value = float(latest_record.get('open_interest_value', 0))
                
                # Check if we have a previous value for this symbol
                if symbol in self.previous_oi_values:
                    previous_oi_value = self.previous_oi_values[symbol]
                    
                    # Calculate change
                    change = current_oi_value - previous_oi_value
                    change_percentage = (change / previous_oi_value * 100) if previous_oi_value > 0 else 0
                    
                    # Only send alert if there's a significant change (more than 1%)
                    if abs(change_percentage) > 1.0:
                        self.send_change_alert(symbol, latest_record, previous_oi_value, current_oi_value, change_percentage)
                
                # Update the previous value for next comparison
                self.previous_oi_values[symbol] = current_oi_value
                
        except Exception as e:
            logging.error(f"Error checking for changes: {e}")

    def send_change_alert(self, symbol: str, latest_record: Dict, previous_value: float, current_value: float, change_percentage: float):
        """Send alert for Open Interest change"""
        try:
            from telegram_service import send_telegram_message
            
            # Determine if it's an increase or decrease
            if change_percentage > 0:
                change_emoji = "📈"
                change_type = "INCREASE"
                change_direction = "↗️"
            else:
                change_emoji = "📉"
                change_type = "DECREASE"
                change_direction = "↘️"
            
            # Calculate averages for context
            data = self.load_current_data()
            averages = self.calculate_averages(data.get(symbol, []))
            avg_oi_value = averages['avg_oi_value']
            
            # Calculate percentage from average
            avg_change = ((current_value - avg_oi_value) / avg_oi_value * 100) if avg_oi_value > 0 else 0
            
            # Build alert message
            alert_message = f"🚨 <b>OPEN INTEREST CHANGE ALERT</b> 🚨\n\n"
            alert_message += f"<b>{symbol}</b>\n"
            alert_message += f"📊 {change_emoji} <b>{change_type}</b> {change_direction}\n"
            alert_message += f"📈 Change: {change_percentage:+.2f}%\n"
            alert_message += f"💰 Previous OI: {self.format_number(previous_value)}\n"
            alert_message += f"💰 Current OI: {self.format_number(current_value)}\n"
            alert_message += f"📊 vs 24h Avg: {avg_change:+.1f}%\n"
            alert_message += f"💵 Price: ${latest_record.get('price', 0):.4f}\n"
            alert_message += f"📊 Volume 24h: {self.format_number(float(latest_record.get('volume_24h', 0)))}\n"
            
            # Add funding rate if available
            funding_rate = latest_record.get('funding_rate', 0)
            if funding_rate != 0:
                alert_message += f"💸 Funding: {funding_rate:.4f}%\n"
            
            alert_message += f"\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            alert_message += f"🔄 Next check in: 15 minutes\n"
            
            # Send the alert
            asyncio.run(send_telegram_message(alert_message))
            logging.info(f"Change alert sent for {symbol}: {change_percentage:+.2f}%")
            
        except Exception as e:
            logging.error(f"Failed to send change alert: {e}")

    def calculate_averages(self, symbol_data: List) -> Dict:
        """Calculate average OI for a symbol"""
        if not symbol_data:
            return {"avg_oi": 0, "avg_oi_value": 0, "data_points": 0}
        
        # Get recent data (last 24 hours)
        now = datetime.now()
        recent_data = []
        
        for record in symbol_data:
            try:
                if isinstance(record['timestamp'], str):
                    record_time = datetime.fromisoformat(record['timestamp'])
                else:
                    record_time = record['timestamp']
                
                if now - record_time <= timedelta(hours=24):
                    recent_data.append(record)
            except Exception as e:
                logging.warning(f"Error parsing timestamp: {e}")
                continue
        
        if not recent_data:
            return {"avg_oi": 0, "avg_oi_value": 0, "data_points": 0}
        
        # Calculate averages
        total_oi = sum(float(r.get('open_interest', 0)) for r in recent_data)
        total_oi_value = sum(float(r.get('open_interest_value', 0)) for r in recent_data)
        count = len(recent_data)
        
        return {
            "avg_oi": total_oi / count if count > 0 else 0,
            "avg_oi_value": total_oi_value / count if count > 0 else 0,
            "data_points": count
        }

    def format_number(self, number: float) -> str:
        """Format large numbers for display"""
        if number >= 1_000_000_000:
            return f"{number/1_000_000_000:.2f}B"
        elif number >= 1_000_000:
            return f"{number/1_000_000:.2f}M"
        elif number >= 1_000:
            return f"{number/1_000:.2f}K"
        else:
            return f"{number:.2f}"

    def send_startup_message(self):
        """Send a startup message to Telegram"""
        try:
            from telegram_service import send_telegram_message
            
            startup_message = f"🚀 <b>Enhanced Open Interest Monitor Started</b>\n\n"
            startup_message += f"⏰ Monitoring every 15 minutes\n"
            startup_message += f"📊 Change alerts only (no regular reports)\n"
            startup_message += f"📅 Started on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            startup_message += f"✅ Enhanced scheduler is running..."
            
            asyncio.run(send_telegram_message(startup_message))
            logging.info("Enhanced startup message sent to Telegram")
        except Exception as e:
            logging.error(f"Failed to send startup message: {e}")

    def send_shutdown_message(self):
        """Send a shutdown message to Telegram"""
        try:
            from telegram_service import send_telegram_message
            
            # Calculate total uptime
            uptime = datetime.now() - self.monitoring_start_time
            uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
            
            shutdown_message = f"🛑 <b>Enhanced Open Interest Monitor Stopped</b>\n\n"
            shutdown_message += f"📅 Stopped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            shutdown_message += f"⏱️ Total uptime: {uptime_str}\n"
            shutdown_message += f"⚠️ Change monitoring will no longer run"
            
            asyncio.run(send_telegram_message(shutdown_message))
            logging.info("Enhanced shutdown message sent to Telegram")
        except Exception as e:
            logging.error(f"Failed to send shutdown message: {e}")

    def run(self):
        """Main function to run the enhanced scheduler"""
        print("🚀 Starting Enhanced Open Interest Monitor Scheduler...")
        print("⏰ Monitoring every 15 minutes")
        print("📊 Change alerts only (no regular reports)")
        print("📱 Telegram notifications enabled")
        print("🔄 Enhanced scheduler is running... (Press Ctrl+C to stop)")
        
        # Send startup message
        self.send_startup_message()
        
        # Schedule monitoring cycles
        schedule.every(15).minutes.do(self.run_monitor_cycle)
        
        # Also run immediately on startup
        self.run_monitor_cycle()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\n⏹️  Shutting down enhanced scheduler...")
            self.send_shutdown_message()
            print("✅ Enhanced scheduler stopped gracefully")
        except Exception as e:
            error_msg = f"❌ Enhanced scheduler error: {e}"
            logging.error(error_msg)
            print(error_msg)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enhanced Open Interest Monitor Scheduler")
    parser.add_argument("--config", default="tokens_config.json", help="Path to the tokens configuration file")
    args = parser.parse_args()

    scheduler = EnhancedScheduler(config_file=args.config)
    scheduler.run()

if __name__ == "__main__":
    main() 