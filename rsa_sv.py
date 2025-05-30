import socket
import threading
import custom_rsa
import sys
import shutil
from datetime import datetime

# ANSI color codes
BLUE = '\033[34m'
RED = '\033[31m'
RESET = '\033[0m'

# ==== DISCOVERY CONFIG ====
DISCOVERY_PORT    = 50000
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"

def generate_keys():
    return custom_rsa.generate_keys(1024)

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

def sending_messages(conn, public_partner, username):
    try:
        while True:
            msg = input("")
            if msg.lower() == "exit":
                if input("Do you want to exit? (Y/N): ").lower() == 'y':
                    conn.send(b"exit")
                    print("Disconnecting…")
                    raise SystemExit
                else:
                    continue

            conn.send(custom_rsa.encrypt(msg, public_partner))

            # own messages: left-aligned
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"{BLUE}<{timestamp}>{RESET}")
            print(f"{BLUE}{username}:{RESET} {msg}")

    except (SystemExit, KeyboardInterrupt):
        conn.close()
        raise

def receiving_messages(conn, private_key, partner_name):
    try:
        while True:
            data = conn.recv(4096)
            if not data or data == b"exit":
                print(f"{partner_name} disconnected.")
                raise SystemExit

            plaintext = custom_rsa.decrypt(data, private_key)

            # partner messages: right-aligned
            width = shutil.get_terminal_size((80, 20)).columns
            timestamp = datetime.now().strftime("%H:%M:%S")
            ts_str = f"<{timestamp}>"
            msg_str = f"{partner_name}: {plaintext}"

            print(" " * (width - len(ts_str)) + f"{RED}{ts_str}{RESET}")
            print(" " * (width - len(msg_str)) + f"{RED}{partner_name}:{RESET} {plaintext}")

    except (SystemExit, KeyboardInterrupt):
        conn.close()
        raise

if __name__ == "__main__":
    username = input("Enter your name: ")
    public_key, private_key = generate_keys()
    threading.Thread(target=handle_discovery, daemon=True).start()

    local_ip = get_local_ip()
    print("Local IP Address:", local_ip)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((local_ip, 9999))
    server.listen(1)
    print("[TCP] Waiting for connection on port 9999…")

    conn, _ = server.accept()

    conn.send(custom_rsa.save_pkcs1(public_key, 'public').encode())
    public_partner = custom_rsa.load_pkcs1(conn.recv(2048).decode(), 'public')

    conn.send(username.encode())
    partner_name = conn.recv(1024).decode()
    print(f"Chatting with {partner_name}")

    t1 = threading.Thread(target=sending_messages, args=(conn, public_partner, username))
    t2 = threading.Thread(target=receiving_messages, args=(conn, private_key, partner_name))
    t1.start(); t2.start()
    t1.join(); t2.join()

    print("Server shutting down.")
    conn.close(); server.close()
    sys.exit()   
