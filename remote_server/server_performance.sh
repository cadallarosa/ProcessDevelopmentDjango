#!/bin/bash

# Server Performance Monitor
echo "======================================"
echo "🖥️  SERVER PERFORMANCE MONITOR"
echo "======================================"
echo "📅 $(date)"
echo ""

# System Information
echo "📊 SYSTEM INFORMATION"
echo "-------------------------------------"
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo "Uptime:$(uptime -p)"
echo ""

# CPU Information
echo "🔧 CPU INFORMATION"
echo "-------------------------------------"
echo "CPU Model: $(lscpu | grep 'Model name' | cut -d':' -f2 | xargs)"
echo "CPU Cores: $(nproc)"
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "  Total: " 100 - $1"%"}'
echo ""

# Memory Usage
echo "💾 MEMORY USAGE"
echo "-------------------------------------"
free -h | grep -E "^Mem|^Swap" | while read line; do
    echo "  $line"
done
echo ""
echo "Memory Details:"
free -m | awk 'NR==2{printf "  Used: %.1f%% (%sMB / %sMB)\n", $3*100/$2, $3, $2}'
echo ""

# Disk Usage
echo "💿 DISK USAGE"
echo "-------------------------------------"
df -h | grep -E '^/dev/' | while read line; do
    echo "  $line"
done
echo ""

# Load Average
echo "📈 LOAD AVERAGE"
echo "-------------------------------------"
echo "  $(uptime | awk -F'load average:' '{print $2}')"
echo ""

# Process Information
echo "⚙️  TOP PROCESSES (by CPU)"
echo "-------------------------------------"
ps aux --sort=-%cpu | head -6 | awk '{printf "  %-10s %5s%% %5s%% %s\n", $1, $3, $4, $11}'
echo ""

echo "⚙️  TOP PROCESSES (by Memory)"
echo "-------------------------------------"
ps aux --sort=-%mem | head -6 | awk '{printf "  %-10s %5s%% %5s%% %s\n", $1, $3, $4, $11}'
echo ""

# Network Connections
echo "🌐 NETWORK STATISTICS"
echo "-------------------------------------"
echo "Active Connections:"
ss -tun | tail -n +2 | wc -l | xargs echo "  Total:"
ss -tun | tail -n +2 | grep ESTAB | wc -l | xargs echo "  Established:"
ss -tun | tail -n +2 | grep LISTEN | wc -l | xargs echo "  Listening:"
echo ""

# Django Stack Status
echo "🚀 DJANGO STACK STATUS"
echo "-------------------------------------"
if pgrep -f "runserver" > /dev/null; then
    echo "  ✅ Django: Running (PID: $(pgrep -f 'runserver' | head -1))"
else
    echo "  ❌ Django: Not Running"
fi

if pgrep -f "celery.*worker" > /dev/null; then
    echo "  ✅ Celery Worker: Running (PID: $(pgrep -f 'celery.*worker' | head -1))"
else
    echo "  ❌ Celery Worker: Not Running"
fi

if pgrep -f "celery.*beat" > /dev/null; then
    echo "  ✅ Celery Beat: Running (PID: $(pgrep -f 'celery.*beat' | head -1))"
else
    echo "  ❌ Celery Beat: Not Running"
fi

if pgrep -f "server.js" > /dev/null; then
    echo "  ✅ Node.js: Running (PID: $(pgrep -f 'server.js' | head -1))"
else
    echo "  ❌ Node.js: Not Running"
fi
echo ""

# Port Check
echo "🔌 PORT STATUS"
echo "-------------------------------------"
for port in 8000 3000 5432 6379; do
    if ss -tln | grep -q ":$port "; then
        echo "  ✅ Port $port: Open"
    else
        echo "  ❌ Port $port: Closed"
    fi
done
echo ""

echo "======================================"
echo "📊 Performance check complete!"
echo "======================================"