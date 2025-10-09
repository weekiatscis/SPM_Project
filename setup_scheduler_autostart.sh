#!/bin/bash
#
# Auto-start Notification Scheduler Setup Script
# This sets up the notification scheduler to run automatically on system boot
#

set -e  # Exit on error

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_FILE="$HOME/Library/LaunchAgents/com.spm.notification_scheduler.plist"
PYTHON_PATH=$(which python3)

echo "======================================================================"
echo "SPM Notification Scheduler - Auto-start Setup"
echo "======================================================================"
echo ""
echo "This will configure the notification scheduler to:"
echo "  - Start automatically when you log in"
echo "  - Keep running in the background"
echo "  - Check for task reminders every hour"
echo "  - Restart automatically if it crashes"
echo ""
echo "Project directory: $PROJECT_DIR"
echo "Python path: $PYTHON_PATH"
echo ""

# Create logs directory
echo "1️⃣ Creating logs directory..."
mkdir -p "$PROJECT_DIR/logs"
echo "   ✅ Created: $PROJECT_DIR/logs"
echo ""

# Create LaunchAgent plist file
echo "2️⃣ Creating LaunchAgent configuration..."
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.spm.notification_scheduler</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$PROJECT_DIR/src/microservices/notifications/notification_scheduler.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/notification_scheduler.log</string>

    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/notification_scheduler_error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

echo "   ✅ Created: $PLIST_FILE"
echo ""

# Unload if already loaded
echo "3️⃣ Checking if scheduler is already running..."
if launchctl list | grep -q com.spm.notification_scheduler; then
    echo "   ⚠️  Scheduler already loaded. Unloading first..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    sleep 1
fi
echo "   ✅ Ready to load"
echo ""

# Load the LaunchAgent
echo "4️⃣ Starting notification scheduler..."
launchctl load "$PLIST_FILE"
sleep 2
echo "   ✅ Scheduler started!"
echo ""

# Verify it's running
echo "5️⃣ Verifying scheduler status..."
if launchctl list | grep -q com.spm.notification_scheduler; then
    echo "   ✅ Scheduler is running!"

    # Show PID if available
    PID=$(launchctl list | grep com.spm.notification_scheduler | awk '{print $1}')
    if [ "$PID" != "-" ]; then
        echo "   Process ID: $PID"
    fi
else
    echo "   ❌ Scheduler failed to start!"
    echo "   Check error log: $PROJECT_DIR/logs/notification_scheduler_error.log"
    exit 1
fi
echo ""

echo "======================================================================"
echo "✅ SETUP COMPLETE!"
echo "======================================================================"
echo ""
echo "The notification scheduler is now running and will:"
echo "  ✓ Start automatically when you log in"
echo "  ✓ Check for task reminders every hour"
echo "  ✓ Send email notifications based on reminder schedules"
echo "  ✓ Restart automatically if it crashes"
echo ""
echo "📊 Monitoring:"
echo "  View logs:        tail -f $PROJECT_DIR/logs/notification_scheduler.log"
echo "  View errors:      tail -f $PROJECT_DIR/logs/notification_scheduler_error.log"
echo "  Check status:     launchctl list | grep spm"
echo ""
echo "🔧 Management:"
echo "  Stop scheduler:   launchctl unload $PLIST_FILE"
echo "  Start scheduler:  launchctl load $PLIST_FILE"
echo "  Restart:          launchctl unload $PLIST_FILE && launchctl load $PLIST_FILE"
echo ""
echo "======================================================================"
echo ""
echo "⏳ Waiting 5 seconds to check for initial activity..."
sleep 5

if [ -f "$PROJECT_DIR/logs/notification_scheduler.log" ]; then
    echo ""
    echo "📋 Recent Activity:"
    echo "----------------------------------------------------------------------"
    tail -10 "$PROJECT_DIR/logs/notification_scheduler.log"
    echo "----------------------------------------------------------------------"
else
    echo ""
    echo "⚠️  No log file yet. The scheduler may take a moment to start."
    echo "   Check again in a few seconds: tail -f $PROJECT_DIR/logs/notification_scheduler.log"
fi

echo ""
echo "✨ All done! Your notification system is ready! ✨"
echo ""
