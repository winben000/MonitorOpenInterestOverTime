#!/usr/bin/env python3
"""
Enhanced TMux-based OpenInterest Monitor Scheduler
Runs the enhanced OpenInterest monitor in a tmux session with regular data reports
"""

import subprocess
import sys
import os
import time
import signal
import logging
import argparse
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_tmux_scheduler.log'),
        logging.StreamHandler()
    ]
)

class EnhancedTmuxScheduler:
    def __init__(self, session_name="enhanced_openinterest_scheduler", config_file="tokens_config.json"):
        self.session_name = session_name
        self.config_file = config_file
        self.script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enhanced_scheduler.py")
        
    def send_telegram_notification(self, message):
        """Send notification to Telegram"""
        try:
            # Import telegram service
            from telegram_service import send_telegram_message
            import asyncio
            asyncio.run(send_telegram_message(message))
            logging.info("Telegram notification sent")
        except Exception as e:
            logging.error(f"Failed to send Telegram notification: {e}")
    
    def tmux_command(self, command):
        """Execute tmux command and return result"""
        try:
            result = subprocess.run(
                f"tmux {command}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logging.error("Tmux command timed out")
            return False, "", "Command timed out"
        except Exception as e:
            logging.error(f"Tmux command failed: {e}")
            return False, "", str(e)
    
    def session_exists(self):
        """Check if tmux session exists"""
        success, stdout, stderr = self.tmux_command(f"has-session -t {self.session_name}")
        return success
    
    def create_session(self):
        """Create new tmux session"""
        logging.info(f"Creating enhanced tmux session: {self.session_name} with config: {self.config_file}")
        
        # Create session and run the enhanced scheduler
        command = f"new-session -d -s {self.session_name} -c {os.getcwd()}"
        success, stdout, stderr = self.tmux_command(command)
        
        if not success:
            logging.error(f"Failed to create tmux session: {stderr}")
            return False
        
        # Send the startup command to the session with config file
        startup_cmd = f"send-keys -t {self.session_name} 'python3 {self.script_path} --config {self.config_file}' Enter"
        success, stdout, stderr = self.tmux_command(startup_cmd)
        
        if not success:
            logging.error(f"Failed to start enhanced scheduler in tmux: {stderr}")
            return False
        
        logging.info(f"Enhanced tmux session created and scheduler started with config: {self.config_file}")
        return True
    
    def attach_session(self):
        """Attach to existing tmux session"""
        logging.info(f"Attaching to enhanced tmux session: {self.session_name}")
        os.system(f"tmux attach-session -t {self.session_name}")
    
    def kill_session(self):
        """Kill tmux session"""
        logging.info(f"Killing enhanced tmux session: {self.session_name}")
        success, stdout, stderr = self.tmux_command(f"kill-session -t {self.session_name}")
        
        if success:
            logging.info("Enhanced tmux session killed successfully")
            self.send_telegram_notification(
                f"🛑 <b>Enhanced OpenInterest Monitor Stopped</b>\n\n"
                f"📅 Stopped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"⚠️ Enhanced monitoring will no longer run automatically"
            )
        else:
            logging.error(f"Failed to kill tmux session: {stderr}")
        
        return success
    
    def restart_session(self):
        """Restart tmux session"""
        logging.info("Restarting enhanced tmux session")
        self.kill_session()
        time.sleep(2)
        return self.create_session()
    
    def get_session_status(self):
        """Get status of tmux session"""
        if not self.session_exists():
            return "not_running"
        
        # Check if the session has any panes
        success, stdout, stderr = self.tmux_command(f"list-panes -t {self.session_name}")
        if not success or not stdout.strip():
            return "empty"
        
        return "running"
    
    def monitor_session(self):
        """Monitor the tmux session and restart if needed"""
        logging.info("Starting enhanced session monitor...")
        
        while True:
            try:
                status = self.get_session_status()
                
                if status == "not_running":
                    logging.warning("Enhanced session not running, creating new session...")
                    self.send_telegram_notification(
                        f"⚠️ <b>Enhanced OpenInterest Monitor Restart</b>\n\n"
                        f"📅 Session was down, restarting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"🔄 Creating new enhanced tmux session..."
                    )
                    self.create_session()
                
                elif status == "empty":
                    logging.warning("Enhanced session exists but is empty, restarting...")
                    self.restart_session()
                
                time.sleep(300)  # Check every 5 minutes
                
            except KeyboardInterrupt:
                logging.info("Enhanced monitor interrupted by user")
                break
            except Exception as e:
                logging.error(f"Enhanced monitor error: {e}")
                time.sleep(60)  # Wait before retrying

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Enhanced OpenInterest Monitor Scheduler - TMux Manager")
    parser.add_argument("command", nargs="?", help="Command to execute")
    parser.add_argument("--config", default="tokens_config.json", help="Path to the tokens configuration file")
    args = parser.parse_args()
    
    # Create scheduler with config file
    scheduler = EnhancedTmuxScheduler(config_file=args.config)
    
    if not args.command:
        print("🚀 Enhanced OpenInterest Monitor Scheduler - TMux Manager")
        print("")
        print("Usage:")
        print("  python3 enhanced_tmux_scheduler.py start [--config FILE]     - Start the enhanced monitor in tmux")
        print("  python3 enhanced_tmux_scheduler.py attach                    - Attach to running session")
        print("  python3 enhanced_tmux_scheduler.py stop                      - Stop the enhanced monitor")
        print("  python3 enhanced_tmux_scheduler.py restart [--config FILE]   - Restart the enhanced monitor")
        print("  python3 enhanced_tmux_scheduler.py status                    - Check session status")
        print("  python3 enhanced_tmux_scheduler.py monitor                   - Monitor and auto-restart")
        print("")
        print("Examples:")
        print("  python3 enhanced_tmux_scheduler.py start                     - Start with default config")
        print("  python3 enhanced_tmux_scheduler.py start --config mav.json   - Start with MAV config")
        print("  python3 enhanced_tmux_scheduler.py start --config milk.json  - Start with MILK config")
        print("")
        print("Features:")
        print("  📊 Regular data reports every 15 minutes")
        print("  📈 Current OI and average OI data")
        print("  💰 Price and volume information")
        print("  📱 Enhanced Telegram notifications")
        print("")
        return
    
    command = args.command.lower()
    
    if command == "start":
        if scheduler.session_exists():
            print("⚠️  Enhanced session already exists. Use 'restart' to restart or 'attach' to connect.")
        else:
            if scheduler.create_session():
                print("✅ Enhanced OpenInterest monitor started successfully in tmux session")
                print(f"📱 Session name: {scheduler.session_name}")
                print(f"📄 Config file: {scheduler.config_file}")
                print("🔗 Use 'attach' to connect to the session")
                print("📊 Use 'status' to check if it's running")
                print("⏰ Enhanced monitor runs every 15 minutes with regular reports")
            else:
                print("❌ Failed to start enhanced monitor")
                sys.exit(1)
    
    elif command == "attach":
        if scheduler.session_exists():
            scheduler.attach_session()
        else:
            print("❌ No running enhanced session found. Use 'start' to create one.")
            sys.exit(1)
    
    elif command == "stop":
        if scheduler.session_exists():
            if scheduler.kill_session():
                print("✅ Enhanced OpenInterest monitor stopped successfully")
            else:
                print("❌ Failed to stop enhanced monitor")
                sys.exit(1)
        else:
            print("⚠️  No running enhanced session found")
    
    elif command == "restart":
        if scheduler.restart_session():
            print("✅ Enhanced OpenInterest monitor restarted successfully")
            print(f"📄 Config file: {scheduler.config_file}")
        else:
            print("❌ Failed to restart enhanced monitor")
            sys.exit(1)
    
    elif command == "status":
        status = scheduler.get_session_status()
        if status == "running":
            print("✅ Enhanced OpenInterest monitor is running")
            print(f"📄 Config file: {scheduler.config_file}")
        elif status == "empty":
            print("⚠️  Enhanced session exists but is empty")
        else:
            print("❌ Enhanced OpenInterest monitor is not running")
    
    elif command == "monitor":
        print("🔍 Starting enhanced session monitor (Ctrl+C to stop)...")
        scheduler.monitor_session()
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python3 enhanced_tmux_scheduler.py' for usage information")
        sys.exit(1)

if __name__ == "__main__":
    main() 