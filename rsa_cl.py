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
DISCOVERY_TIMEOUT = 5

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
    public_key, private_key = custom_rsa.generate_keys(1024)

    server_ip = discover_server()
    if not server_ip:
        sys.exit("Could not find server.")

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((server_ip, 9999))
    print(f"[TCP] Connected to {server_ip}:9999")

    public_partner = custom_rsa.load_pkcs1(conn.recv(2048).decode(), 'public')
    conn.send(custom_rsa.save_pkcs1(public_key, 'public').encode())

    partner_name = conn.recv(1024).decode()
    conn.send(username.encode())
    print(f"Chatting with {partner_name}")

    t1 = threading.Thread(target=sending_messages, args=(conn, public_partner, username))
    t2 = threading.Thread(target=receiving_messages, args=(conn, private_key, partner_name))
    t1.start(); t2.start()
    t1.join(); t2.join()

    print("Client shutting down.")
    conn.close()
    sys.exit() 
