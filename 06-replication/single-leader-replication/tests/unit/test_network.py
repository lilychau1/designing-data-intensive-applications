"""
test_network.py

Unit tests for in-memory network membership and message delivery.
"""

import pytest

from single_leader_replication.models import LogEntry
from single_leader_replication.network import Network
from single_leader_replication.node import Node


def test_send_delivers_a_log_entry_to_a_registered_follower() -> None:
    network = Network()
    leader = Node(role='leader')
    follower = Node()
    entry = LogEntry(index=1, operation='SET', key='colour', value='blue')
    network.register_node(leader)
    network.register_node(follower)

    network.send(leader.id, follower.id, entry)

    assert follower.read('colour') == 'blue'
    assert follower.last_applied_index == 1
    assert follower.log == [entry]


def test_send_rejects_an_unregistered_sender() -> None:
    network = Network()
    leader = Node(role='leader')
    follower = Node()
    network.register_node(follower)

    with pytest.raises(ValueError, match='must be registered'):
        network.send(leader, follower, LogEntry(index=1, operation='SET', key='a', value=1))


def test_send_rejects_an_unregistered_receiver() -> None:
    network = Network()
    leader = Node(role='leader')
    follower = Node()
    network.register_node(leader)

    with pytest.raises(ValueError, match='must be registered'):
        network.send(leader, follower, LogEntry(index=1, operation='SET', key='a', value=1))


def test_send_rejects_delivery_to_the_same_node() -> None:
    network = Network()
    leader = Node(role='leader')
    network.register_node(leader)

    with pytest.raises(ValueError, match='cannot be the same'):
        network.send(leader.id, leader.id, LogEntry(index=1, operation='SET', key='a', value=1))

