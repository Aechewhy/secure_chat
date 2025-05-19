import socket
import threading

# Global flag to control thread execution
running = True

def receive_messages(client_socket):
    """Receive messages from the client and display them."""
    global running
    while running:
        try:
            data = client_socket.recv(1024)
            if not data:
                print("Client disconnected.")
                running = False
                break
            message = data.decode('utf-8')
            if message == "exit":
                print("Client sent exit command.")
                running = False
                break
            print("Client:", message)
        except:
            break

def send_messages(client_socket):
    """Send messages to the client based on user input."""
    global running
    while running:
        try:
            message = input("Server: ")
            if message == "exit":
                client_socket.send(message.encode('utf-8'))
                running = False
                break
            client_socket.send(message.encode('utf-8'))
        except:
            print("Error sending message.")
            running = False
            break

if __name__ == "__main__":
    # Set up server address and socket
    server_address = ('localhost', 12345)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(server_address)
    server_socket.listen(1)
    print("Waiting for connection...")

    # Accept client connection
    client_socket, client_address = server_socket.accept()
    print("Connected to", client_address)

    # Start threads for sending and receiving
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    send_thread = threading.Thread(target=send_messages, args=(client_socket,))
    receive_thread.start()
    send_thread.start()

    # Wait for threads to complete
    receive_thread.join()
    send_thread.join()

    # Clean up
    client_socket.close()
    server_socket.close()
    print("Server shut down.")
