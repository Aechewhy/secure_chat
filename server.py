import socket
import threading
import rsa
import sys

# Function to get local IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Generate RSA key pair
public_key, private_key = rsa.newkeys(1024)

# Determine and print host IP
local_ip = get_local_ip()
print("Local IP Address:", local_ip)
print(f"[HOST] Binding to {local_ip}:9999 – share this with your client")

# Create TCP server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((local_ip, 9999))
server.listen()
client, _ = server.accept()

# Exchange public keys
client.send(public_key.save_pkcs1("PEM"))
public_partner = rsa.PublicKey.load_pkcs1(client.recv(2048))

# Function to send messages
def sending_messages(c):
    while True:
        msg = input("")
        if msg.lower() == "exit":
            c.send(b"exit")
            print("Disconnecting...")
            c.close()
            sys.exit()
        c.send(rsa.encrypt(msg.encode(), public_partner))
        print("You: " + msg)

# Function to receive messages
def receiving_messages(c):
    try:
        while True:
            data = c.recv(2048)
            if not data or data == b"exit":
                print("Partner disconnected.")
                break
            print("Partner: " + rsa.decrypt(data, private_key).decode())
    except (ConnectionAbortedError, OSError):
        # Socket has been closed, exit quietly
        pass
    finally:
        c.close()
        sys.exit()

# Start send/receive threads
t = threading.Thread(target=sending_messages, args=(client,))
t.daemon = True
t.start()

r = threading.Thread(target=receiving_messages, args=(client,))
r.daemon = True
r.start()

# Keep main thread alive
try:
    while True:
        pass
except KeyboardInterrupt:
    print("\nServer shutting down.")
    server.close()
    sys.exit()