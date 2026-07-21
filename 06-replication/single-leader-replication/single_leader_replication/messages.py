"""
messages.py

Message model for single-leader replication system.
"""

from dataclasses import dataclass
from single_leader_replication.models import LogEntry

@dataclass
class AppendEntryMessage:
    """
    Represents a message containing a log entry for replication.
    """
    sender_id: str
    receiver_id: str
    log_entry: LogEntry
    
@dataclass
class WriteRequestMessage:
    """
    Represents a message for a write request to the leader node.
    """
    key: str
    value: str
    
@dataclass
class ReadRequestMessage:
    """
    Represents a message for a read request to the leader node.
    """
    request_id: str
    key: str

@dataclass
class ReadResponseMessage:
    """
    Represents a message containing the response to a read request.
    """
    request_id: str
    key: str
    value: str | None
    
@dataclass
class PromoteToLeaderMessage:
    """
    Represents a message to promote a node to leader.
    """
    pass
    
@dataclass
class DemoteToFollowerMessage:
    """
    Represents a message to demote a node to follower.
    """
    pass
    
@dataclass
class ConfigureFollowersMessage:
    """
    Represents a message to configure followers for the leader node.
    """
    leader_id: str
    follower_ids: list[str]
    
@dataclass
class GetNodeStateRequestMessage:
    """
    Represents a message to request the state of a node.
    """
    request_id: str
    
@dataclass
class GetNodeStateResponseMessage:
    """
    Represents a message containing the state of a node in response to a request.
    """
    request_id: str
    node_id: str
    role: str
    last_applied_index: int