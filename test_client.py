import socket
import threading
import rsa
import sys

DISCOVERY_PORT = 50000
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"
RESPONSE_MESSAGE = b"SERVER_HERE"
DISCOVERY_TIMEOUT = 5  # seconds

public_key, private_key = rsa.newkeys(1024)

# Discover server via UDP broadcast
def discover_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(DISCOVERY_TIMEOUT)
    sock.sendto(DISCOVERY_MESSAGE, ('<broadcast>', DISCOVERY_PORT))
    print("[DISCOVERY] Broadcast sent, waiting for server response...")
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            if data == RESPONSE_MESSAGE:
                print(f"[DISCOVERY] Server found at {addr[0]}")
                return addr[0]
    except socket.timeout:
        print("[DISCOVERY] No server response received.")
        return None

# Thread for sending plaintext messages
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

# Thread for receiving plaintext messages
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
    server_ip = discover_server()
    if not server_ip:
        sys.exit("Could not find a server.")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, 9999))

    # Exchange RSA keys
    public_partner = rsa.PublicKey.load_pkcs1(client.recv(2048))
    client.send(public_key.save_pkcs1("PEM"))

    # Start chat threads
    t_send = threading.Thread(target=sending_messages, args=(client, public_partner))
    t_recv = threading.Thread(target=receiving_messages, args=(client,))
    t_send.start()
    t_recv.start()

    # Wait for threads to finish
    t_send.join()
    t_recv.join()

    print("Client shutting down.")
    client.close()
    sys.exit()