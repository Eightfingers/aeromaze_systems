import time
import zmq

context = zmq.Context()
commander = context.socket(zmq.ROUTER)
commander.bind("tcp://127.0.0.1:5556")

print("Router is up")
time.sleep(1)

while True:
    # ROUTER receives 3 frames: identity, topic, payload
    identity, topic, payload = commander.recv_multipart()
    
    # Compare bytes with bytes (b"GoalPose")
    if topic == b"NetworkHealth":
        print(f"Received from {identity.decode()}: {topic.decode()} -> {payload.decode()}")
        # commander.send_multipart([b"Drone_1", b"NetworkHealth", b"Pong"])
        commander.send_multipart([identity, b"NetworkHealth", b"Pong"])