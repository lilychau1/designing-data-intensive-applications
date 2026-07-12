"""
test_storage.py

Unit tests for the Storage class in the single_leader_replication module.
"""

from single_leader_replication.storage import Storage
from single_leader_replication.models import LogEntry

def test_apply_log_entry_set_operation():
    """
    Test that applying a 'SET' log entry correctly updates the storage.
    """
    storage = Storage()
    log_entry = LogEntry(index=0, operation='SET', key='test_key', value='test_value')
    
    storage.apply_log_entry(log_entry)
    
    assert storage.get('test_key') == 'test_value'

def test_apply_log_entry_invalid_operation():
    """
    Test that applying a log entry with an invalid operation raises a ValueError.
    """
    storage = Storage()
    log_entry = LogEntry(index=0,operation='INVALID', key='test_key', value='test_value')
    
    try:
        storage.apply_log_entry(log_entry)
        assert False, "Expected ValueError for invalid operation"
    except ValueError as e:
        assert str(e) == 'Unknown operation: INVALID'
    
def test_get_non_existent_key_returns_none():
    """
    Test that retrieving a non-existent key returns None.
    """
    storage = Storage()
    
    assert storage.get('non_existent_key') is None
    