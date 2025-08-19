# Gunicorn HTTPS configuration for Django
import os
import multiprocessing

# Server socket - HTTPS on port 443
bind = "0.0.0.0:443"
backlog = 2048

# SSL Configuration
keyfile = "/etc/ssl/private/django.key"
certfile = "/etc/ssl/certs/django.crt"
# ca_certs = "/etc/ssl/certs/ca_bundle.crt"  # If you have intermediate certificates

# Security settings
ssl_version = 2  # Use TLS
ciphers = 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS'
do_handshake_on_connect = False

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeouts
timeout = 120
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "django_https_app"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True

# User/Group (run as non-root for security after binding to port 443)
# user = "www-data"
# group = "www-data"

print("🔒 Gunicorn HTTPS configuration loaded")
print(f"📍 Binding to: {bind}")
print(f"👥 Workers: {workers}")
print(f"🔐 SSL keyfile: {keyfile}")
print(f"📜 SSL certificate: {certfile}")