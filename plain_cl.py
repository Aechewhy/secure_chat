import socket
import threading

# Global flag to control thread execution
running = True

def receive_messages(client_socket):
    """Receive messages from the server and display them."""
    global running
    while running:
        try:
            data = client_socket.recv(1024)
            if not data:
                print("Server disconnected.")
                running = False
                break
            message = data.decode('utf-8')
            if message == "exit":
                print("Server sent exit command.")
                running = False
                break
            print("Server:", message)
        except:
            break

def send_messages(client_socket):
    """Send messages to the server based on user input."""
    global running
    while running:
        try:
            message = input("Client: ")
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
    # Connect to server
    server_address = ('localhost', 12345)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server_address)
    print("Connected to server.")

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
    print("Client shut down.")
