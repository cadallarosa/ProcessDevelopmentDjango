#!/bin/bash

# SSL Certificate Setup for localhost development
echo "🔐 SSL Certificate Setup for Django/Gunicorn"
echo "=============================================="

# Create directories
sudo mkdir -p /etc/ssl/certs
sudo mkdir -p /etc/ssl/private
sudo mkdir -p /var/log/gunicorn

# Generate self-signed certificate for localhost
generate_localhost_cert() {
    echo "📝 Generating self-signed certificate for localhost..."

    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/django.key \
        -out /etc/ssl/certs/django.crt \
        -subj "/C=US/ST=California/L=City/O=Development/OU=IT/CN=localhost" \
        -extensions v3_req \
        -config <(cat << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = City
O = Development
OU = IT Department
CN = localhost

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = 127.0.0.1
DNS.3 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
)

    echo "✅ Self-signed certificate generated for localhost"
}

# Set proper permissions
set_permissions() {
    echo "🔒 Setting secure permissions..."

    sudo chmod 600 /etc/ssl/private/django.key
    sudo chmod 644 /etc/ssl/certs/django.crt
    sudo chown root:root /etc/ssl/private/django.key
    sudo chown root:root /etc/ssl/certs/django.crt

    # Create log directories
    sudo mkdir -p /var/log/gunicorn
    sudo chown $USER:$USER /var/log/gunicorn
    sudo chmod 755 /var/log/gunicorn

    echo "✅ Permissions set"
}

# Main execution
generate_localhost_cert
set_permissions

echo ""
echo "📋 Certificate Information:"
echo "   Certificate: /etc/ssl/certs/django.crt"
echo "   Private Key: /etc/ssl/private/django.key"
echo ""
echo "✅ SSL setup complete for localhost!"
echo ""
echo "🚀 Next step: Run deployment script"