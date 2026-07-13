"""
network.py

Manages the network communication between database nodes.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from single_leader_replication.models import LogEntry

if TYPE_CHECKING:
    from single_leader_replication.node import Node
class Network:
    """
    Represents the network layer for database nodes.
    """
    
    def __init__(self):
        """
        Initialize the network with an empty list of nodes.
        """
        self._nodes: dict[str, Node] = {}
        
    def get_node(self, node_id: str) -> Node:
        """
        Retrieve a node by its ID.
        
        Args:
            node_id (str): The ID of the node to retrieve.
        
        Returns:
            Node: The node with the specified ID.
        """
        return self._nodes[node_id]
        
    def register_node(self, node: Node) -> None:
        """
        Register a new node to the network.

        Args:
            node (Node): The node to register.
        """
        self._nodes[node.id] = node

    def send(self, sender_id: str, receiver_id: str, log_entry_message: LogEntry) -> None:
        """
        Send a LogEntry message from one node to another.
        
        Args:
            sender (Node): The node sending the LogEntry message.
            receiver (Node): The node receiving the LogEntry message.
            log_entry_message (LogEntry): The LogEntry message to send.
        """
        if sender_id not in self._nodes or receiver_id not in self._nodes:
            raise ValueError("Both sender and receiver must be registered nodes.")

        elif sender_id == receiver_id:
            raise ValueError("Sender and receiver cannot be the same node.")

        self._nodes[receiver_id].receive_log_entry(log_entry_message)
