"""
node.py

Represents a single database node. 

A node owns: 
- Its local storage
- Its replication log

Clients send write requests to a node rather than directly to the 
storage engine. 

Later in the project, nodes will also replicate log entries to follower
nodes. 
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from typing import Any

from single_leader_replication.storage import Storage
from single_leader_replication.replication_log import ReplicationLog
from single_leader_replication.models import LogEntry
from single_leader_replication.config import Config

if TYPE_CHECKING:
    from single_leader_replication.network import Network

class Node():
    """
    A single database node. 
    """

    def __init__(
        self,
        config: Config, 
        role: str = 'follower', 
    ) -> None:
        """
        Initialize a new database node.
        """

        # Storage and replication log
        self._storage = Storage()
        self._log = ReplicationLog()
        
        # Node state
        self._last_applied_index = 0  # Track the index of the last applied log entry
        self._followers: list[str] = []  # List of follower node IDs for replication
        
        # Node identification and role
        self._config = config
        self._role = role  # Role of the node: 'leader' or 'follower'

    @property
    def id(self) -> str:
        """
        Get the unique identifier for the node.

        Returns:
            str: The unique identifier for the node.
        """
        return self._config.node_id

    @property
    def last_applied_index(self) -> int:
        """
        Get the index of the last applied log entry.

        Returns:
            int: The index of the last applied log entry.
        """
        return self._last_applied_index
    
    @property
    def log(self) -> list[LogEntry]:
        """
        Get the list of log entries.

        Returns:
            list[LogEntry]: The list of log entries.
        """
        return self._log.entries

    @property
    def address(self) -> str:
        """
        Get the network address of the node.

        Returns:
            str: The network address of the node.
        """
        return self._config.address
    
    @property
    def peers(self) -> dict[str, str]:
        """
        Get the dictionary of peer nodes.

        Returns:
            dict[str, str]: A dictionary mapping peer node IDs to their addresses.
        """
        return self._config.peers
    
    @property
    def followers(self) -> list[str]:
        """
        Get the list of follower node IDs.

        Returns:
            list[str]: The list of follower node IDs.
        """
        return self._followers.copy()
    
    def set_role(self, role: str) -> None:
        """
        Set the role of the node.

        Args:
            role (str): The role to set ('leader' or 'follower').
        """
        if role not in ['leader', 'follower']:
            raise ValueError("Role must be either 'leader' or 'follower'.")
        self._role = role
    
    @property
    def role(self) -> str:
        """
        Get the role of the node.

        Returns:
            str: The role of the node ('leader' or 'follower').
        """
        return self._role
    
    def _require_leader(self) -> None:
        """Ensure the node is a leader.

        Raises:
            ValueError: If the node is not a leader.
        """
        if self._role != "leader":
            raise ValueError("Only leader nodes can perform this operation.")
        
    def add_follower(self, follower_id: str) -> None:
        """
        Add a follower node to the list of followers for replication.

        Args:
            follower_id (str): The ID of the follower node to add.
        """
        self._require_leader()
        
        if follower_id == self.id:
            raise ValueError("A node cannot be its own follower.")

        if follower_id not in self._followers:
            self._followers.append(follower_id)

    def clear_followers(self) -> None:
        """
        Clear the list of followers for the node.
        """
        self._followers.clear()
    
    def promote_to_leader(self) -> None:
        """
        Promote this node to a leader role.
        """
        self._role = 'leader'
        self.clear_followers()
        
    def demote_to_follower(self) -> None:
        """
        Demote this node to a follower role.
        """
        self._role = 'follower'
        self.clear_followers()

    def receive_log_entry(self, log_entry: LogEntry) -> None:
        """
        Receive a log entry from the leader and apply it to the local storage.

        Args:
            log_entry (LogEntry): The log entry to apply.
        """
        if log_entry.index <= self._last_applied_index:
            # Ignore log entries that have already been applied
            return
        
        elif log_entry.index == self._last_applied_index + 1:
            # Append
            self._log.add_entry(log_entry)
            
            # Apply
            self.apply_log_entry(log_entry)
        else: 
            # Handle out-of-order log entries (not implemented in this simple example)
            raise ValueError(f"Received out-of-order log entry: {log_entry.index}. Expected: {self._last_applied_index + 1}")

    def apply_log_entry(self, log_entry: LogEntry) -> None:
        """
        Apply a log entry to the node's storage and update the last applied index.

        Args:
            log_entry (LogEntry): The log entry to apply.
        """
        self._storage.apply_log_entry(log_entry)
        self._last_applied_index = log_entry.index

    def write(self, key: str, value: Any) -> LogEntry:
        """
        Write a key-value pair to the node's storage and log the operation.

        Args:
            key (str): The key to write.
            value (Any): The value to write.
        """
        self._require_leader()
        # Append
        log_entry = self._log.append(operation='SET', key=key, value=value)

        # Apply
        self.apply_log_entry(log_entry)
    
        return log_entry  # Return the log entry for testing purposes

    def read(self, key: str) -> Any | None:
        """
        Read a value from the node's storage by key.

        Args:
            key (str): The key to read.

        Returns:
            Any | None: The value associated with the key, or None if not found.
        """
        return self._storage.get(key)
    