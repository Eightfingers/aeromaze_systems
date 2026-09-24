# Links
https://zguide.zeromq.org/docs/chapter1/
https://zguide.zeromq.org/docs/chapter2/
https://zguide.zeromq.org/docs/chapter3/

# Problem 

For multiple drones (will be referred to as nodes) awaiting command from a single computer, a more robust mechanism is required other than PUB/SUB. Since a published command message such as takeoff might not reach all drones (assuming if a single drone is lagging). Thus to achieve syncronization, we implement a Dealer-REP check before performing PUB/SUB.

# Router-Dealer vs REQ-REP
REQ-REP will cause the REQUESTER to perform a blocking wait before sending another REQ to another REP.
(This is not very fast although it is possible)
Therefore, we use the Router-Dealer pattern, where the central computer (Router) connects to multiple Robots (Dealer) multiple  nodes without blocking and then wait for replies accordingly from the REP node.
Once it recieve a REP from every1 -> We switch back to normal PUB-SUB 

Main computer (DEALER) sends a network health check to the drones (ROUTER) via Router-Dealer. Once Router-Dealer succeeds, we start normal PUB-SUB.
The Dealer Sockets Connects ()
The Router Socket Binds (remember the server socket binds!)
Bind on stable, long-lived, or static nodes: The component with a well-known IP address/port or fixed infrastructure should call bind().
Connect on dynamic, transient, or scaling nodes: The component that comes and goes, scales up/down, or lives behind NAT/firewalls should call connect().