"""
network_process.py

This module handles the network communication for each node in the cluster.
"""

from multiprocessing import Queue
from threading import Timer

from single_leader_replication.messages import AppendEntryMessage

class NetworkProcess:

    def __init__(self, outgoing: Queue, routes: dict[str, Queue], replication_delays: dict[str, float]):
        """
        Initialize the NetworkProcess with an outgoing queue and a dictionary of queues for each node.

        Args:
            outgoing (Queue): The queue for sending outgoing messages.
            queues (dict[str, Queue]): A dictionary mapping node IDs to their respective queues.
        """
        self._outgoing = outgoing
        self._routes = routes
        self._replication_delays = replication_delays
        
    def run(self):
        while True: 
            message = self._outgoing.get()
            
            if message is None: 
                break  # Exit the loop if a None message is received
            receiver = message.receiver_id
            if receiver not in self._routes:
                continue

            delay = self._replication_delays.get(receiver, 0)
            
            if isinstance(message, AppendEntryMessage) and delay > 0: 
                timer = Timer(
                    delay, 
                    self._routes[receiver].put,
                    args=(message,), 
                )
                
                timer.daemon = True  # Ensure the timer thread does not prevent program exit
                timer.start()
                continue  # Skip the immediate sending of the message; it will be sent after the delay
            
            self._routes[receiver].put(message)