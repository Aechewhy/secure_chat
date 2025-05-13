### server.py
import socket
import threading
import rsa
import sys

# ==== DISCOVERY CONFIG ====
DISCOVERY_PORT = 50000
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"
RESPONSE_MESSAGE = b"SERVER_HERE"

# ==== RSA KEY SETUP ====
public_key, private_key = rsa.newkeys(1024)

# Function to get local IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Discovery responder thread
def handle_discovery():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", DISCOVERY_PORT))
    print(f"[DISCOVERY] Listening on UDP {DISCOVERY_PORT}...")
    while True:
        data, addr = sock.recvfrom(1024)
        if data == DISCOVERY_MESSAGE:
            print(f"[DISCOVERY] Responding to {addr}")
            sock.sendto(RESPONSE_MESSAGE, addr)

# Thread for sending plaintext messages (exit handling)
def sending_messages(c, public_partner=None):
    try:
        while True:
            msg = input("")
            if msg.lower() == "exit":
                c.send(b"exit")
                print("Disconnecting...")
                raise SystemExit
            c.send(msg.encode())
            print("You: " + msg)
    except (SystemExit, KeyboardInterrupt):
        c.close()
        raise

# Thread for receiving plaintext messages (exit handling)
def receiving_messages(c):
    try:
        while True:
            data = c.recv(2048)
            if not data or data == b"exit":
                print("Partner disconnected.")
                raise SystemExit
            print("Partner: " + data.decode())
    except (SystemExit, KeyboardInterrupt):
        c.close()
        raise

if __name__ == "__main__":
    # Print local IP
    local_ip = get_local_ip()
    print("Local IP Address:", local_ip)

    # Start discovery responder
    discovery_thread = threading.Thread(target=handle_discovery, daemon=True)
    discovery_thread.start()

    # Start TCP server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((local_ip, 9999))
    server.listen(1)
    print("[TCP] Waiting for connection on port 9999...")
    client, _ = server.accept()

    # Exchange RSA keys
    client.send(public_key.save_pkcs1("PEM"))
    public_partner = rsa.PublicKey.load_pkcs1(client.recv(2048))

    # Start chat threads
    t_send = threading.Thread(target=sending_messages, args=(client, public_partner))
    t_recv = threading.Thread(target=receiving_messages, args=(client,))
    t_send.start()
    t_recv.start()

    # Wait for threads to finish
    t_send.join()
    t_recv.join()

    print("Server shutting down.")
    server.close()