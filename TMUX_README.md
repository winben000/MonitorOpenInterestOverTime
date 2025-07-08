# OpenInterest TMUX Setup Guide

This guide explains how to set up and use tmux to run the OpenInterest monitor automatically in the background.

## What is TMUX?

TMUX (Terminal Multiplexer) allows you to run multiple terminal sessions that persist even when you disconnect from your server. This is perfect for running the OpenInterest monitor continuously.

## Prerequisites

1. **Install TMUX** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tmux
   
   # macOS
   brew install tmux
   
   # CentOS/RHEL
   sudo yum install tmux
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your environment**:
   - Set up your `.env` file with API keys
   - Configure your token monitoring files

## Quick Start

### 1. Initial Setup

Run the tmux setup script to create all necessary sessions:

```bash
chmod +x tmux_setup.sh
./tmux_setup.sh
```

This will:
- Install Python dependencies
- Create multiple tmux sessions for different monitoring scenarios
- Start the main scheduler automatically

### 2. Using the Control Script

The `tmux_control.sh` script provides easy commands to manage your sessions:

```bash
chmod +x tmux_control.sh

# Start all sessions
./tmux_control.sh start

# Check status
./tmux_control.sh status

# View logs
./tmux_control.sh logs

# Stop all sessions
./tmux_control.sh stop
```

## Available Sessions

### Main Sessions

| Session Name | Description | Command |
|--------------|-------------|---------|
| `oi-scheduler` | Main scheduler (runs every 15 minutes) | `./tmux_control.sh scheduler` |
| `oi-all-monitors` | All individual token monitors | `./tmux_control.sh all` |
| `oi-manual` | Manual multi-token monitoring | `./tmux_control.sh manual` |
| `oi-logs` | Real-time log monitoring | `./tmux_control.sh logs` |

### Individual Token Sessions

| Session Name | Token | Config File |
|--------------|-------|-------------|
| `oi-milk` | MILK | `milk.json` |
| `oi-h` | H | `h.json` |
| `oi-more` | MORE | `more.json` |
| `oi-sahara` | SAHARA | `sahara.json` |
| `oi-dmc` | DMC | `dmc.json` |
| `oi-mav` | MAV | `mav.json` |
| `oi-cudis` | CUDIS | `cudis.json` |

## Control Commands

### Basic Commands

```bash
# Start all sessions
./tmux_control.sh start

# Stop all sessions
./tmux_control.sh stop

# Restart all sessions
./tmux_control.sh restart

# Check status of all sessions
./tmux_control.sh status

# List all available sessions
./tmux_control.sh list
```

### Attaching to Sessions

```bash
# Attach to main scheduler
./tmux_control.sh scheduler

# Attach to logs
./tmux_control.sh logs

# Attach to manual monitoring
./tmux_control.sh manual

# Attach to all monitors
./tmux_control.sh all
```

### Force Operations

```bash
# Force kill all sessions
./tmux_control.sh kill
```

## Manual TMUX Commands

If you prefer to use tmux directly:

### List Sessions
```bash
tmux list-sessions
```

### Attach to a Session
```bash
tmux attach-session -t oi-scheduler
```

### Detach from Session
```
Ctrl+B, then D
```

### Kill a Session
```bash
tmux kill-session -t oi-scheduler
```

### Kill All Sessions
```bash
tmux kill-server
```

## Session Management

### Detaching and Reconnecting

1. **Detach from a session**: Press `Ctrl+B`, then `D`
2. **Reconnect to a session**: `tmux attach-session -t oi-scheduler`
3. **List all sessions**: `tmux list-sessions`

### Multiple Windows

Each session can have multiple windows:
- `Ctrl+B, C` - Create new window
- `Ctrl+B, N` - Next window
- `Ctrl+B, P` - Previous window
- `Ctrl+B, <number>` - Switch to window number

### Splitting Panes

- `Ctrl+B, %` - Split vertically
- `Ctrl+B, "` - Split horizontally
- `Ctrl+B, arrow keys` - Navigate between panes

## Monitoring and Logs

### Viewing Logs

The `oi-logs` session shows real-time logs:
```bash
./tmux_control.sh logs
```

This will show:
- `open_interest_monitor.log` - Main monitoring logs
- `scheduler.log` - Scheduler activity logs

### Checking Status

To see which sessions are running:
```bash
./tmux_control.sh status
```

This shows:
- ✓ Active sessions
- ✗ Inactive sessions

## Troubleshooting

### Common Issues

1. **Session not found**
   ```bash
   # Recreate all sessions
   ./tmux_control.sh restart
   ```

2. **Python dependencies missing**
   ```bash
   pip install -r requirements.txt
   ```

3. **Permission denied**
   ```bash
   chmod +x tmux_setup.sh tmux_control.sh
   ```

4. **TMUX not installed**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tmux
   ```

### Log Locations

- Main logs: `open_interest_monitor.log`
- Scheduler logs: `scheduler.log`
- TMUX logs: Check with `tmux list-sessions`

### Restarting Services

If you need to restart everything:
```bash
./tmux_control.sh stop
sleep 5
./tmux_control.sh start
```

## Advanced Configuration

### Custom Session Names

You can modify `tmux_setup.sh` to change session names or add new sessions.

### Environment Variables

Make sure your `.env` file is properly configured:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TOPIC_ID=your_topic_id
```

### Monitoring Intervals

The scheduler runs every 15 minutes by default. You can modify this in `scheduler.py`.

## Security Considerations

1. **API Keys**: Store API keys in `.env` file, not in scripts
2. **Permissions**: Use appropriate file permissions
3. **Network**: Ensure your server can access required APIs
4. **Logs**: Monitor logs for any security issues

## Support

If you encounter issues:

1. Check the logs: `./tmux_control.sh logs`
2. Check status: `./tmux_control.sh status`
3. Restart services: `./tmux_control.sh restart`
4. Review the main README.md for general troubleshooting

## Quick Reference

| Action | Command |
|--------|---------|
| Start everything | `./tmux_control.sh start` |
| View logs | `./tmux_control.sh logs` |
| Check status | `./tmux_control.sh status` |
| Stop everything | `./tmux_control.sh stop` |
| Restart | `./tmux_control.sh restart` |
| Manual monitoring | `./tmux_control.sh manual` |
| Scheduler | `./tmux_control.sh scheduler` | 