"""
helper.py

Helper functions for tests.
"""
from single_leader_replication.config import Config


def make_config(node_id: str) -> Config:
    return Config(
        node_id=node_id,
        address=f"localhost:{node_id}",
    )


def make_configs() -> list[Config]:
    return [
        make_config("node-1"),
        make_config("node-2"),
        make_config("node-3"),
    ]