"""
config.py

Configuration to represent a running node's environment.
"""

class Config:
    def __init__(self, node_id: str, role: str, address: str, peers: dict[str, str], follower_ids: list[str]):
        self._node_id = node_id
        self._role = role
        self._address = address
        self._peers = peers
        self._follower_ids = follower_ids

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def role(self) -> str:
        return self._role

    @property
    def address(self) -> str:
        return self._address

    @property
    def peers(self) -> dict[str, str]:
        return self._peers

    @property
    def follower_ids(self) -> list[str]:
        return self._follower_ids