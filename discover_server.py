import socket
import threading

DISCOVERY_PORT = 50000
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"
RESPONSE_MESSAGE = b"SERVER_HERE"

def handle_discovery():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", DISCOVERY_PORT))
    print(f"[DISCOVERY] Listening for discovery messages on UDP {DISCOVERY_PORT}...")

    while True:
        data, addr = sock.recvfrom(1024)
        if data == DISCOVERY_MESSAGE:
            print(f"[DISCOVERY] Received discovery request from {addr}")
            sock.sendto(RESPONSE_MESSAGE, addr)

if __name__ == "__main__":
    threading.Thread(target=handle_discovery, daemon=True).start()

    print("Server discovery service started. Ready for TCP connections.")
    input("Press Enter to exit.\n")
