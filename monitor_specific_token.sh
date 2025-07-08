#!/bin/bash

# OpenInterest Specific Token Monitor
# This script helps you monitor specific tokens

set -e

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
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to show usage
show_usage() {
    echo "OpenInterest Specific Token Monitor"
    echo ""
    echo "Usage: $0 [COMMAND] [TOKEN]"
    echo ""
    echo "Commands:"
    echo "  start <token>     - Start monitoring a specific token"
    echo "  stop <token>      - Stop monitoring a specific token"
    echo "  status <token>    - Check status of token monitoring"
    echo "  list              - List available token configs"
    echo "  create <token>    - Create a new token config"
    echo "  attach <token>    - Attach to token's tmux session"
    echo "  logs <token>      - View logs for specific token"
    echo "  help              - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start milk     # Start monitoring MILK token"
    echo "  $0 start btc      # Start monitoring BTC token"
    echo "  $0 status milk    # Check MILK monitoring status"
    echo "  $0 create eth     # Create ETH token config"
    echo ""
    echo "Available tokens:"
    echo "  milk, h, more, sahara, dmc, mav, cudis"
}

# Function to check if tmux is installed
check_tmux() {
    if ! command -v tmux &> /dev/null; then
        print_error "tmux is not installed. Please install it first:"
        echo "  sudo apt-get install tmux"
        exit 1
    fi
}

# Function to list available token configs
list_tokens() {
    print_header "Available Token Configurations"
    
    echo ""
    echo "Pre-configured tokens:"
    echo "======================"
    
    # List existing token configs
    for config in *.json; do
        if [[ -f "$config" && "$config" != "tokens_config.json" && "$config" != "test_symbols.json" ]]; then
            token_name=$(basename "$config" .json)
            if [[ -f "$config" ]]; then
                symbol=$(python3 -c "import json; print(json.load(open('$config'))['symbol'])" 2>/dev/null || echo "Unknown")
                echo -e "  ${GREEN}$token_name${NC} - $symbol"
            fi
        fi
    done
    
    echo ""
    echo "Multi-token config:"
    echo "==================="
    if [[ -f "tokens_config.json" ]]; then
        symbols=$(python3 -c "import json; print(', '.join(json.load(open('tokens_config.json'))['symbols']))" 2>/dev/null || echo "Unknown")
        echo -e "  ${GREEN}tokens_config.json${NC} - $symbols"
    fi
}

# Function to create a new token config
create_token_config() {
    local token_name=$1
    
    if [[ -z "$token_name" ]]; then
        print_error "Please specify a token name"
        echo "Usage: $0 create <token_name>"
        exit 1
    fi
    
    # Convert token name to uppercase and add USDT
    symbol="${token_name^^}USDT"
    
    print_status "Creating config for $token_name ($symbol)..."
    
    # Create the config file
    cat > "${token_name}.json" <<EOF
{
    "exchange": "bybit",
    "symbol": "$symbol"
}
EOF
    
    print_status "Created ${token_name}.json"
    echo "You can now start monitoring with: $0 start $token_name"
}

# Function to start monitoring a specific token
start_token_monitoring() {
    local token_name=$1
    
    if [[ -z "$token_name" ]]; then
        print_error "Please specify a token name"
        echo "Usage: $0 start <token_name>"
        exit 1
    fi
    
    local config_file="${token_name}.json"
    
    if [[ ! -f "$config_file" ]]; then
        print_error "Config file $config_file not found"
        echo "Available configs:"
        list_tokens
        exit 1
    fi
    
    check_tmux
    
    print_header "Starting $token_name Monitoring"
    
    # Create tmux session name
    local session_name="oi-${token_name}"
    
    # Check if session already exists
    if tmux has-session -t "$session_name" 2>/dev/null; then
        print_warning "Session $session_name already exists"
        read -p "Do you want to restart it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            tmux kill-session -t "$session_name"
        else
            print_status "Use '$0 attach $token_name' to attach to existing session"
            exit 0
        fi
    fi
    
    # Create new tmux session
    print_status "Creating tmux session: $session_name"
    tmux new-session -d -s "$session_name" -n "monitor"
    
    # Start the monitor in the session
    tmux send-keys -t "$session_name:monitor" "cd $(pwd)" C-m
    tmux send-keys -t "$session_name:monitor" "python3 monitor.py --config $config_file" C-m
    
    print_status "✅ $token_name monitoring started successfully!"
    echo ""
    echo "📱 Session name: $session_name"
    echo "🔗 To attach: $0 attach $token_name"
    echo "📊 To check status: $0 status $token_name"
    echo "⏹️  To stop: $0 stop $token_name"
    echo "📝 To view logs: $0 logs $token_name"
}

