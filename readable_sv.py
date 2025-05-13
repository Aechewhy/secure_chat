import socket
import threading
import sys
import shutil

# ==== DISCOVERY CONFIG ====
DISCOVERY_PORT    = 50000
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"

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
    print(f"[DISCOVERY] Listening on UDP {DISCOVERY_PORT}…")
    while True:
        data, addr = sock.recvfrom(1024)
        if data == DISCOVERY_MESSAGE:
            server_ip = get_local_ip().encode()
            print(f"[DISCOVERY] Got ping from {addr}; replying with {server_ip.decode()}")
            sock.sendto(server_ip, addr)

# Thread for sending plaintext messages (exit confirmation)
def sending_messages(sock):
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
            sock.send(msg.encode())
            print("You: " + msg)
    except (SystemExit, KeyboardInterrupt):
        sock.close()
        raise

# Thread for receiving plaintext messages (right-aligned)
def receiving_messages(sock):
    try:
        width = shutil.get_terminal_size((80, 20)).columns
        while True:
            data = sock.recv(2048)
            if not data or data == b"exit":
                print("Partner disconnected.")
                raise SystemExit
            text = "Partner: " + data.decode()
            print(text.rjust(width))
    except (SystemExit, KeyboardInterrupt):
        sock.close()
        raise

if __name__ == "__main__":
    # Print local IP and start discovery
    local_ip = get_local_ip()
    print("Local IP Address:", local_ip)
    threading.Thread(target=handle_discovery, daemon=True).start()

    # Start TCP server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((local_ip, 9999))
    server.listen(1)
    print("[TCP] Waiting for connection on port 9999…")
    conn, _ = server.accept()

    # Start chat threads\    
    t_send = threading.Thread(target=sending_messages,   args=(conn,))
    t_recv = threading.Thread(target=receiving_messages, args=(conn,))
    t_send.start(); t_recv.start()
    t_send.join();  t_recv.join()

    print("Server shutting down.")
    conn.close(); server.close()
    sys.exit()