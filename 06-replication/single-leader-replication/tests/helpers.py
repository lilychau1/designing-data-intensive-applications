# tests/conftest.py

from single_leader_replication.config import Config
from single_leader_replication.node import Node

def make_config(node_id: str) -> Config:
    return Config(
        node_id=node_id,
        address=f"localhost:{node_id}",
        peers={}
    )


def make_node(node_id: str, role: str = "follower", network=None) -> Node:
    return Node(
        config=make_config(node_id),
        role=role, 
        network=network
    )