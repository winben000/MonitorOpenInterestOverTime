#!/bin/bash

# Enhanced OpenInterest Monitor Scheduler - TMux Startup Script
# This script starts the enhanced OpenInterest monitor in a tmux session with regular data reports

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Enhanced OpenInterest Monitor${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Check if tmux is installed
check_tmux() {
    if ! command -v tmux &> /dev/null; then
        print_error "tmux is not installed. Please install it first:"
        echo "  Ubuntu/Debian: sudo apt-get install tmux"
        echo "  CentOS/RHEL: sudo yum install tmux"
        echo "  macOS: brew install tmux"
        exit 1
    fi
    print_status "tmux is installed"
}

# Check if Python dependencies are available
check_python_deps() {
    if ! python3 -c "import schedule, requests, ccxt" 2>/dev/null; then
        print_error "Python dependencies are missing. Please install them:"
        echo "  pip3 install -r requirements.txt"
        exit 1
    fi
    print_status "Python dependencies are available"
}

# Check if required files exist
check_files() {
    if [ ! -f "enhanced_scheduler.py" ]; then
        print_error "enhanced_scheduler.py not found. Please make sure you're in the correct directory."
        exit 1
    fi
    if [ ! -f "monitor.py" ]; then
        print_error "monitor.py not found. Please make sure you're in the correct directory."
        exit 1
    fi
    print_status "Required files found"
}

# Main function
main() {
    print_header
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    print_status "Checking prerequisites..."
    check_tmux
    check_python_deps
    check_files
    
    print_status "Starting enhanced OpenInterest monitor in tmux..."
    
    # Start the enhanced scheduler
    if python3 enhanced_tmux_scheduler.py start; then
        print_status "✅ Enhanced monitor started successfully!"
        echo ""
        echo "📱 Session name: enhanced_openinterest_scheduler"
        echo "🔗 To attach to the session: python3 enhanced_tmux_scheduler.py attach"
        echo "📊 To check status: python3 enhanced_tmux_scheduler.py status"
        echo "⏹️  To stop: python3 enhanced_tmux_scheduler.py stop"
        echo "🔄 To restart: python3 enhanced_tmux_scheduler.py restart"
        echo "🔍 To monitor: python3 enhanced_tmux_scheduler.py monitor"
        echo ""
        print_status "The enhanced monitor will run every 15 minutes with regular data reports"
        echo ""
        echo "📊 Enhanced Features:"
        echo "  • Regular data reports every 15 minutes"
        echo "  • Current OI and average OI data"
        echo "  • Price and volume information"
        echo "  • Percentage change from average"
        echo "  • Enhanced Telegram notifications"
    else
        print_error "Failed to start enhanced monitor"
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    "attach")
        python3 enhanced_tmux_scheduler.py attach
        ;;
    "stop")
        python3 enhanced_tmux_scheduler.py stop
        ;;
    "restart")
        python3 enhanced_tmux_scheduler.py restart
        ;;
    "status")
        python3 enhanced_tmux_scheduler.py status
        ;;
    "monitor")
        python3 enhanced_tmux_scheduler.py monitor
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  - Start the enhanced monitor"
        echo "  attach     - Attach to running session"
        echo "  stop       - Stop the enhanced monitor"
        echo "  restart    - Restart the enhanced monitor"
        echo "  status     - Check session status"
        echo "  monitor    - Monitor and auto-restart"
        echo "  help       - Show this help"
        echo ""
        echo "Enhanced Features:"
        echo "  📊 Regular data reports every 15 minutes"
        echo "  📈 Current OI and average OI data"
        echo "  💰 Price and volume information"
        echo "  📱 Enhanced Telegram notifications"
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac 