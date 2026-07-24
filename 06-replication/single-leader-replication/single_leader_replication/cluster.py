"""
cluster.py

Manages a cluster of database nodes.

This module is responsible for coordinating interactions between
multiple nodes, including leader election and log replication.
"""
from multiprocessing import Queue, Process, Manager
import uuid
from typing import Any
import queue

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
from single_leader_replication.models import NodeInfo, NodeStatus, NodeRole

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
        self._all_node_ids: list[str] = list(self._node_configs.keys())
        self._active_node_ids: list[str] = list(self._node_configs.keys())
        self._node_history: dict[str, NodeInfo] = {}
        
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
            
            self._node_history[node_id] = NodeInfo(
                node_id=node_id,
                role=NodeRole.FOLLOWER if node_id != self._leader_id else NodeRole.LEADER,
                status=NodeStatus.STOPPED,
                last_applied_index=0,
            )

    def configure_followers(self) -> None:
        """
        Configure the followers for the current leader.

        This method ensures that all nodes in the cluster, except for the leader,
        are added as followers to the leader node.
        """
        if self._leader_id is None:
            return

        follower_ids = [node_id for node_id in self._active_node_ids if node_id != self._leader_id]
        self._routes[self._leader_id].put(
            ConfigureFollowersMessage(
                leader_id=self._leader_id,
                follower_ids=follower_ids
            )
        )

    @property
    def node_ids(self) -> list[str]:
        return self._all_node_ids
    
    @property
    def active_node_ids(self) -> list[str]:
        return self._active_node_ids

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
        Remove a node from the active cluster while retaining its
        historical state for observability.
        """

        if node_id not in self._all_node_ids:
            return

        if node_id not in self._active_node_ids:
            return

        was_leader = node_id == self._leader_id

        # Get final state before removing the node.
        final_state = self.get_node_state(node_id)

        # Mark it as removed.
        self._node_history[node_id] = NodeInfo(
            node_id=node_id,
            role=NodeRole.FOLLOWER,
            status=NodeStatus.REMOVED,
            last_applied_index=final_state.last_applied_index,
        )
        
        # Stop process.
        self._routes[node_id].put(None)
        self._processes[node_id].join()

        # Remove from active cluster.
        self._active_node_ids.remove(node_id)

        # Remove active runtime resources.
        del self._routes[node_id]
        del self._workers[node_id]
        del self._processes[node_id]

        if was_leader:
            self._leader_id = None

            if self._active_node_ids:
                self.elect_new_leader()
        else:
            self.configure_followers()
    
    def restart_node(self, node_id: str) -> None:
        """
        Restart a previously removed node and add it back to the active cluster.

        The node is recreated as a follower and then added back to the
        current leader's follower configuration.
        """

        if node_id not in self._all_node_ids:
            raise ValueError(f"Unknown node: {node_id}")

        if node_id in self._active_node_ids:
            raise ValueError(f"Node {node_id} is already active")

        config = self._node_configs[node_id]

        # Create a new inbox for the restarted node.
        inbox = self._manager.Queue()

        # Create a new NodeProcess.
        worker = NodeProcess(
            config=config,
            inbox=inbox,
            outgoing=self._outgoing,
            client_responses=self._client_responses,
            state_responses=self._state_responses,
        )

        # Create a new OS process.
        process = Process(target=worker.run)

        # Restore runtime bookkeeping.
        self._routes[node_id] = inbox
        self._workers[node_id] = worker
        self._processes[node_id] = process

        # Mark node as active again.
        self._active_node_ids.append(node_id)

        # Start the process.
        process.start()

        # Reset the node's role to follower.
        self._routes[node_id].put(
            DemoteToFollowerMessage()
        )

        # Remove REMOVED status from history.
        previous_state = self._node_history[node_id]

        self._node_history[node_id] = NodeInfo(
            node_id=node_id,
            role=NodeRole.FOLLOWER,
            status=NodeStatus.RUNNING,
            last_applied_index=previous_state.last_applied_index,
        )
        # Reconfigure the leader's followers.
        self.configure_followers()
            
    def get_node_states(self) -> dict[str, NodeInfo]:
        """
        Return the latest known state of every node, including removed nodes.

        This method does not query node processes. It returns the cluster's
        latest known snapshot.
        """
        return dict(self._node_history)
    
    def get_active_node_states(self) -> dict[str, NodeInfo]:
        """
        Query all active nodes for their current state.

        Returns:
            A dictionary mapping active node IDs to their latest state.
        """

        request_id = str(uuid.uuid4())

        states: dict[str, NodeInfo] = {}

        active_node_ids = list(self._active_node_ids)

        for node_id in active_node_ids:
            self._routes[node_id].put(
                GetNodeStateRequestMessage(
                    request_id=request_id,
                )
            )

        while len(states) < len(active_node_ids):
            try:
                response: GetNodeStateResponseMessage = (
                    self._state_responses.get(timeout=5)
                )
            except queue.Empty:
                raise RuntimeError(
                    "Timed out waiting for node state responses. "
                    f"Received {len(states)} of {len(active_node_ids)} responses."
                )

            if response.request_id != request_id:
                continue

            process = self._processes[response.node_id]

            state = NodeInfo(
                node_id=response.node_id,
                role=response.role,
                status=(
                    NodeStatus.RUNNING
                    if process.is_alive()
                    else NodeStatus.STOPPED
                ),
                last_applied_index=response.last_applied_index,
            )

            states[response.node_id] = state

            # Update latest known state.
            self._node_history[response.node_id] = state

        return states


    def get_node_state(self, node_id: str) -> NodeInfo:
        """
        Get the current state of a node.

        Active nodes are queried directly.
        Removed nodes return their last known state.
        """

        if node_id not in self._all_node_ids:
            raise ValueError(f"Unknown node: {node_id}")

        if node_id not in self._active_node_ids:
            return self._node_history[node_id]

        request_id = str(uuid.uuid4())

        self._routes[node_id].put(
            GetNodeStateRequestMessage(
                request_id=request_id,
            )
        )

        while True:
            response: GetNodeStateResponseMessage = (
                self._state_responses.get()
            )

            if response.request_id != request_id:
                continue

            process = self._processes[response.node_id]

            state = NodeInfo(
                node_id=response.node_id,
                role=response.role,
                status=(
                    NodeStatus.RUNNING
                    if process.is_alive()
                    else NodeStatus.STOPPED
                ),
                last_applied_index=response.last_applied_index,
            )

            self._node_history[node_id] = state

            return state

    def choose_best_node(self) -> str:
        """
        Choose the best node to become the new leader.

        Returns:
            str: The chosen node ID to become the new leader.
        """
        if not self._active_node_ids:
            raise RuntimeError('No active nodes available to choose from.')

        states = self.get_active_node_states()
        
        running_states = [
            state for state in states.values()
            if state.status == NodeStatus.RUNNING
        ]

        return max(
            running_states,
            key=lambda state: (
            state.last_applied_index,
            state.node_id,
            ),
        ).node_id
    
    def elect_new_leader(self) -> None:
        """
        Elect a new leader from the currently active nodes.
        """

        if not self._active_node_ids:
            raise RuntimeError("No active nodes available.")

        # Find the best active node.
        new_leader_id = self.choose_best_node()

        # Demote the previous leader if there is one
        # and it is still active.
        if (
            self._leader_id is not None
            and self._leader_id in self._active_node_ids
            and self._leader_id != new_leader_id
        ):
            self._routes[self._leader_id].put(
                DemoteToFollowerMessage()
            )

        # Update cluster's leader reference.
        self._leader_id = new_leader_id

        # Promote new leader.
        self._routes[new_leader_id].put(
            PromoteToLeaderMessage()
        )

        # Update the historical state immediately.
        previous_state = self._node_history[new_leader_id]

        self._node_history[new_leader_id] = NodeInfo(
            node_id=new_leader_id,
            role=NodeRole.LEADER,
            status=NodeStatus.RUNNING,
            last_applied_index=previous_state.last_applied_index,
        )

        # Configure the new leader with active followers.
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
            states = self.get_active_node_states()
            
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

        if node_id not in self._all_node_ids:
            raise ValueError(f"Unknown node: {node_id}")
        
        if node_id not in self._active_node_ids:
            raise ValueError(f"Node {node_id} is not active.")

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