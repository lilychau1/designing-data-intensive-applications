"""
network_process.py

This module handles the network communication for each node in the cluster.
"""

from multiprocessing import Queue

class NetworkProcess:

    def __init__(self, outgoing: Queue, routes: dict[str, Queue]):
        """
        Initialize the NetworkProcess with an outgoing queue and a dictionary of queues for each node.

        Args:
            outgoing (Queue): The queue for sending outgoing messages.
            queues (dict[str, Queue]): A dictionary mapping node IDs to their respective queues.
        """
        self._outgoing = outgoing
        self._routes = routes
        
    def run(self):
        while True: 
            message = self._outgoing.get()
            
            if message is None: 
                break  # Exit the loop if a None message is received
            receiver = message.receiver_id
            if receiver not in self._routes:
                continue

            self._routes[receiver].put(message)