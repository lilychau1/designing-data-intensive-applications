"""
storage.py

Implements the storage engine for a single database node. 

The storage engine is responsible only for maintaining the node's local
key-value state. It knows nothing about networking, replicaiton, leaders, 
followers or HTTP. 

Initially the storage engine is empty an in-memory dictionary. 

Later in the project, writes will come from replaying replication log
entries instead of directly from clients. 
"""

from typing import Any
from single_leader_replication.replication_log import ReplicationLog
from single_leader_replication.models import LogEntry

class Storage:
    """
    A simple in-memory key-value store.
    
    This class represents the local state of a database node. 
    """
        
        
    def __init__(self) -> None: 
        """Initialise an empty key-value store."""
        self._data: dict[str, Any] = {}
        
    def apply_log_entry(self, entry:LogEntry) -> None:
        """
        Apply a log entry to the local state. 

        Args:
            entry (LogEntry): The log entry to apply.
        """
        if entry.operation == 'SET':
            self._data[entry.key] = entry.value
        else:
            raise ValueError(f'Unknown operation: {entry.operation}')
        
    def get(self, key:str) -> Any | None: 
        """
        Retrieve a value by key. 
        
        Returns None if the key doesn't exist. 

        Args:
            key (str): Key to retrieve.

        Returns:
            Any | None: Value associated with the key, or None if not found.
        """
        return self._data.get(key)
    