#!/bin/bash

# Django Stack Startup Script
echo "🚀 Starting Django Stack..."

# Define paths
PROJECT_DIR="/home/cdallarosa/home/cdallarosa/PycharmProjects"
VENV_PATH="$PROJECT_DIR/.venv/.venv"
OPCUA_DIR="$PROJECT_DIR/plotly_integration/process_development/downstream_processing/akta/opcua_server/opcua-browser"
NODE_PATH="/home/cdallarosa/.config/JetBrains/PyCharm2025.1/node/versions/22.15.1/bin/node"

# Kill any existing processes
echo "🔄 Stopping existing processes..."
sudo pkill -f "runserver 0.0.0.0:8000" 2>/dev/null
sudo pkill -f "server.js" 2>/dev/null
sudo pkill -f "celery.*worker" 2>/dev/null
sudo pkill -f "celery.*beat" 2>/dev/null
sleep 2

# Start Django server
echo "📦 Starting Django server on port 8000..."
cd "$PROJECT_DIR" && \
source "$VENV_PATH/bin/activate" && \
python manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &
DJANGO_PID=$!

## Start Node.js server
#echo "🌐 Starting Node.js server..."
#cd "$OPCUA_DIR" && \
#"$NODE_PATH" server.js > nodejs.log 2>&1 &
#NODEJS_PID=$!

# Start Celery worker
echo "👷 Starting Celery worker..."
cd "$PROJECT_DIR" && \
source "$VENV_PATH/bin/activate" && \
celery -A djangoProject worker --loglevel=info > celery-worker.log 2>&1 &
CELERY_WORKER_PID=$!

# Start Celery beat
echo "⏰ Starting Celery beat..."
cd "$PROJECT_DIR" && \
source "$VENV_PATH/bin/activate" && \
celery -A djangoProject beat --loglevel=info > celery-beat.log 2>&1 &
CELERY_BEAT_PID=$!

# Wait for services to start
sleep 3

# Check service status
echo ""
echo "📊 Service Status:"
if kill -0 $DJANGO_PID 2>/dev/null; then
    echo "✅ Django running on port 8000 (PID: $DJANGO_PID)"
else
    echo "❌ Django failed to start"
fi

if kill -0 $NODEJS_PID 2>/dev/null; then
    echo "✅ Node.js server running (PID: $NODEJS_PID)"
else
    echo "❌ Node.js failed to start"
fi

if kill -0 $CELERY_WORKER_PID 2>/dev/null; then
    echo "✅ Celery Worker running (PID: $CELERY_WORKER_PID)"
else
    echo "❌ Celery Worker failed to start"
fi

if kill -0 $CELERY_BEAT_PID 2>/dev/null; then
    echo "✅ Celery Beat running (PID: $CELERY_BEAT_PID)"
else
    echo "❌ Celery Beat failed to start"
fi

# Test Django port
echo ""
echo "🔌 Testing Django connection..."
sleep 2
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 2>/dev/null || echo "000")
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "301" ] || [ "$RESPONSE" = "302" ]; then
    echo "✅ Django is responding on http://localhost:8000"
else
    echo "⚠️  Django HTTP response code: $RESPONSE"
fi

echo ""
echo "📝 Log files created:"
echo "   - django.log"
echo "   - nodejs.log"
echo "   - celery-worker.log"
echo "   - celery-beat.log"
echo ""
echo "💡 To stop all services, run: ./stop_django_stack.sh"
echo "🔍 To view logs, use: tail -f <logfile>"