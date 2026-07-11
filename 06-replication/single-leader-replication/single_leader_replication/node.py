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

from typing import Any

from single_leader_replication.storage import Storage
from single_leader_replication.replication_log import ReplicationLog
from single_leader_replication.models import LogEntry


class Node():
    """
    A single database node. 
    """

    def __init__(self, role: str = 'follower') -> None:
        """
        Initialize a new database node.
        """
        self._storage = Storage()
        self._log = ReplicationLog()
        self._last_applied_index = 0  # Track the index of the last applied log entry
        self._followers: list[Node] = []  # List of follower nodes for replication
        self._role = role  # Role of the node: 'leader' or 'follower'
    
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
    
    def add_follower(self, follower: Node) -> None:
        """
        Add a follower node to the list of followers for replication.

        Args:
            follower (Node): The follower node to add.
        """
        if self._role != 'leader':
            raise ValueError("Only leader nodes can have followers.")
        else:
            if follower is self:
                raise ValueError("A node cannot be its own follower.")
            
            if follower not in self._followers:
                self._followers.append(follower)

    def promote_to_leader(self) -> None:
        """
        Promote this node to a leader role.
        """
        self._role = 'leader'
        self._followers = []  # Reset followers when promoting to leader
        
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
            # Apply the log entry if it's the next in sequence
            self._log.add_entry(log_entry)
            self._storage.apply_log_entry(log_entry)
            self._last_applied_index = log_entry.index
        else: 
            # Handle out-of-order log entries (not implemented in this simple example)
            raise ValueError(f"Received out-of-order log entry: {log_entry.index}. Expected: {self._last_applied_index + 1}")

    def sync_follower(self, follower: Node) -> None:
        """
        Replicate log entries to all follower nodes.

        This method sends all log entries that have not yet been applied to
        each follower node. It ensures that followers stay in sync with the
        leader's state.
        """
        for log_entry in self._log.entries:
            if log_entry.index > follower.last_applied_index:
                follower.receive_log_entry(log_entry)

    def write(self, key: str, value: Any) -> LogEntry:
        """
        Write a key-value pair to the node's storage and log the operation.

        Args:
            key (str): The key to write.
            value (Any): The value to write.
        """
        if self._role != 'leader':
            raise ValueError("Only leader nodes can accept write operations.")
        else: 
            log_entry = self._log.append(operation='SET', key=key, value=value)
            self._storage.apply_log_entry(log_entry)
            self._last_applied_index = log_entry.index  # Update the last applied index

            for follower in self._followers:
                self.sync_follower(follower)
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
    