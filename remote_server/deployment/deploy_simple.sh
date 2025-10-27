#!/bin/bash

# Simple Django HTTPS Deployment with Direct Gunicorn
echo "🚀 Simple Django HTTPS Deployment"
echo "=================================="

# Configuration - YOUR SPECIFIC PATH
PROJECT_PATH="/home/cdallarosa/home/cdallarosa/PycharmProjects"
DOMAIN_NAME="localhost"  # Using localhost for development

# Function to install requirements
install_requirements() {
    echo "📦 Installing requirements..."
    cd $PROJECT_PATH
    source venv/bin/activate
    pip install gunicorn
    echo "✅ Requirements installed"
}

# Function to prepare Django
prepare_django() {
    echo "🎯 Preparing Django..."
    cd $PROJECT_PATH
    source venv/bin/activate

    # Create logs directory
    mkdir -p logs

    # Collect static files
    python manage.py collectstatic --noinput --settings=djangoProject.settings_production

    # Run migrations
    python manage.py migrate --settings=djangoProject.settings_production

    echo "✅ Django prepared"
}

# Function to configure firewall
configure_firewall() {
    echo "🔥 Configuring firewall..."
    sudo ufw allow 443/tcp
    sudo ufw allow 80/tcp
    sudo ufw --force enable
    echo "✅ Firewall configured"
}

# Function to start application
start_application() {
    echo "🎬 Starting Django application..."
    cd $PROJECT_PATH
    source venv/bin/activate

    echo "🔒 Starting Gunicorn on HTTPS port 443..."
    echo "🌐 Your app will be available at: https://localhost"
    echo "🌐 Or: https://127.0.0.1"
    echo ""
    echo "📋 To stop: Press Ctrl+C"
    echo ""

    # Start Gunicorn with HTTPS
    sudo $PROJECT_PATH/venv/bin/gunicorn \
        -c djangoProject/gunicorn_config.py \
        --env DJANGO_SETTINGS_MODULE=djangoProject.settings_production \
        djangoProject.wsgi:application
}

# Function to create systemd service
create_service() {
    echo "⚙️ Creating systemd service..."

    sudo tee /etc/systemd/system/django-https.service > /dev/null << EOF
[Unit]
Description=Django HTTPS Application
After=network.target

[Service]
Type=notify
User=root
Group=root
WorkingDirectory=$PROJECT_PATH
Environment=PATH=$PROJECT_PATH/venv/bin
Environment=DJANGO_SETTINGS_MODULE=djangoProject.settings_production
ExecStart=$PROJECT_PATH/venv/bin/gunicorn -c djangoProject/gunicorn_config.py djangoProject.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable django-https.service

    echo "✅ Systemd service created"
    echo "🎬 Start with: sudo systemctl start django-https"
    echo "📊 Status: sudo systemctl status django-https"
    echo "📋 Logs: sudo journalctl -u django-https -f"
}

# Main execution
main() {
    echo "🔧 Configuration:"
    echo "📁 Project Path: $PROJECT_PATH"
    echo "🌐 Domain: $DOMAIN_NAME"
    echo ""

    read -p "❓ Continue? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "❌ Cancelled"
        exit 1
    fi

    install_requirements
    prepare_django
    configure_firewall

    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "Choose how to run:"
    echo "1) Start now (foreground)"
    echo "2) Create systemd service (background)"
    read -p "Enter choice (1 or 2): " run_choice

    case $run_choice in
        1)
            start_application
            ;;
        2)
            create_service
            echo "🎬 Start the service: sudo systemctl start django-https"
            ;;
        *)
            echo "❌ Invalid choice"
            exit 1
            ;;
    esac
}

# Check if running as root for port 443
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script needs root access to bind to port 443"
    echo "   Run with: sudo $0"
    exit 1
fi

main