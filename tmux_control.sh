#!/bin/bash

# OpenInterest TMUX Control Script
# Easy commands to manage tmux sessions

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

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to show usage
show_usage() {
    echo "OpenInterest TMUX Control Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       - Start all tmux sessions"
    echo "  stop        - Stop all tmux sessions"
    echo "  restart     - Restart all tmux sessions"
    echo "  status      - Show status of all sessions"
    echo "  logs        - Attach to logs session"
    echo "  scheduler   - Attach to scheduler session"
    echo "  manual      - Attach to manual monitoring session"
    echo "  all         - Attach to all monitors session"
    echo "  list        - List all available sessions"
    echo "  kill        - Kill all sessions (force stop)"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start all sessions"
    echo "  $0 status    # Check session status"
    echo "  $0 logs      # View logs"
    echo "  $0 stop      # Stop all sessions"
}

# Function to check if tmux is installed
check_tmux() {
    if ! command -v tmux &> /dev/null; then
        print_error "tmux is not installed. Please install tmux first:"
        echo "  Ubuntu/Debian: sudo apt-get install tmux"
        echo "  macOS: brew install tmux"
        echo "  CentOS/RHEL: sudo yum install tmux"
        exit 1
    fi
}

# Function to start all sessions
start_sessions() {
    print_header "Starting OpenInterest TMUX Sessions"
    check_tmux
    
    cd "$SCRIPT_DIR"
    
    # Run the setup script to create all sessions
    if [ -f "tmux_setup.sh" ]; then
        bash tmux_setup.sh
    else
        print_error "tmux_setup.sh not found. Please run the setup first."
        exit 1
    fi
}

# Function to stop all sessions
stop_sessions() {
    print_header "Stopping OpenInterest TMUX Sessions"
    check_tmux
    
    # List of session names
    sessions=(
        "oi-scheduler"
        "oi-all-monitors"
        "oi-manual"
        "oi-logs"
        "oi-milk"
        "oi-h"
        "oi-more"
        "oi-sahara"
        "oi-dmc"
        "oi-mav"
        "oi-cudis"
    )
    
    for session in "${sessions[@]}"; do
        if tmux has-session -t "$session" 2>/dev/null; then
            print_status "Stopping session: $session"
            tmux kill-session -t "$session"
        else
            print_warning "Session $session not found"
        fi
    done
    
    print_status "All sessions stopped"
}

# Function to restart all sessions
restart_sessions() {
    print_header "Restarting OpenInterest TMUX Sessions"
    stop_sessions
    sleep 2
    start_sessions
}

# Function to show status
show_status() {
    print_header "OpenInterest TMUX Sessions Status"
    check_tmux
    
    echo ""
    echo "Active Sessions:"
    echo "================"
    
    if tmux list-sessions 2>/dev/null | grep -q "oi-"; then
        tmux list-sessions | grep "oi-" || echo "No active sessions found"
    else
        echo "No active sessions found"
    fi
    
    echo ""
    echo "Session Details:"
    echo "================"
    
    sessions=(
        "oi-scheduler:Main scheduler (runs every 15 minutes)"
        "oi-all-monitors:All individual token monitors"
        "oi-manual:Manual multi-token monitoring"
        "oi-logs:Log monitoring"
        "oi-milk:Monitor for MILK token"
        "oi-h:Monitor for H token"
        "oi-more:Monitor for MORE token"
        "oi-sahara:Monitor for SAHARA token"
        "oi-dmc:Monitor for DMC token"
        "oi-mav:Monitor for MAV token"
        "oi-cudis:Monitor for CUDIS token"
    )
    
    for session_info in "${sessions[@]}"; do
        IFS=':' read -r session_name description <<< "$session_info"
        if tmux has-session -t "$session_name" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $session_name - $description"
        else
            echo -e "  ${RED}✗${NC} $session_name - $description"
        fi
    done
}

# Function to attach to logs session
attach_logs() {
    check_tmux
    if tmux has-session -t "oi-logs" 2>/dev/null; then
        print_status "Attaching to logs session..."
        tmux attach-session -t "oi-logs"
    else
        print_error "Logs session not found. Run '$0 start' first."
        exit 1
    fi
}

# Function to attach to scheduler session
attach_scheduler() {
    check_tmux
    if tmux has-session -t "oi-scheduler" 2>/dev/null; then
        print_status "Attaching to scheduler session..."
        tmux attach-session -t "oi-scheduler"
    else
        print_error "Scheduler session not found. Run '$0 start' first."
        exit 1
    fi
}

# Function to attach to manual monitoring session
attach_manual() {
    check_tmux
    if tmux has-session -t "oi-manual" 2>/dev/null; then
        print_status "Attaching to manual monitoring session..."
        tmux attach-session -t "oi-manual"
    else
        print_error "Manual monitoring session not found. Run '$0 start' first."
        exit 1
    fi
}

# Function to attach to all monitors session
attach_all_monitors() {
    check_tmux
    if tmux has-session -t "oi-all-monitors" 2>/dev/null; then
        print_status "Attaching to all monitors session..."
        tmux attach-session -t "oi-all-monitors"
    else
        print_error "All monitors session not found. Run '$0 start' first."
        exit 1
    fi
}

# Function to list all sessions
list_sessions() {
    print_header "Available TMUX Sessions"
    check_tmux
    
    echo ""
    echo "Session Commands:"
    echo "================="
    echo "  ${YELLOW}tmux attach-session -t oi-scheduler${NC}  - Main scheduler"
    echo "  ${YELLOW}tmux attach-session -t oi-all-monitors${NC} - All token monitors"
    echo "  ${YELLOW}tmux attach-session -t oi-manual${NC}     - Manual monitoring"
    echo "  ${YELLOW}tmux attach-session -t oi-logs${NC}       - View logs"
    echo ""
    echo "Individual Token Sessions:"
    echo "========================="
    echo "  ${YELLOW}tmux attach-session -t oi-milk${NC}       - MILK token"
    echo "  ${YELLOW}tmux attach-session -t oi-h${NC}          - H token"
    echo "  ${YELLOW}tmux attach-session -t oi-more${NC}       - MORE token"
    echo "  ${YELLOW}tmux attach-session -t oi-sahara${NC}     - SAHARA token"
    echo "  ${YELLOW}tmux attach-session -t oi-dmc${NC}        - DMC token"
    echo "  ${YELLOW}tmux attach-session -t oi-mav${NC}        - MAV token"
    echo "  ${YELLOW}tmux attach-session -t oi-cudis${NC}      - CUDIS token"
    echo ""
    echo "Control Commands:"
    echo "================="
    echo "  ${YELLOW}tmux list-sessions${NC}                   - List all sessions"
    echo "  ${YELLOW}tmux kill-session -t <session>${NC}       - Kill specific session"
    echo "  ${YELLOW}tmux kill-server${NC}                     - Kill all sessions"
}

# Function to force kill all sessions
kill_sessions() {
    print_header "Force Killing All TMUX Sessions"
    check_tmux
    
    print_warning "This will force kill all tmux sessions!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        tmux kill-server
        print_status "All tmux sessions killed"
    else
        print_status "Operation cancelled"
    fi
}

# Main script logic
case "${1:-help}" in
    start)
        start_sessions
        ;;
    stop)
        stop_sessions
        ;;
    restart)
        restart_sessions
        ;;
    status)
        show_status
        ;;
    logs)
        attach_logs
        ;;
    scheduler)
        attach_scheduler
        ;;
    manual)
        attach_manual
        ;;
    all)
        attach_all_monitors
        ;;
    list)
        list_sessions
        ;;
    kill)
        kill_sessions
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