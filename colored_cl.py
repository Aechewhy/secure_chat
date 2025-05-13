import socket
import threading
import rsa
import sys
import shutil

# ANSI color codes
BLUE = '\033[34m'
RED = '\033[31m'
RESET = '\033[0m'

# ==== DISCOVERY CONFIG ====
DISCOVERY_PORT    = 50000
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"
DISCOVERY_TIMEOUT = 5

# Discover server via UDP broadcast
def discover_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(DISCOVERY_TIMEOUT)

    sock.sendto(DISCOVERY_MESSAGE, ('<broadcast>', DISCOVERY_PORT))
    print("[DISCOVERY] Broadcast sent, waiting for server response…")

    try:
        data, _ = sock.recvfrom(1024)
        server_ip = data.decode().strip()
        print(f"[DISCOVERY] Server IP: {server_ip}")
        return server_ip
    except socket.timeout:
        print("[DISCOVERY] No server response.")
        return None

# Thread for sending encrypted messages (exit confirmation)
def sending_messages(sock, public_partner):
    try:
        while True:
            msg = input("")
            if msg.lower() == "exit":
                confirm = input("Do you want to exit? (Y/N): ")
                if confirm.lower() == 'y':
                    sock.send(b"exit")
                    print("Disconnecting…")
                    raise SystemExit
                else:
                    continue
            ciphertext = rsa.encrypt(msg.encode(), public_partner)
            sock.send(ciphertext)
            print(f"{BLUE}You:{RESET} {msg}")
    except (SystemExit, KeyboardInterrupt):
        sock.close()
        raise

# Thread for receiving encrypted messages (right-aligned, colored)
def receiving_messages(sock, private_key):
    try:
        width = shutil.get_terminal_size((80, 20)).columns
        label = "Partner: "
        while True:
            data = sock.recv(4096)
            if not data or data == b"exit":
                print("Partner disconnected.")
                raise SystemExit
            plaintext = rsa.decrypt(data, private_key).decode()
            full = label + plaintext
            pad = max(width - len(full), 0)
            print(" " * pad + f"{RED}{label}{RESET}{plaintext}")
    except (SystemExit, KeyboardInterrupt):
        sock.close()
        raise

if __name__ == "__main__":
    # Generate keys and discover
    public_key, private_key = rsa.newkeys(1024)
    server_ip = discover_server()
    if not server_ip:
        sys.exit("Could not find server.")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, 9999))
    print(f"[TCP] Connected to {server_ip}:9999")

    # Exchange RSA public keys
    public_partner = rsa.PublicKey.load_pkcs1(client.recv(2048))
    client.send(public_key.save_pkcs1("PEM"))

    # Start chat threads\    
    t1 = threading.Thread(target=sending_messages,   args=(client, public_partner))
    t2 = threading.Thread(target=receiving_messages, args=(client, private_key))
    t1.start(); t2.start()
    t1.join();  t2.join()

    print("Client shutting down.")
    client.close()
    sys.exit()