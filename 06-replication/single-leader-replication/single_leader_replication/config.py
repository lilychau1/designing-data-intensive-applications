"""
config.py

Configuration to represent a running node's environment.
"""

class Config:
    def __init__(self, node_id: str, address: str, peers: dict[str, str]):
        self._node_id = node_id
        self._address = address
        self._peers = peers

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def address(self) -> str:
        return self._address

    @property
    def peers(self) -> dict[str, str]:
        return self._peers
