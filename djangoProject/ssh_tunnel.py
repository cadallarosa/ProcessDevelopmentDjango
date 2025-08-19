import paramiko
import threading
import time
from sshtunnel import SSHTunnelForwarder

# SSH CONFIGURATION
SSH_HOST = "10.0.0.235"  # Change to your actual SSH server address
SSH_PORT = 22
SSH_USER = "cdallarosa"
SSH_PASSWORD = "cdallarosa"  # Use key-based authentication instead for security

# MYSQL CONFIGURATION
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
LOCAL_PORT = 3306  # Local port to forward MySQL

server = None  # To store the SSH tunnel instance


def create_ssh_tunnel():
    global server
    try:
        server = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASSWORD,  # Replace with ssh_pkey for key auth
            remote_bind_address=(MYSQL_HOST, MYSQL_PORT),
            local_bind_address=("127.0.0.1", LOCAL_PORT),
        )
        server.start()
        print(f"SSH Tunnel Opened: 127.0.0.1:{LOCAL_PORT} -> {MYSQL_HOST}:{MYSQL_PORT}")

        # Keep the tunnel alive
        while True:
            time.sleep(10)

    except Exception as e:
        print(f"SSH Tunnel Error: {e}")


# Run the SSH tunnel in a separate thread so Django can continue running
def start_ssh_tunnel():
    ssh_thread = threading.Thread(target=create_ssh_tunnel, daemon=True)
    ssh_thread.start()
