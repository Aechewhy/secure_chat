import socket
import threading
import rsa
import sys

DISCOVERY_PORT = 50000
DISCOVERY_MESSAGE = b"DISCOVER_SERVER"
RESPONSE_MESSAGE = b"SERVER_HERE"
DISCOVERY_TIMEOUT = 5  # seconds

public_key, private_key = rsa.newkeys(1024)

def discover_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(DISCOVERY_TIMEOUT)

    sock.sendto(DISCOVERY_MESSAGE, ('<broadcast>', DISCOVERY_PORT))
    print("[DISCOVERY] Broadcast sent, waiting for server response...")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            server_ip = data.decode().strip()
            print(f"[DISCOVERY] Server found at {server_ip}")
            return server_ip
    except socket.timeout:
        print("[DISCOVERY] No server response received.")
        return None


def sending_messages(c, public_partner):
    while True:
        msg = input("")
        if msg.lower() == "exit":
            c.send(b"exit")
            print("Disconnecting...")
            c.close()
            sys.exit()
        # c.send(rsa.encrypt(msg.encode(), public_partner))
        c.send(msg.encode())
        print("You: " + msg)

def receiving_messages(c):
    try:
        while True:
            data = c.recv(2048)
            if not data or data == b"exit":
                print("Partner disconnected.")
                break
            # print("Partner: " + rsa.decrypt(data, private_key).decode())
            print("Partner: " + data.decode())  # ✅ Display plain text
    except:
        pass
    finally:
        c.close()
        sys.exit()

if __name__ == "__main__":
    server_ip = discover_server()
    if not server_ip:
        sys.exit("Could not find a server.")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, 9999))

    public_partner = rsa.PublicKey.load_pkcs1(client.recv(2048))
    client.send(public_key.save_pkcs1("PEM"))

    threading.Thread(target=sending_messages, args=(client, public_partner), daemon=True).start()
    threading.Thread(target=receiving_messages, args=(client,), daemon=True).start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Client shutting down.")
        client.close()
        sys.exit()
