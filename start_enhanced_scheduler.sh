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

# Function to show usage
show_usage() {
    echo "Enhanced OpenInterest Monitor Scheduler"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  (no args)           - Start the enhanced monitor with default config"
    echo "  --config FILE       - Start with specific config file"
    echo "  attach              - Attach to running session"
    echo "  stop                - Stop the enhanced monitor"
    echo "  restart [--config]  - Restart the enhanced monitor"
    echo "  status              - Check session status"
    echo "  monitor             - Monitor and auto-restart"
    echo "  help                - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Start with default config (tokens_config.json)"
    echo "  $0 --config mav.json         # Start with MAV token config"
    echo "  $0 --config milk.json        # Start with MILK token config"
    echo "  $0 restart --config h.json   # Restart with H token config"
    echo "  $0 status                    # Check if monitor is running"
    echo ""
    echo "Available config files:"
    echo "  tokens_config.json (default) - All tokens"
    echo "  mav.json                     - MAV token only"
    echo "  milk.json                    - MILK token only"
    echo "  h.json                       - H token only"
    echo "  more.json                    - MORE token only"
    echo "  sahara.json                  - SAHARA token only"
    echo "  dmc.json                     - DMC token only"
    echo "  cudis.json                   - CUDIS token only"
    echo ""
    echo "Enhanced Features:"
    echo "  📊 Change alerts only (no regular reports)"
    echo "  📈 Increase/decrease indicators"
    echo "  💰 Price and volume information"
    echo "  📱 Enhanced Telegram notifications"
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
    local config_file="tokens_config.json"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --config)
                config_file="$2"
                shift 2
                ;;
            *)
                break
                ;;
        esac
    done
    
    # Check if config file exists
    if [ ! -f "$config_file" ]; then
        print_error "Config file '$config_file' not found"
        echo "Available config files:"
        ls -1 *.json 2>/dev/null | grep -v "test_" || echo "No config files found"
        exit 1
    fi
    
    print_header
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    print_status "Checking prerequisites..."
    check_tmux
    check_python_deps
    check_files
    
    print_status "Starting enhanced OpenInterest monitor in tmux..."
    print_status "Using config file: $config_file"
    
    # Start the enhanced scheduler with config file
    if python3 enhanced_tmux_scheduler.py start --config "$config_file"; then
        print_status "✅ Enhanced monitor started successfully!"
        echo ""
        echo "📱 Session name: enhanced_openinterest_scheduler"
        echo "📄 Config file: $config_file"
        echo "🔗 To attach to the session: python3 enhanced_tmux_scheduler.py attach"
        echo "📊 To check status: python3 enhanced_tmux_scheduler.py status"
        echo "⏹️  To stop: python3 enhanced_tmux_scheduler.py stop"
        echo "🔄 To restart: python3 enhanced_tmux_scheduler.py restart --config $config_file"
        echo "🔍 To monitor: python3 enhanced_tmux_scheduler.py monitor"
        echo ""
        print_status "The enhanced monitor will check every 15 minutes and send alerts only when there are changes"
        echo ""
        echo "📊 Enhanced Features:"
        echo "  • Change alerts only (no regular reports)"
        echo "  • Increase/decrease indicators"
        echo "  • Price and volume information"
        echo "  • Percentage change from previous value"
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
        shift
        python3 enhanced_tmux_scheduler.py restart "$@"
        ;;
    "status")
        python3 enhanced_tmux_scheduler.py status
        ;;
    "monitor")
        python3 enhanced_tmux_scheduler.py monitor
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    "")
        main "$@"
        ;;
    --config)
        main "$@"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac 