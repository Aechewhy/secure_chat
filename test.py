
import socket
import threading
import rsa

# Get the local machine's IP address dynamically
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # Try to connect to a public IP (Google DNS) and get the local IP
        s.connect(('10.254.254.254', 1))  # This doesn't actually send data
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'  # Default to localhost if no connection is available
    finally:
        s.close()
    return local_ip

# Automatically get the IP and use it
local_ip = get_local_ip()
print("Local IP Address:", local_ip)

public_key, private_key = rsa.newkeys(1024)
public_partner = None
choice = input("Do you want to host (1) or to connect (2): ")

if choice == '1':
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((local_ip, 9999))
    server.listen()
    client, _ = server.accept()
    client.send(public_key.save_pkcs1("PEM"))
    public_partner = rsa.PublicKey.load_pkcs1(client.recv(1024))

elif choice == '2':
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((local_ip, 9999))
    public_partner = rsa.PublicKey.load_pkcs1(client.recv(1024))
    client.send(public_key.save_pkcs1("PEM"))
else:
    exit()

def sending_messages(c):
    while True:
        message = input("")
        # c.send(rsa.encrypt(message.encode(), public_partner))
        c.send(message.encode())
        print("You: " + message)
def receiving_messages(c):
    while True:
        # print("Partner: " + rsa.decrypt(c.recv(1024),private_key).decode())
        print("Partner: " + c.recv(1024).decode())

threading.Thread(target=sending_messages, args=(client,)).start()
threading.Thread(target=receiving_messages, args=(client,)).start()