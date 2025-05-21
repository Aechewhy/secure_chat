import socket
import threading
import sys
import shutil
from datetime import datetime
import custom_rsa  # your RSA module

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
    print(f"[DISCOVERY] Listening on UDP {DISCOVERY_PORT}…")
    while True:
        data, addr = sock.recvfrom(1024)
        if data == DISCOVERY_MESSAGE:
            sock.sendto(get_local_ip().encode(), addr)

# Sending thread: show encrypted bytes on sender screen
def sending_messages(conn, public_partner, username):
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
            # encrypt
            ciphertext = custom_rsa.encrypt(msg, public_partner)
            # display encrypted form
            print(f"Encrypted (hex): {ciphertext.hex()}")
            conn.send(ciphertext)
            # display own message with timestamp
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"{BLUE}<{timestamp}>{RESET}")
            print(f"{BLUE}{username}:{RESET} {msg}")
    finally:
        conn.close()
        sys.exit()

# Receiving thread
def receiving_messages(conn, private_key, partner_name):
    width = shutil.get_terminal_size((80,20)).columns
    try:
        while True:
            data = conn.recv(8192)
            if not data or data == b'exit':
                print(f"{partner_name} disconnected.")
                break
            plaintext = custom_rsa.decrypt(data, private_key)
            timestamp = datetime.now().strftime('%H:%M:%S')
            label = f"{partner_name} {timestamp}: "
            pad = max(width - len(label) - len(plaintext), 0)
            print(' ' * pad + f"{RED}{label}{RESET}{plaintext}")
    finally:
        conn.close()
        sys.exit()

if __name__ == '__main__':
    username = input('Enter your name: ')
    # Generate RSA keys once for this session
    public_key, private_key = custom_rsa.generate_keys(1024)

    threading.Thread(target=handle_discovery, daemon=True).start()
    ip = get_local_ip()
    print('Local IP Address:', ip)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, 9999))
    server.listen(1)
    print('[TCP] Waiting for connection on port 9999…')
    conn, _ = server.accept()

    # Exchange public keys
    conn.send(custom_rsa.save_pkcs1(public_key, 'public').encode())
    partner_pem = conn.recv(2048).decode()
    public_partner = custom_rsa.load_pkcs1(partner_pem, 'public')

    # Exchange names
    conn.send(username.encode())
    partner_name = conn.recv(1024).decode()
    print(f"Chatting with {partner_name}")

    # Start chat threads
    t1 = threading.Thread(target=sending_messages,   args=(conn, public_partner, username))
    t2 = threading.Thread(target=receiving_messages, args=(conn, private_key, partner_name))
    t1.start(); t2.start()
    t1.join();  t2.join()

    print('Server shutting down.')
    server.close()
    sys.exit()
