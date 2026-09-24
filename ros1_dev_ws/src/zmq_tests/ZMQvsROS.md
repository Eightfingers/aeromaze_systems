# ROS1 vs pyZMQ behaviour on a lossy network.

## Notes on ROS1 vsd pyZMQ behaviour on a simulated lossy network 
'sudo tc qdisc add dev lo root netem delay 100ms loss 10%'
100ms delay and 10% packet loss
Using ping we can measure the RTT to be ~200ms. 

## Testing scripts
The python script `python3 pub_self_position.py` creates 10 publishers in ROS1 and ZMQ.

## Initing ROS nodes under lossy wifi
Time taken to create ROS node: 1.732560 seconds

Latency is also inccured in initing a ros node under lossy wifi

## Testing 10 ROS publishers 
Time taken to create ROS odom publisher: 0.201129 seconds
Time taken to create ROS odom publisher: 0.201334 seconds
Time taken to create ROS odom publisher: 0.202194 seconds
Time taken to create ROS odom publisher: 0.202712 seconds
Time taken to create ROS odom publisher: 0.457281 seconds
Time taken to create ROS odom publisher: 0.201056 seconds
Time taken to create ROS odom publisher: 0.641792 seconds
Time taken to create ROS odom publisher: 0.202452 seconds
Time taken to create ROS odom publisher: 0.201978 seconds
Time taken to create ROS odom publisher: 0.619260 seconds
Time taken to create every ROS publisher: 3.131573 seconds

Notice the latency of around ~RTT inccured in creating odom publisher, which is around 200ms each.

## Testing 10 ZMQ publishers 
Time taken to create ZMQ pose publisher: 0.000589 seconds
Time taken to create ZMQ pose publisher: 0.000097 seconds
Time taken to create ZMQ pose publisher: 0.000070 seconds
Time taken to create ZMQ pose publisher: 0.000061 seconds
Time taken to create ZMQ pose publisher: 0.000068 seconds
Time taken to create ZMQ pose publisher: 0.000063 seconds
Time taken to create ZMQ pose publisher: 0.000066 seconds
Time taken to create ZMQ pose publisher: 0.000183 seconds
Time taken to create ZMQ pose publisher: 0.000081 seconds
Time taken to create ZMQ pose publisher: 0.000062 seconds
Time taken to create every ZMQ Pose publisher: 0.001617 seconds

No latency of RTT inccured in creating odom publisher, which is around 200ms each.

## Testing 10 ROS subscribers 
Time taken to create ROS odom sub0: 0.908792 seconds
Time taken to create ROS odom sub1: 1.342733 seconds
Time taken to create ROS odom sub2: 1.994537 seconds
Time taken to create ROS odom sub3: 0.405121 seconds
Time taken to create ROS odom sub4: 1.045592 seconds
Time taken to create ROS odom sub5: 1.061893 seconds
Time taken to create ROS odom sub6: 0.405777 seconds
Time taken to create ROS odom sub7: 0.835805 seconds
Time taken to create ROS odom sub8: 0.818827 seconds
Time taken to create ROS odom sub9: 1.343063 seconds
All ROS subs took : 10.163453 seconds to create

Notice even greater latency incurred in creating zmq odom subscriber.

All ROS subs took : 10.163453 seconds to create
Average end to end time taken for sub1: 0.282899 seconds and it took 13.932265 seconds to fill up the socket.
Average end to end time taken for sub0: 0.321338 seconds and it took 18.188959 seconds to fill up the socket.
Average end to end time taken for sub2: 0.339997 seconds and it took 15.006428 seconds to fill up the socket.
Average end to end time taken for sub3: 0.320112 seconds and it took 14.757553 seconds to fill up the socket.
Average end to end time taken for sub7: 0.252333 seconds and it took 12.952387 seconds to fill up the socket.
Average end to end time taken for sub5: 0.298079 seconds and it took 14.233765 seconds to fill up the socket.
Average end to end time taken for sub8: 0.337380 seconds and it took 13.429196 seconds to fill up the socket.
Average end to end time taken for sub9: 0.320372 seconds and it took 12.502147 seconds to fill up the socket.
Average end to end time taken for sub4: 0.386492 seconds and it took 17.188550 seconds to fill up the socket.
Average end to end time taken for sub6: 0.369197 seconds and it took 16.795861 seconds to fill up the socket.

Out of 200 samples end to end time time. End to end time taken is defined as taking the recieved msg timestamp - current ros timestamp.

## Testing 10 ZMQ subscribers
Time taken to connect to ZMQ socket0 : 0.000517 seconds
Time taken to connect to ZMQ socket1 : 0.000114 seconds
Time taken to connect to ZMQ socket2 : 0.000094 seconds
Time taken to connect to ZMQ socket3 : 0.000096 seconds
Time taken to connect to ZMQ socket4 : 0.000089 seconds
Time taken to connect to ZMQ socket5 : 0.000085 seconds
Time taken to connect to ZMQ socket6 : 0.000096 seconds
Time taken to connect to ZMQ socket7 : 0.000081 seconds
Time taken to connect to ZMQ socket8 : 0.000086 seconds
Time taken to connect to ZMQ socket9 : 0.000080 seconds
All ZMQ sockets took : 0.001506 seconds to create

Almost no latency incurred in creating ros zmq subscriber socket.

Average end to end time taken for sub5: 0.254608 seconds and it took 10.780004 seconds to fill up the socket.
Average end to end time taken for sub3: 0.230111 seconds and it took 10.929757 seconds to fill up the socket.
Average end to end time taken for sub9: 0.321862 seconds and it took 10.988290 seconds to fill up the socket.
Average end to end time taken for sub2: 0.220253 seconds and it took 11.029909 seconds to fill up the socket.
Average end to end time taken for sub0: 0.205873 seconds and it took 11.330280 seconds to fill up the socket.
Average end to end time taken for sub8: 0.224125 seconds and it took 11.630883 seconds to fill up the socket.
Average end to end time taken for sub6: 0.260347 seconds and it took 12.181471 seconds to fill up the socket.
Average end to end time taken for sub1: 0.223311 seconds and it took 12.331396 seconds to fill up the socket.
Average end to end time taken for sub7: 0.213126 seconds and it took 13.232135 seconds to fill up the socket.
Average end to end time taken for sub4: 0.368070 seconds and it took 15.313269 seconds to fill up the socket.

Out of 200 samples end to end time time. End to end time taken is defined as taking the recieved msg timestamp - current ros timestamp.

