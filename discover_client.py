import socket
import time

DISCOVERY_PORT = 50000
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"
RESPONSE_MESSAGE = b"SERVER_HERE"
TIMEOUT = 5  # seconds

def discover_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(TIMEOUT)

    sock.sendto(DISCOVERY_MESSAGE, ('<broadcast>', DISCOVERY_PORT))
    print("[DISCOVERY] Broadcast message sent. Waiting for response...")

    try:
        while True:
            data, server_addr = sock.recvfrom(1024)
            if data == RESPONSE_MESSAGE:
                print(f"[DISCOVERY] Server found at {server_addr[0]}")
                return server_addr[0]
    except socket.timeout:
        print("[DISCOVERY] No server response received.")
        return None

if __name__ == "__main__":
    server_ip = discover_server()
    if server_ip:
        print(f"Use this IP to connect: {server_ip}")
    else:
        print("Server not found.")
