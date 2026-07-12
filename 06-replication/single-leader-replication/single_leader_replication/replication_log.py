"""
replication_log.py

Stores an ordered sequence of write operations. 

Every successful write to the leader is first appended to the log. 

Later in the project, follower nodes will replay these log entries to
keep their state synchronised with the leader. 

For now, the log only exists in memory. 
"""
from typing import Any
from single_leader_replication.models import LogEntry

class ReplicationLog: 
    """
    An in-memory log of write operations.
    """
    
    def __init__(self) -> None: 
        """Initialise an empty log."""
        self.entries: list[LogEntry] = []
        
    def append(self, operation: str, key: str, value: Any) -> LogEntry: 
        index = len(self.entries) + 1
        entry = LogEntry(index=index, operation=operation, key=key, value=value)
        self.entries.append(entry)
        return entry
    
    def add_entry(self, log_entry: LogEntry) -> None:
        """
        Add a log entry to the log.

        Args:
            log_entry (LogEntry): The log entry to add.
        """
        if log_entry.index != len(self.entries) + 1:
            raise ValueError(f'Log entry index {log_entry.index} is not the next expected index {len(self.entries) + 1}.')
        else:
            self.entries.append(log_entry)
            
    def get(self, index: int) -> LogEntry | None:
        """
        Retrieve a log entry by its index.

        Args:
            index (int): The index of the log entry to retrieve.

        Returns:
            LogEntry | None: The log entry if found, otherwise None.
        """
        if 1 <= index <= len(self.entries):
            return self.entries[index - 1]
        else:
            return None