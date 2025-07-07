#!/usr/bin/env python3
"""
Open Interest Monitor Scheduler
Runs the open interest monitor at specified intervals and sends results to Telegram
"""

import schedule
import time
import logging
import subprocess
import sys
import os
from datetime import datetime
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

def run_monitor_cycle():
    """Run one monitoring cycle"""
    try:
        logging.info("Starting scheduled monitoring cycle...")
        
        # Run the monitor for one cycle
        result = subprocess.run([
            sys.executable, 'monitor.py', '--config', 'tokens_config.json'
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            logging.info("Monitoring cycle completed successfully")
        else:
            logging.error(f"Monitoring cycle failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logging.error("Monitoring cycle timed out")
    except Exception as e:
        logging.error(f"Error running monitoring cycle: {e}")

def send_startup_message():
    """Send a startup message to Telegram"""
    try:
        from telegram_service import send_telegram_message
        
        startup_message = f"🚀 <b>Open Interest Monitor Scheduler Started</b>\n\n"
        startup_message += f"⏰ Monitoring every 15 minutes\n"
        startup_message += f"📅 Started on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        startup_message += f"✅ Scheduler is running and monitoring..."
        
        asyncio.run(send_telegram_message(startup_message))
        logging.info("Startup message sent to Telegram")
    except Exception as e:
        logging.error(f"Failed to send startup message: {e}")

def send_shutdown_message():
    """Send a shutdown message to Telegram"""
    try:
        from telegram_service import send_telegram_message
        
        shutdown_message = f"🛑 <b>Open Interest Monitor Scheduler Stopped</b>\n\n"
        shutdown_message += f"📅 Stopped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        shutdown_message += f"⚠️ Monitoring will no longer run automatically"
        
        asyncio.run(send_telegram_message(shutdown_message))
        logging.info("Shutdown message sent to Telegram")
    except Exception as e:
        logging.error(f"Failed to send shutdown message: {e}")

def main():
    """Main function to run the scheduler"""
    print("🚀 Starting Open Interest Monitor Scheduler...")
    print("⏰ Monitoring every 15 minutes")
    print("📱 Telegram notifications enabled")
    print("🔄 Scheduler is running... (Press Ctrl+C to stop)")
    
    # Send startup message
    send_startup_message()
    
    # Schedule monitoring cycles
    schedule.every(15).minutes.do(run_monitor_cycle)
    
    # Also run immediately on startup
    run_monitor_cycle()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down scheduler...")
        send_shutdown_message()
        print("✅ Scheduler stopped gracefully")
    except Exception as e:
        error_msg = f"❌ Scheduler error: {e}"
        logging.error(error_msg)
        print(error_msg)

if __name__ == "__main__":
    main() 