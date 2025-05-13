import socket
import threading
import sys
import shutil

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
        print(f"[DISCOVERY] Server announced IP {server_ip}")
        return server_ip
    except socket.timeout:
        print("[DISCOVERY] No server response received.")
        return None

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
    server_ip = discover_server()
    if not server_ip:
        sys.exit("Could not find a server on the LAN.")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, 9999))
    print(f"[TCP] Connected to server at {server_ip}:9999")

    # Start chat threads
    t_send = threading.Thread(target=sending_messages,   args=(client,))
    t_recv = threading.Thread(target=receiving_messages, args=(client,))
    t_send.start(); t_recv.start()
    t_send.join();  t_recv.join()

    print("Client shutting down.")
    client.close()
    sys.exit()