# Function to stop monitoring a specific token
stop_token_monitoring() {
    local token_name=$1
    
    if [[ -z "$token_name" ]]; then
        print_error "Please specify a token name"
        echo "Usage: $0 stop <token_name>"
        exit 1
    fi
    
    local session_name="oi-${token_name}"
    
    print_status "Stopping $token_name monitoring..."
    
    if tmux has-session -t "$session_name" 2>/dev/null; then
        tmux kill-session -t "$session_name"
        print_status "✅ $token_name monitoring stopped"
    else
        print_warning "No active session found for $token_name"
    fi
}

# Function to check status of token monitoring
check_token_status() {
    local token_name=$1
    
    if [[ -z "$token_name" ]]; then
        print_error "Please specify a token name"
        echo "Usage: $0 status <token_name>"
        exit 1
    fi
    
    local session_name="oi-${token_name}"
    local config_file="${token_name}.json"
    
    print_header "$token_name Monitoring Status"
    
    echo ""
    echo "Configuration:"
    echo "=============="
    if [[ -f "$config_file" ]]; then
        symbol=$(python3 -c "import json; print(json.load(open('$config_file'))['symbol'])" 2>/dev/null || echo "Unknown")
        echo -e "  ${GREEN}✓${NC} Config file: $config_file"
        echo -e "  ${GREEN}✓${NC} Symbol: $symbol"
    else
        echo -e "  ${RED}✗${NC} Config file not found: $config_file"
    fi
    
    echo ""
    echo "TMux Session:"
    echo "============="
    if tmux has-session -t "$session_name" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Session running: $session_name"
        
        # Check if session has active panes
        if tmux list-panes -t "$session_name" 2>/dev/null | grep -q .; then
            echo -e "  ${GREEN}✓${NC} Session has active panes"
        else
            echo -e "  ${YELLOW}⚠${NC} Session exists but no active panes"
        fi
    else
        echo -e "  ${RED}✗${NC} Session not running: $session_name"
    fi
    
    echo ""
    echo "Recent Logs:"
    echo "============"
    if [[ -f "open_interest_monitor.log" ]]; then
        # Show recent logs for this token
        if grep -i "$token_name" open_interest_monitor.log | tail -5; then
            echo ""
        else
            echo "  No recent logs found for $token_name"
        fi
    else
        echo "  No log file found"
    fi
}

# Function to attach to token's tmux session
attach_to_token() {
    local token_name=$1
    
    if [[ -z "$token_name" ]]; then
        print_error "Please specify a token name"
        echo "Usage: $0 attach <token_name>"
        exit 1
    fi
    
    local session_name="oi-${token_name}"
    
    if tmux has-session -t "$session_name" 2>/dev/null; then
        print_status "Attaching to $token_name monitoring session..."
        tmux attach-session -t "$session_name"
    else
        print_error "No active session found for $token_name"
        echo "Start monitoring first with: $0 start $token_name"
        exit 1
    fi
}

# Function to view logs for specific token
view_token_logs() {
    local token_name=$1
    
    if [[ -z "$token_name" ]]; then
        print_error "Please specify a token name"
        echo "Usage: $0 logs <token_name>"
        exit 1
    fi
    
    print_status "Showing logs for $token_name..."
    
    if [[ -f "open_interest_monitor.log" ]]; then
        echo "Filtering logs for $token_name (press Ctrl+C to stop):"
        echo ""
        grep -i "$token_name" open_interest_monitor.log | tail -f
    else
        print_error "No log file found"
        exit 1
    fi
}

# Main script logic
case "${1:-help}" in
    start)
        start_token_monitoring "$2"
        ;;
    stop)
        stop_token_monitoring "$2"
        ;;
    status)
        check_token_status "$2"
        ;;
    list)
        list_tokens
        ;;
    create)
        create_token_config "$2"
        ;;
    attach)
        attach_to_token "$2"
        ;;
    logs)
        view_token_logs "$2"
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac 