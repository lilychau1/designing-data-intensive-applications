"""
test_replication_log.py

Unit tests for the ReplicationLog class in the single_leader_replication module.
"""

from single_leader_replication.replication_log import ReplicationLog
from single_leader_replication.models import LogEntry

def test_append_valid_log_entry():
    """
    Test that appending a log entry increases the log size.
    """
    log = ReplicationLog()
    initial_size = len(log.entries)
    operation = 'SET'
    key = 'test_key'
    value = 'test_value'
    log.append(operation=operation, key=key, value=value)
    assert len(log.entries) == initial_size + 1

def test_get_existing_log_entry():
    """
    Test that retrieving a log entry by index returns the correct entry.
    """
    log = ReplicationLog()
    operation = 'SET'
    key = 'test_key'
    value = 'test_value'
    log_entry = LogEntry(index=1, operation=operation, key=key, value=value)
    log.append(operation=operation, key=key, value=value)
    assert log.get(1) == log_entry

def test_get_non_existent_log_entry():
    """
    Test that retrieving a non-existent log entry returns None.
    """
    log = ReplicationLog()
    assert log.get(0) is None
