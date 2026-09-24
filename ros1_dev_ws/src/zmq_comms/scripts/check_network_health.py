#!/usr/bin/env python3

import zmq
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import io
import time

# Run this script to publish setpoints to all drones on the Ground Control Computer!!!

# STARLING 2 Camera POV
# Positive X -> Right 
# Positive Y -> Forward 

# EMNAVI GLOBAL FRAME, INITIALIZED WITH CAMERA FACING FORWARD
# Positive X -> Foward
# Positive Y -> LEFT

# NUS VICON ROOM
# POSITIVE X -> is Left
# POSITIVE Y -> is backward

class NetworkHealth:
    def __init__(self):
        # ZeroMQ setup
        self.context = zmq.Context()
        self.poller = zmq.Poller()
        self.polling = True

        self.str_start_ip = "192.168.65.206"
        self.num_drones = 10
        parts = self.str_start_ip.split('.')
        self.start_ip_fourth_octet = int(parts[3])
        self.str_first_second_third_octet = parts[0] + "." + parts[1] + "." + parts[2] + "." 

        # Use a Dealer Router pattern to send pings recieve acks from each drone
        self.dealer_socket_map = {}
        self.list_of_agent_names = []

        self.timeout_seconds = 2.0

        # Dynamically connect..
        for i in range (self.num_drones):
            dealer_socket = self.context.socket(zmq.DEALER)
            dealer_socket.setsockopt_string(zmq.IDENTITY, "CentralComputer")
            str_current_ip = self.str_first_second_third_octet + str(self.start_ip_fourth_octet + i)
            dealer_socket.connect(f"tcp://{str_current_ip}:5556") # 5556 for network health
            self.poller.register(dealer_socket, zmq.POLLIN)
            self.dealer_socket_map[dealer_socket] = i

            # Dynamically fill in the list of agent names
            agent_name = "agent_{}".format(i+1)
            self.list_of_agent_names.append(agent_name)
            print("Agent name: {}, Ip Address: {}".format(agent_name, str_current_ip))


        print("ZMQ setup ready")
    
    def check_for_health(self):
        print("Checking for network health, pinging all agents!")
        # 1. Send Ping out to all dealer sockets
        for sock in self.dealer_socket_map:
            sock.send_multipart([b"NetworkHealth", b"Ping"])

        # 2. Setup tracking for the 1.5-second time window
        start_time = time.time()

        # Use a set instead of a list to avoid duplicate ACKs from inflating counts
        agent_names_received = set()
        expected_agents = set(self.list_of_agent_names)

        while True:
            # Calculate remaining time left in our 1-second budget
            elapsed = time.time() - start_time
            remaining_ms = int((self.timeout_seconds - elapsed) * 1000)

            # Time budget expired or all agents replied -> exit loop
            if remaining_ms <= 0 or agent_names_received == expected_agents:
                break

            # Poll with the EXACT remaining time left
            socks = dict(self.poller.poll(timeout=remaining_ms))

            # Process sockets that have incoming data
            for sock, event in socks.items():
                if event & zmq.POLLIN:
                    try:
                        # recv_multipart(zmq.NOBLOCK) prevents blocking if frames get desynced
                        msg = sock.recv_multipart(flags=zmq.NOBLOCK)
                        
                        if len(msg) == 2:
                            topic, data = msg
                            if topic == b"NetworkHealth":
                                agent_id = data.decode('utf-8')
                                print(f"Got ACK from agent: {agent_id}")
                                agent_names_received.add(agent_id)
                                
                    except zmq.ZMQError as e:
                        print("Recv error:", e)

        # 3. Validation check after loop finishes
        missing_agents = expected_agents - agent_names_received

        if not missing_agents:
            print("All agents responded successfully within {} second!".format(self.timeout_seconds))
            return True
        else:
            print("Timeout reached..")
            print(f"Obtained responses from: {list(agent_names_received)}")
            print(f"Timeout reached. Missing responses from: {list(missing_agents)}")
            return False

    def shutdown_node(self):
        print("Shutting down node")
        for sock in self.dealer_socket_map:
            sock.close()
        self.context.term()

if __name__ == "__main__":
    node = NetworkHealth()
    node.check_for_health()
    node.shutdown_node()
