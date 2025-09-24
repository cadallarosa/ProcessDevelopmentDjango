#!/bin/bash

# Django Stack Stop Script
echo "🛑 Stopping Django Stack..."

# Kill processes
echo "Stopping Django server..."
sudo pkill -f "runserver 0.0.0.0:8000" 2>/dev/null

echo "Stopping Node.js server..."
sudo pkill -f "server.js" 2>/dev/null

echo "Stopping Celery worker..."
sudo pkill -f "celery.*worker" 2>/dev/null

echo "Stopping Celery beat..."
sudo pkill -f "celery.*beat" 2>/dev/null

# Wait a moment
sleep 2

# Check if processes are stopped
echo ""
echo "📊 Checking process status..."
if pgrep -f "runserver 0.0.0.0:8000" > /dev/null; then
    echo "⚠️  Django still running"
else
    echo "✅ Django stopped"
fi

if pgrep -f "server.js" > /dev/null; then
    echo "⚠️  Node.js still running"
else
    echo "✅ Node.js stopped"
fi

if pgrep -f "celery.*worker" > /dev/null; then
    echo "⚠️  Celery worker still running"
else
    echo "✅ Celery worker stopped"
fi

if pgrep -f "celery.*beat" > /dev/null; then
    echo "⚠️  Celery beat still running"
else
    echo "✅ Celery beat stopped"
fi

echo ""
echo "🧹 All services stopped"