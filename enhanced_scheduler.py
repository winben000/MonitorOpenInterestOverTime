#!/usr/bin/env python3
"""
Enhanced Open Interest Monitor Scheduler
Runs the open interest monitor at specified intervals and sends regular data updates to Telegram
"""

import schedule
import time
import logging
import subprocess
import sys
import os
import json
import asyncio
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
    def __init__(self):
        self.data_file = "open_interest_data.json"
        self.last_report_time = None
        self.monitoring_start_time = datetime.now()
        
    def run_monitor_cycle(self):
        """Run one monitoring cycle and collect data"""
        try:
            logging.info("Starting enhanced monitoring cycle...")
            
            # Run the monitor for one cycle
            result = subprocess.run([
                sys.executable, 'monitor.py', '--config', 'tokens_config.json'
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            if result.returncode == 0:
                logging.info("Monitoring cycle completed successfully")
                # Send regular data report
                self.send_regular_data_report()
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

    def send_regular_data_report(self):
        """Send regular data report to Telegram"""
        try:
            from telegram_service import send_telegram_message
            
            # Load current data
            data = self.load_current_data()
            if not data:
                logging.warning("No data available for report")
                return
            
            # Get current time
            now = datetime.now()
            self.last_report_time = now
            
            # Calculate uptime
            uptime = now - self.monitoring_start_time
            uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
            
            # Build report message
            report_message = f"📊 <b>Open Interest Regular Report</b>\n\n"
            report_message += f"⏰ Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            report_message += f"🕐 Uptime: {uptime_str}\n"
            report_message += f"📈 Monitored Tokens: {len(data)}\n\n"
            
            # Add data for each token
            for symbol, records in data.items():
                if not records:
                    continue
                
                # Get latest record
                latest_record = records[-1]
                
                # Calculate averages
                averages = self.calculate_averages(records)
                
                # Format the data
                current_oi = float(latest_record.get('open_interest', 0))
                current_oi_value = float(latest_record.get('open_interest_value', 0))
                avg_oi = averages['avg_oi']
                avg_oi_value = averages['avg_oi_value']
                
                # Calculate percentage change from average
                if avg_oi_value > 0:
                    pct_change = ((current_oi_value - avg_oi_value) / avg_oi_value) * 100
                    pct_str = f"({pct_change:+.1f}%)"
                else:
                    pct_str = "(N/A)"
                
                # Add token data to report
                report_message += f"<b>{symbol}</b>\n"
                report_message += f"  📊 Current OI: {self.format_number(current_oi_value)} {pct_str}\n"
                report_message += f"  📈 Avg OI (24h): {self.format_number(avg_oi_value)}\n"
                report_message += f"  💰 Price: ${latest_record.get('price', 0):.4f}\n"
                report_message += f"  📊 Volume 24h: {self.format_number(float(latest_record.get('volume_24h', 0)))}\n"
                
                # Add funding rate if available
                funding_rate = latest_record.get('funding_rate', 0)
                if funding_rate != 0:
                    report_message += f"  💸 Funding: {funding_rate:.4f}%\n"
                
                report_message += "\n"
            
            # Add summary
            total_oi_value = sum(float(records[-1].get('open_interest_value', 0)) for records in data.values() if records)
            report_message += f"<b>📊 Summary</b>\n"
            report_message += f"Total OI Value: {self.format_number(total_oi_value)}\n"
            report_message += f"Next report in: 15 minutes\n"
            
            # Send the message
            asyncio.run(send_telegram_message(report_message))
            logging.info("Regular data report sent to Telegram")
            
        except Exception as e:
            logging.error(f"Failed to send regular data report: {e}")

    def send_startup_message(self):
        """Send a startup message to Telegram"""
        try:
            from telegram_service import send_telegram_message
            
            startup_message = f"🚀 <b>Enhanced Open Interest Monitor Started</b>\n\n"
            startup_message += f"⏰ Monitoring every 15 minutes\n"
            startup_message += f"📊 Regular data reports enabled\n"
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
            shutdown_message += f"⚠️ Regular monitoring will no longer run"
            
            asyncio.run(send_telegram_message(shutdown_message))
            logging.info("Enhanced shutdown message sent to Telegram")
        except Exception as e:
            logging.error(f"Failed to send shutdown message: {e}")

    def run(self):
        """Main function to run the enhanced scheduler"""
        print("🚀 Starting Enhanced Open Interest Monitor Scheduler...")
        print("⏰ Monitoring every 15 minutes")
        print("📊 Regular data reports every 15 minutes")
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
    scheduler = EnhancedScheduler()
    scheduler.run()

if __name__ == "__main__":
    main() 