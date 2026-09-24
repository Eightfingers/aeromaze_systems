import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.DEALER)
socket.setsockopt_string(zmq.IDENTITY, "CentralComputer")
socket.connect("tcp://localhost:5556")

while True:
    # Pass frame parts inside a list, using valid byte literals
    socket.send_multipart([b"NetworkHealth", b"Ping"])
    print("send 1")
    time.sleep(1)

    # 2. Block and wait for reply from ROUTER
    reply = socket.recv_multipart()
    print(f"Received reply: {[part.decode() for part in reply]}")

    time.sleep(1)