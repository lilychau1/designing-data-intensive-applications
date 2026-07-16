"""
cluster.py

Manages a cluster of database nodes.

This module is responsible for coordinating interactions between
multiple nodes, including leader election and log replication.
"""

from single_leader_replication.node import Node
from single_leader_replication.network import Network

class Cluster:
    def __init__(self, nodes: list[Node], leader_node: Node | None = None) -> None:
        """
        Initialize a new cluster with a list of nodes.

        Args:
            nodes (list[Node]): The list of nodes in the cluster.
        """
        self._nodes = nodes
        self._leader: Node | None = leader_node
        if leader_node is not None:
            self._leader = leader_node
            leader_node.set_role('leader')
        else:
            self._leader = None
        
        self._network: Network = Network()
        
        for node in self._nodes:
            self._network.register_node(node)
            node.set_network(self._network)

        self.configure_followers()

    def configure_followers(self) -> None:
        """
        Configure the followers for the current leader.

        This method ensures that all nodes in the cluster, except for the leader,
        are added as followers to the leader node.
        """
        if self._leader is None:
            return
    
        for node in self._nodes:
            if node != self._leader:
                self._leader.add_follower(node.id)

    @property
    def leader(self) -> Node:
        """
        Get the current leader of the cluster.

        Returns:
            Node: The current leader node.
        """
        if self._leader is None:
            raise RuntimeError('No leader is currently set in the cluster.')
        return self._leader

    def remove_node(self, node: Node) -> None:
        """
        Remove a node from the cluster.

        Args:
            node (Node): The node to remove.
        """
        if node not in self._nodes:
            return

        was_leader = node == self._leader

        self._nodes.remove(node)

        if was_leader:
            self.elect_new_leader()
    
    def choose_best_node(self) -> Node:
        """
        Choose the best node to become the new leader.

        Returns:
            Node: The chosen node to become the new leader.
        """
        if not self._nodes:
            raise RuntimeError('No nodes available to choose from.')
        else: 
            return max(
                self._nodes,
                key=lambda node: (
                    node.last_applied_index,
                    node.id,
                ),
            )
    
    def elect_new_leader(self) -> None:
        """
        Elect a new leader for the cluster.
        """
        new_leader = self.choose_best_node()

        if self._leader is not None:
            self._leader.set_role("follower")

        new_leader.promote_to_leader()

        self._leader = new_leader

        new_leader.clear_followers()
        self.configure_followers()
