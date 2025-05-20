import socket
import threading
import sys
import shutil
from datetime import datetime

# ANSI color codes
BLUE = '\033[34m'
RED  = '\033[31m'
RESET= '\033[0m'

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
    try:
        data, _ = sock.recvfrom(1024)
        return data.decode().strip()
    except socket.timeout:
        return None

# Sending thread (plaintext)
def sending_messages(conn, username):
    try:
        while True:
            msg = input("")
            if msg.lower() == 'exit':
                if input("Do you want to exit? (Y/N): ").lower() == 'y':
                    conn.send(b'exit')
                    print("Disconnecting…")
                    break
                else:
                    continue
            data = msg.encode()
            conn.send(data)
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"{BLUE}<{timestamp}>{RESET}")
            print(f"{BLUE}{username}:{RESET} {msg}")
    finally:
        conn.close()
        sys.exit()

# Receiving thread (plaintext)
def receiving_messages(conn, partner_name):
    width = shutil.get_terminal_size((80,20)).columns
    try:
        while True:
            data = conn.recv(8192)
            if not data or data == b'exit':
                print(f"{partner_name} disconnected.")
                break
            plaintext = data.decode()
            timestamp = datetime.now().strftime('%H:%M:%S')
            label = f"{partner_name} {timestamp}: "
            pad = max(width - len(label) - len(plaintext), 0)
            print(' ' * pad + f"{RED}{label}{RESET}{plaintext}")
    finally:
        conn.close()
        sys.exit()

if __name__ == '__main__':
    username = input('Enter your name: ')

    server_ip = discover_server()
    if not server_ip:
        sys.exit("Could not find server.")
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((server_ip,9999))

    # exchange names
    partner_name = conn.recv(1024).decode()
    conn.send(username.encode())
    print(f"Chatting with {partner_name}")

    t1 = threading.Thread(target=sending_messages,   args=(conn, username))
    t2 = threading.Thread(target=receiving_messages, args=(conn, partner_name))
    t1.start(); t2.start()
    t1.join();  t2.join()

    print('Client shutting down.')
    conn.close()
    sys.exit()
