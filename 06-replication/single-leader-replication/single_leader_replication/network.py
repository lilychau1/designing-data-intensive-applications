"""
network.py

Manages the network communication between database nodes.
"""
from single_leader_replication.node import Node
from single_leader_replication.models import LogEntry

class Network:
    """
    Represents the network layer for database nodes.
    """
    
    def __init__(self):
        """
        Initialize the network with an empty list of nodes.
        """
        self._nodes: list[Node] = []
        
    def register_node(self, node: Node) -> None:
        """
        Register a new node to the network.
        
        Args:
            node (Node): The node to register.
        """
        self._nodes.append(node)
        
    def send(self, sender: Node, receiver: Node, log_entry_message: LogEntry) -> None: 
        """
        Send a LogEntry message from one node to another.
        
        Args:
            sender (Node): The node sending the LogEntry message.
            receiver (Node): The node receiving the LogEntry message.
            log_entry_message (LogEntry): The LogEntry message to send.
        """
        if sender not in self._nodes or receiver not in self._nodes: 
            raise ValueError("Both sender and receiver must be registered nodes.")

        elif sender == receiver:
            raise ValueError("Sender and receiver cannot be the same node.")
        
        elif sender.role != 'leader':
            raise ValueError("Only the leader node can send messages.")
        
        receiver.receive_log_entry(log_entry_message)
        
