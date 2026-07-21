"""
config.py

Configuration to represent a running node's environment.
"""

class Config:
    def __init__(self, node_id: str, address: str) -> None:
        self._node_id = node_id
        self._address = address

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def address(self) -> str:
        return self._address
