"""
cluster.py

Manages a cluster of database nodes.

This module is responsible for coordinating interactions between
multiple nodes, including leader election and log replication.
"""
from multiprocessing import Queue, Process, Manager
import uuid
from typing import Any

from single_leader_replication.config import Config
from single_leader_replication.node_process import NodeProcess
from single_leader_replication.network_process import NetworkProcess
from single_leader_replication.messages import (
    ConfigureFollowersMessage,
    DemoteToFollowerMessage,
    GetNodeStateRequestMessage,
    GetNodeStateResponseMessage,
    WriteRequestMessage,
    ReadRequestMessage,
    ReadResponseMessage,
    PromoteToLeaderMessage,
)

class Cluster:
    def __init__(self, node_configs: list[Config], leader_node_id: str | None = None) -> None:
        """
        Initialize a new cluster with a list of nodes.

        Args:
            nodes (list[Node]): The list of nodes in the cluster.
        """
        self._workers: dict[str, NodeProcess] = {}
        self._processes: dict[str, Process] = {}
        self._node_configs: dict[str, Config] = {config.node_id: config for config in node_configs}
        self._node_ids: list[str] = list(self._node_configs.keys())

        self._leader_id: str | None = leader_node_id

        # Create shared network
        # Outgoing messages from node processes to the network process
        self._outgoing: Queue = Queue()
        
        # Requests from clients into the cluster
        self._client_requests: Queue = Queue()
        self._client_responses: Queue = Queue()
        self._state_responses: Queue = Queue()

        # Network process for handling incoming and outgoing messages
        self._network_process: NetworkProcess = None
        
        # Route mapping for each node's inbox
        self._manager = Manager()
        self._routes: dict[str, Queue] = self._manager.dict()

        # Register every node on the network and reset its role.
        for node_id, config in self._node_configs.items():
            inbox = self._manager.Queue()
            
            # Worker-level logic
            worker = NodeProcess(
                config=config,
                inbox=inbox,
                outgoing=self._outgoing,
                client_responses=self._client_responses,
                state_responses=self._state_responses,
            )
            self._workers[node_id] = worker

            # System-level process
            process = Process(target=worker.run)
            self._processes[node_id] = process
            
            self._routes[node_id] = inbox

    def configure_followers(self) -> None:
        """
        Configure the followers for the current leader.

        This method ensures that all nodes in the cluster, except for the leader,
        are added as followers to the leader node.
        """
        if self._leader_id is None:
            return

        follower_ids = [node_id for node_id in self._node_ids if node_id != self._leader_id]
        self._routes[self._leader_id].put(
            ConfigureFollowersMessage(
                leader_id=self._leader_id,
                follower_ids=follower_ids
            )
        )

    @property
    def node_ids(self) -> list[str]:
        return self._node_ids
    
    @property
    def processes(self) -> dict[str, NodeProcess]:
        return self._workers
    
    @property
    def leader_id(self) -> str | None:
        return self._leader_id
    
    def start(self) -> None:
        """
        Start all node processes in the cluster.
        """
        
        # Start network router
        self._network_process = Process(
            target=NetworkProcess(
                outgoing=self._outgoing, # Outgoing messages of the cluster will be sent to the outgoing queue of the network process
                routes=self._routes, # Incoming messages for each node will be sent to their respective inboxes
            ).run
        )
        
        self._network_process.start()
        
        # Start node processes
        for process in self._processes.values():
            process.start()
            
        # Establish initail cluster state
        if self._leader_id is not None:
            self._routes[self._leader_id].put(
                PromoteToLeaderMessage()
            )
            
            self.configure_followers()
        else: 
            self.elect_new_leader()
        
    def stop(self) -> None:
        """
        Stop all node processes in the cluster.
        """
        for node_id, queue in self._routes.items():
            print(f"Stopping {node_id}")
            queue.put(None)

        for node_id, process in self._processes.items():
            print(f"Waiting for {node_id}")
            process.join()
            
        self._outgoing.put(None)
        self._network_process.join()
        
        self._manager.shutdown()
            
    def remove_node(self, node_id: str) -> None:
        """
        Remove a node from the cluster.

        Args:
            node (Node): The node to remove.
        """
        if node_id not in self._node_ids:
            return

        was_leader = node_id == self._leader_id

        # Stop process
        self._routes[node_id].put(None)
        self._processes[node_id].join()
        
        # Remove bookkeeping references
        self._node_ids.remove(node_id)
        del self._routes[node_id]
        del self._workers[node_id]
        del self._processes[node_id]
        del self._node_configs[node_id]

        if was_leader:
            self._leader_id = None
            self.elect_new_leader()
        else:
            self.configure_followers()
    
    def get_node_states(self) -> dict[str, GetNodeStateResponseMessage]:
        """
        Get the state of all nodes in the cluster.

        Args:
            node_id (str): The ID of the node to retrieve the state for.

        Returns:
            dict: A dictionary mapping node IDs to their state information, including role and last applied index.
        """
        request_id = str(uuid.uuid4())

        states: dict[str, GetNodeStateResponseMessage] = {}

        for node_id in self._node_ids:
            # Send a request to each node to get its state
            self._routes[node_id].put(
                GetNodeStateRequestMessage(
                    request_id=request_id,
                )
            )

        # Wait for responses from all nodes
        while len(states) < len(self._node_ids):
            response: GetNodeStateResponseMessage = self._state_responses.get()

            if response.request_id != request_id:
                continue
            
            states[response.node_id] = response
        
        return states
                
    def choose_best_node(self) -> str:
        """
        Choose the best node to become the new leader.

        Returns:
            str: The chosen node ID to become the new leader.
        """
        if not self._node_ids:
            raise RuntimeError('No nodes available to choose from.')

        states = self.get_node_states()
        
        return max(
            states.values(),
            key=lambda state: (
                state.last_applied_index,
                state.node_id,
            ),
        ).node_id
    
    def elect_new_leader(self) -> None:
        """
        Elect a new leader for the cluster based on the state of the live node processes.
        """
        
        if not self._node_ids:
            raise RuntimeError("No nodes available to elect a leader.")

        new_leader_id = self.choose_best_node()

        # Demote old leader
        if self._leader_id is not None:
            self._routes[self._leader_id].put(
                DemoteToFollowerMessage()
            )

        # Update cluster's view of leader
        self._leader_id = new_leader_id

        # Promote new leader
        self._routes[new_leader_id].put(
            PromoteToLeaderMessage()
        )

        # Configure followers for the new leader
        self.configure_followers()
        
    def write(self, key: str, value: any) -> None:
        """
        Write a key-value pair to the leader node.

        Args:
            key (str): The key to write.
            value (any): The value to write.
        """
        if self._leader_id is None:
            raise RuntimeError('No leader available to accept writes.')

        self._routes[self._leader_id].put(WriteRequestMessage(key=key, value=value))
    
    def read(self, key: str) -> any:
        """
        Read a value from the leader node.

        Args:
            key (str): The key to read.
        """
        if self._leader_id is None:
            raise RuntimeError('No leader available to accept reads.')
        
        request_id = str(uuid.uuid4())

        self._routes[self._leader_id].put(ReadRequestMessage(request_id=request_id, key=key))
        
        while True:
            response: ReadResponseMessage = self._client_responses.get()
            if response.request_id == request_id:
                return response.value
    
    def wait_for_replication(self, expected_index: int) -> None:
        """
        Wait for a key-value pair to be replicated across all nodes in the cluster.

        This method is primarily useful for testing and diagnostics.
        """
        while True:
            states = self.get_node_states()
            
            if all(
                state.last_applied_index >= expected_index
                for state in states.values()
            ):
                return
    
    def read_from_node(self, node_id: str, key: str) -> Any | None:
        """
        Read a value directly from a specific node.

        This is primarily useful for testing and diagnostics.
        """

        if node_id not in self._node_ids:
            raise ValueError(f"Unknown node: {node_id}")

        request_id = str(uuid.uuid4())

        self._routes[node_id].put(
            ReadRequestMessage(
                request_id=request_id,
                key=key,
            )
        )

        while True:
            response: ReadResponseMessage = self._client_responses.get()

            if response.request_id == request_id:
                return response.value