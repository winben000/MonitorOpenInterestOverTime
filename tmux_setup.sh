#!/bin/bash

# OpenInterest TMUX Setup Script
# This script sets up tmux sessions for running the OpenInterest monitor

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

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    print_error "tmux is not installed. Please install tmux first:"
    echo "  Ubuntu/Debian: sudo apt-get install tmux"
    echo "  macOS: brew install tmux"
    echo "  CentOS/RHEL: sudo yum install tmux"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_header "OpenInterest TMUX Setup"

# Check if Python dependencies are installed
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in current directory"
    exit 1
fi

print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Function to create a tmux session
create_session() {
    local session_name=$1
    local command=$2
    local description=$3
    
    print_status "Creating tmux session: $session_name - $description"
    
    # Kill existing session if it exists
    tmux kill-session -t "$session_name" 2>/dev/null || true
    
    # Create new session
    tmux new-session -d -s "$session_name" -n "main"
    
    # Set up the session with the command
    tmux send-keys -t "$session_name:main" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$session_name:main" "$command" C-m
    
    print_status "Session '$session_name' created successfully"
}

# Function to create a monitoring session for individual tokens
create_token_session() {
    local token_name=$1
    local config_file=$2
    
    if [ -f "$config_file" ]; then
        create_session "oi-$token_name" "python3 monitor.py --config $config_file" "Monitor for $token_name"
    else
        print_warning "Config file $config_file not found, skipping $token_name"
    fi
}

# Create main scheduler session
print_header "Setting up Main Scheduler"
create_session "oi-scheduler" "python3 scheduler.py" "Main OpenInterest Scheduler"

# Create individual token monitoring sessions
print_header "Setting up Individual Token Monitors"

# Check which token config files exist and create sessions for them
token_configs=(
    "milk:milk.json"
    "h:h.json"
    "more:more.json"
    "sahara:sahara.json"
    "dmc:dmc.json"
    "mav:mav.json"
    "cudis:cudis.json"
)

for token_config in "${token_configs[@]}"; do
    IFS=':' read -r token_name config_file <<< "$token_config"
    create_token_session "$token_name" "$config_file"
done

# Create a session for running all monitors together
print_header "Setting up Multi-Monitor Session"
create_session "oi-all-monitors" "./run_all_monitors.sh" "All Token Monitors"

# Create a session for manual monitoring
print_header "Setting up Manual Monitoring Session"
create_session "oi-manual" "python3 monitor.py --config tokens_config.json" "Manual Multi-Token Monitor"

# Create a session for logs and monitoring
print_header "Setting up Logs Session"
tmux kill-session -t "oi-logs" 2>/dev/null || true
tmux new-session -d -s "oi-logs" -n "logs"
tmux send-keys -t "oi-logs:logs" "cd '$SCRIPT_DIR'" C-m
tmux send-keys -t "oi-logs:logs" "tail -f open_interest_monitor.log scheduler.log" C-m

print_header "TMUX Sessions Created Successfully"

echo ""
echo "Available tmux sessions:"
echo "  ${GREEN}oi-scheduler${NC}     - Main scheduler (runs every 15 minutes)"
echo "  ${GREEN}oi-all-monitors${NC}  - All individual token monitors"
echo "  ${GREEN}oi-manual${NC}        - Manual multi-token monitoring"
echo "  ${GREEN}oi-logs${NC}          - Log monitoring"
echo ""
echo "Individual token sessions:"
for token_config in "${token_configs[@]}"; do
    IFS=':' read -r token_name config_file <<< "$token_config"
    if [ -f "$config_file" ]; then
        echo "  ${GREEN}oi-$token_name${NC}      - Monitor for $token_name"
    fi
done

echo ""
echo "TMUX Commands:"
echo "  ${YELLOW}tmux list-sessions${NC}           - List all sessions"
echo "  ${YELLOW}tmux attach-session -t oi-scheduler${NC}  - Attach to scheduler"
echo "  ${YELLOW}tmux attach-session -t oi-logs${NC}       - View logs"
echo "  ${YELLOW}tmux kill-session -t oi-scheduler${NC}    - Stop scheduler"
echo "  ${YELLOW}tmux kill-server${NC}                     - Stop all sessions"
echo ""
echo "Quick start:"
echo "  ${GREEN}tmux attach-session -t oi-scheduler${NC}"
echo ""
print_status "Setup complete! The OpenInterest monitor is now running in tmux sessions." 