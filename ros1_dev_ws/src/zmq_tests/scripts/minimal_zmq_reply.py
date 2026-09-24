import time
import zmq

# Initialize the ZeroMQ context
context = zmq.Context()

# Create a REP (Reply) socket
server_socket = context.socket(zmq.REP)
server_socket.bind("tcp://*:5555")

print("ZeroMQ Server started. Waiting for requests on port 5555...")

while True:
    # 1. Block and wait for the next request from a client
    request_message = server_socket.recv_string()
    print(f"Received request: '{request_message}'")

    # Simulate doing some "work" (e.g., database query or processing)
    time.sleep(1)

    # 2. Send the reply back to the exact client who requested it
    reply_message = f"World (Processed: {request_message})"
    server_socket.send_string(reply_message)
