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

# RSA key generation
def generate_keys():
    return rsa.newkeys(1024)

# Get LAN IP
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
    print(f"[DISCOVERY] Listening on UDP {DISCOVERY_PORT}…")
    while True:
        data, addr = sock.recvfrom(1024)
        if data == DISCOVERY_MESSAGE:
            ip = get_local_ip().encode()
            print(f"[DISCOVERY] Replying to {addr} with {ip.decode()}")
            sock.sendto(ip, addr)

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
    # Prepare keys and discovery
    public_key, private_key = generate_keys()
    threading.Thread(target=handle_discovery, daemon=True).start()

    # Start TCP server
    local_ip = get_local_ip()
    print("Local IP Address:", local_ip)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((local_ip, 9999))
    server.listen(1)
    print("[TCP] Waiting for connection on port 9999…")
    conn, _ = server.accept()

    # Exchange RSA public keys
    conn.send(public_key.save_pkcs1("PEM"))
    public_partner = rsa.PublicKey.load_pkcs1(conn.recv(2048))

    # Start chat threads\    
    t1 = threading.Thread(target=sending_messages,   args=(conn, public_partner))
    t2 = threading.Thread(target=receiving_messages, args=(conn, private_key))
    t1.start(); t2.start()
    t1.join();  t2.join()

    print("Server shutting down.")
    conn.close(); server.close()
    sys.exit()