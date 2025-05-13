import socket
import threading
import rsa
import sys

# ==== DISCOVERY CONFIG ====
DISCOVERY_PORT = 50000
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"
RESPONSE_MESSAGE = b"SERVER_HERE"

# ==== RSA KEY SETUP ====
public_key, private_key = rsa.newkeys(1024)

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
    print(f"[DISCOVERY] Listening on UDP {DISCOVERY_PORT}...")
    while True:
        data, addr = sock.recvfrom(1024)
        if data == DISCOVERY_MESSAGE:
            print(f"[DISCOVERY] Responding to {addr}")
            sock.sendto(RESPONSE_MESSAGE, addr)

def sending_messages(c, public_partner):
    while True:
        msg = input("")
        if msg.lower() == "exit":
            c.send(b"exit")
            print("Disconnecting...")
            c.close()
            sys.exit()
        c.send(msg.encode())
        # c.send(rsa.encrypt(msg.encode(), public_partner))
        print("You: " + msg)

def receiving_messages(c):
    try:
        while True:
            data = c.recv(2048)
            if not data or data == b"exit":
                print("Partner disconnected.")
                break
            # print("Partner: " + c.recv(1024).decode())
            print("Partner: " + data.decode())
            # print("Partner: " + rsa.decrypt(data, private_key).decode())
    except:
        pass
    finally:
        c.close()
        sys.exit()

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("Local IP Address:", local_ip)

    # Start UDP discovery responder in background
    threading.Thread(target=handle_discovery, daemon=True).start()

    # Start TCP server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((local_ip, 9999))
    server.listen(1)
    print("[TCP] Waiting for connection on port 9999...")
    client, _ = server.accept()

    # Exchange public keys
    client.send(public_key.save_pkcs1("PEM"))
    public_partner = rsa.PublicKey.load_pkcs1(client.recv(2048))

    # Start chat
    threading.Thread(target=sending_messages, args=(client, public_partner), daemon=True).start()
    threading.Thread(target=receiving_messages, args=(client,), daemon=True).start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Server shutting down.")
        server.close()
        sys.exit()
