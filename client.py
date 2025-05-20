import socket
import threading
import rsa
import sys

# Generate RSA key pair
public_key, private_key = rsa.newkeys(1024)

# Prompt for server IP
server_ip = input("Enter the HOST machine's IP address: ")

# Connect to server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((server_ip, 9999))

# Exchange public keys
public_partner = rsa.PublicKey.load_pkcs1(client.recv(2048))
client.send(public_key.save_pkcs1("PEM"))

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
    print("\nClient shutting down.")
    client.close()
    sys.exit()
