# Business MCP Server - Cron Job Setup (Linux/Mac)
# ============================================================
# This script sets up automatic startup of the Business MCP Server
# using cron (Linux/Mac task scheduler).
#
# Usage:
#   ./setup_cron.sh install    - Install cron jobs
#   ./setup_cron.sh uninstall  - Remove cron jobs
#   ./setup_cron.sh status     - Show cron status
# ============================================================

#!/bin/bash

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="$SCRIPT_DIR/server.py"
LOG_FILE="$SCRIPT_DIR/mcp_server.log"
CRON_LOG="/tmp/business_mcp_cron.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python not found. Please install Python 3.8+"
        exit 1
    fi
    
    log_info "Using Python: $PYTHON_CMD"
}

# Install cron jobs
install_cron() {
    log_info "Installing Business MCP Server cron jobs..."
    
    # Create startup script
    cat > "$SCRIPT_DIR/start_server.sh" << 'EOF'
#!/bin/bash
# Business MCP Server Startup Script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Start server
python server.py >> mcp_server.log 2>&1
EOF
    
    chmod +x "$SCRIPT_DIR/start_server.sh"
    log_info "Created startup script: $SCRIPT_DIR/start_server.sh"
    
    # Create cron entry for startup (on boot)
    CRON_ENTRY="@reboot $SCRIPT_DIR/start_server.sh"
    
    # Add to crontab
    (crontab -l 2>/dev/null | grep -v "$SCRIPT_DIR"; echo "$CRON_ENTRY") | crontab -
    
    if [ $? -eq 0 ]; then
        log_info "✓ Cron job installed successfully"
        log_info "  Server will start automatically on system boot"
    else
        log_error "✗ Failed to install cron job"
        log_warn "  Run 'crontab -e' to manually add:"
        log_warn "  $CRON_ENTRY"
    fi
    
    # Show instructions
    echo ""
    echo "============================================================"
    echo "Installation Complete!"
    echo "============================================================"
    echo ""
    echo "The Business MCP Server will now:"
    echo "  • Start automatically when the system boots"
    echo "  • Log output to: $LOG_FILE"
    echo ""
    echo "To view logs:"
    echo "  tail -f $LOG_FILE"
    echo ""
    echo "To manage cron jobs:"
    echo "  crontab -e  (edit)"
    echo "  crontab -l  (list)"
    echo "  crontab -r  (remove all)"
    echo ""
}

# Uninstall cron jobs
uninstall_cron() {
    log_info "Removing Business MCP Server cron jobs..."
    
    # Remove from crontab
    (crontab -l 2>/dev/null | grep -v "$SCRIPT_DIR") | crontab -
    
    if [ $? -eq 0 ]; then
        log_info "✓ Cron jobs removed successfully"
    else
        log_warn "No cron jobs found"
    fi
    
    # Remove startup script
    if [ -f "$SCRIPT_DIR/start_server.sh" ]; then
        rm "$SCRIPT_DIR/start_server.sh"
        log_info "✓ Removed startup script"
    fi
    
    echo ""
    log_info "Uninstallation complete!"
    echo ""
}

# Show status
show_status() {
    echo ""
    echo "============================================================"
    echo "Business MCP Server - Cron Status"
    echo "============================================================"
    echo ""
    
    # Check Python
    check_python
    
    # Check server script
    if [ -f "$SERVER_SCRIPT" ]; then
        log_info "✓ Server script found: $SERVER_SCRIPT"
    else
        log_error "✗ Server script not found: $SERVER_SCRIPT"
    fi
    
    # Check cron jobs
    echo ""
    echo "Current cron jobs for this script:"
    crontab -l 2>/dev/null | grep "$SCRIPT_DIR" || echo "  No cron jobs found"
    
    # Check if server is running
    echo ""
    echo "Server processes:"
    pgrep -f "python.*server.py" > /dev/null
    if [ $? -eq 0 ]; then
        log_info "✓ Server is running"
        ps aux | grep "python.*server.py" | grep -v grep | head -3
    else
        log_warn "Server is not running"
    fi
    
    # Show recent logs
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "Recent log entries:"
        echo "------------------------------------------------------------"
        tail -10 "$LOG_FILE"
    else
        echo ""
        log_warn "No log file found yet"
    fi
    
    echo ""
    echo "============================================================"
}

# Show help
show_help() {
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install    - Install cron jobs for automatic startup"
    echo "  uninstall  - Remove cron jobs"
    echo "  status     - Show current status"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 install"
    echo "  $0 uninstall"
    echo "  $0 status"
    echo ""
}

# Main
case "${1:-}" in
    install)
        check_python
        install_cron
        ;;
    uninstall)
        uninstall_cron
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac

exit 0
