import zmq

context = zmq.Context()

def create_client_socket(ctx):
    """Helper to create and connect a fresh REQ socket."""
    sock = ctx.socket(zmq.REQ)
    sock.connect("tcp://localhost:5555")
    return sock

client_socket = create_client_socket(context)

# 1. Set up the Poller and register our client socket
poller = zmq.Poller()
poller.register(client_socket, zmq.POLLIN)

payload = "Hello Poller"
print(f"Sending: '{payload}'")
client_socket.send_string(payload)

# 2. Poll for the incoming reply with a 2000ms (2 second) timeout
# Instead of client_socket.recv_string() blocking your whole script, poll checks the wire.
socks = dict(poller.poll(timeout=2000))

# 3. Check if the socket actually received data
if client_socket in socks and socks[client_socket] == zmq.POLLIN:
    # A message is waiting in the buffer! This recv_string() is safe and instant.
    reply = client_socket.recv_string()
    print(f"Success! Received: {reply}")
else:
    # Timeout hit! No message arrived within 2 seconds.
    print("Timeout! The server is unresponsive.")
    
    # ⚠️ RECOVERY STEP:
    # The REQ socket is now in an unuseable "waiting-for-reply" state. 
    # To fix this so you can try sending again later, you must reset it.
    print("Resetting client connection...")
    poller.unregister(client_socket)
    client_socket.close()
    
    # Recreate and re-register a fresh socket for the next attempt
    client_socket = create_client_socket(context)
    poller.register(client_socket, zmq.POLLIN)

client_socket.close()
context.term()

## No poling method
# import zmq

# # Initialize the ZeroMQ context
# context = zmq.Context()

# # Create a REQ (Request) socket
# print("Connecting to the ZeroMQ server...")
# client_socket = context.socket(zmq.REQ)
# client_socket.connect("tcp://localhost:5555")

# # Send 5 sequential requests
# for request_num in range(1, 6):
#     payload = f"Hello {request_num}"
#     print(f"Sending: '{payload}' ...")
    
#     # 1. Send the request
#     client_socket.send_string(payload)
    
#     # 2. Block until the matching reply is received from the server
#     reply_message = client_socket.recv_string()
#     print(f"Received reply: [{reply_message}]")

# # Clean up resources
# client_socket.close()
# context.term()