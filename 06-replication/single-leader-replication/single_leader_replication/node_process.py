"""
node_process.py

Node process for handling incoming requests and managing the node's state.
"""

from multiprocessing import Queue
from single_leader_replication.node import Node
from single_leader_replication.config import Config
from single_leader_replication.messages import (
    AppendEntryMessage,
    ConfigureFollowersMessage,
    GetNodeStateRequestMessage,
    GetNodeStateResponseMessage,
    WriteRequestMessage,
    ReadRequestMessage,
    ReadResponseMessage,
    PromoteToLeaderMessage,
    DemoteToFollowerMessage,
)

class NodeProcess:
    """
    A process that runs a single database node and handles incoming requests.
    """
    def __init__(
        self, 
        config: Config,
        inbox: Queue,
        outgoing: Queue,
        client_responses: Queue,
        state_responses: Queue,
    ) -> None:
        """
        Initialize a new NodeProcess.

        Args:
            node (Node): The database node to run in this process.
            inbox (Queue): A queue for receiving incoming requests.
            outgoing (Queue): A queue for sending outgoing requests.
        """
        self._config: Config = config
        self._inbox: Queue = inbox
        self._outgoing: Queue = outgoing
        self._client_responses: Queue = client_responses
        self._state_responses: Queue = state_responses
        self._node: Node | None = None  # The database node will be initialized in the run method

    def run(self) -> None:
        """
        Run the node process, handling incoming requests from the inbox.
        """
        self._node = Node(config=self._config)
        
        while True: 
            message = self._inbox.get()
            
            if message is None: 
                break  # Exit the loop if a None message is received
            
            self.handle_message(message)

    def handle_message(
        self,
        message:
            AppendEntryMessage
            | WriteRequestMessage
            | ReadRequestMessage
            | PromoteToLeaderMessage
            | DemoteToFollowerMessage
            | ConfigureFollowersMessage
            | GetNodeStateRequestMessage,
    ) -> None:
        """
        Handle an incoming message.

        Args:
            message (AppendEntryMessage): The incoming message to handle.
        """
        if isinstance(message, AppendEntryMessage):
            self._node.receive_log_entry(message.log_entry)
        elif isinstance(message, WriteRequestMessage):
            self.handle_write(message)
        elif isinstance(message, ReadRequestMessage):
            self.handle_read(message)
        elif isinstance(message, PromoteToLeaderMessage):
            self.handle_promote_to_leader()
        elif isinstance(message, DemoteToFollowerMessage):
            self.handle_demote_to_follower()
        elif isinstance(message, ConfigureFollowersMessage):
            self.handle_configure_followers(message)
        elif isinstance(message, GetNodeStateRequestMessage):
            self.handle_get_node_state(message)
        else:
            raise ValueError(f"Unknown message type: {type(message)}")

    def handle_write(self, message: WriteRequestMessage) -> None:
        """
        Handle a write request message.

        Args:
            message (WriteRequestMessage): The incoming write request message to handle.
        """
        log_entry = self._node.write(message.key, message.value)
        
        for follower_id in self._node.followers:
            self._outgoing.put(AppendEntryMessage(
                sender_id=self._node.id,
                receiver_id=follower_id,
                log_entry=log_entry, 
            )
        )
            
    def handle_read(self, message: ReadRequestMessage) -> None:
        """
        Handle a read request message.

        Args:
            message (ReadRequestMessage): The incoming read request message to handle.
        """
        value = self._node.read(message.key)

        self._client_responses.put(
            ReadResponseMessage(
                request_id=message.request_id,
                key=message.key,
                value=value,
            )
        )
    
    def handle_promote_to_leader(self) -> None:
        """
        Handle a promote to leader message.

        Args:
            message (PromoteToLeaderMessage): The incoming promote to leader message to handle.
        """
        self._node.promote_to_leader()
        
    def handle_demote_to_follower(self) -> None:
        """
        Handle a demote to follower message.

        Args:
            message (DemoteToFollowerMessage): The incoming demote to follower message to handle.
        """
        self._node.demote_to_follower()
    
    def handle_configure_followers(self, message: ConfigureFollowersMessage) -> None:
        """
        Handle a configure followers message.

        Args:
            message (ConfigureFollowersMessage): The incoming configure followers message to handle.
        """
        if message.leader_id != self._node.id:
            raise ValueError(f"Node {self._node.id} received ConfigureFollowersMessage for leader {message.leader_id}")
        
        self._node.clear_followers()
        
        for follower_id in message.follower_ids:
            self._node.add_follower(follower_id)

    def handle_get_node_state(self, message: GetNodeStateRequestMessage) -> None:
        """
        Handle a get node state request.

        Args:
            message (GetNodeStateRequestMessage): The incoming get node state request message to handle.
        """
        self._state_responses.put(
            GetNodeStateResponseMessage(
                request_id=message.request_id,
                node_id=self._node.id,
                role=self._node.role,
                last_applied_index=self._node.last_applied_index,
            )
        )
