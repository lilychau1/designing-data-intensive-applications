"""
models.py

Defines request, response, and domain models used by the application.

These models validate incoming client requests, represent replication
state, and ensure the API has well-defined contracts.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class SetRequest(BaseModel):
    """
    Request body for storing a key-value pair.
    """

    key: str
    value: Any


class ValueResponse(BaseModel):
    """
    Response returned when retrieving a value.
    """

    key: str
    value: Any


class LogEntry(BaseModel):
    """
    Single log entry representing a write operation.
    """

    index: int
    operation: str
    key: str
    value: Any


class NodeStatus(str, Enum):
    """
    Runtime status of a node process.
    """
    RUNNING = "running"
    STOPPED = "stopped"
    REMOVED = "removed"


class NodeRole(str, Enum):
    """
    Replication role of a node.
    """

    LEADER = "leader"
    FOLLOWER = "follower"


class NodeInfo(BaseModel):
    """
    Details for a single node in the cluster.
    """

    node_id: str
    role: NodeRole
    status: NodeStatus
    last_applied_index: int


class NodeStatusResponse(BaseModel):
    """
    Response returned when querying the status of the cluster nodes.
    """

    leader_id: str | None
    nodes: list[NodeInfo]