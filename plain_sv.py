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

# Get LAN IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Discovery responder thread
def handle_discovery():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", DISCOVERY_PORT))
    while True:
        data, addr = sock.recvfrom(1024)
        if data == DISCOVERY_MESSAGE:
            sock.sendto(get_local_ip().encode(), addr)

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
            # send plaintext
            data = msg.encode()
            conn.send(data)
            # display own message and timestamp
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

    threading.Thread(target=handle_discovery, daemon=True).start()
    ip = get_local_ip()
    print('Local IP Address:', ip)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, 9999))
    server.listen(1)
    conn, _ = server.accept()

    # exchange names
    conn.send(username.encode())
    partner_name = conn.recv(1024).decode()
    print(f"Chatting with {partner_name}")

    t1 = threading.Thread(target=sending_messages,   args=(conn, username))
    t2 = threading.Thread(target=receiving_messages, args=(conn, partner_name))
    t1.start(); t2.start()
    t1.join();  t2.join()

    print('Server shutting down.')
    server.close()
    sys.exit()
