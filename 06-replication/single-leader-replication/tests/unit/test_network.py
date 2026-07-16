"""
test_network.py

Unit tests for in-memory network membership and message delivery.
"""

import pytest

from single_leader_replication.models import LogEntry
from single_leader_replication.network import Network

from tests.helpers import make_node


def test_send_delivers_a_log_entry_to_a_registered_follower() -> None:
    network = Network()
    leader = make_node(node_id='leader-1', role='leader')
    follower = make_node('follower-1')
    entry = LogEntry(index=1, operation='SET', key='colour', value='blue')
    network.register_node(leader)
    network.register_node(follower)

    network.send(leader.id, follower.id, entry)

    assert follower.read('colour') == 'blue'
    assert follower.last_applied_index == 1
    assert follower.log == [entry]

def test_follower_receives_replication_entry():
    follower = make_node('follower-1')

    entry = LogEntry(
        index=1,
        operation="SET",
        key="colour",
        value="blue",
    )

    follower.receive_log_entry(entry)

    assert follower.read("colour") == "blue"

def test_send_rejects_an_unregistered_sender() -> None:
    network = Network()
    leader = make_node(node_id='leader-1', role='leader')
    follower = make_node('follower-1')
    network.register_node(follower)

    with pytest.raises(ValueError, match='must be registered'):
        network.send(leader, follower, LogEntry(index=1, operation='SET', key='a', value=1))


def test_send_rejects_an_unregistered_receiver() -> None:
    network = Network()
    leader = make_node(node_id='leader-1', role='leader')
    follower = make_node('follower-1')
    network.register_node(leader)

    with pytest.raises(ValueError, match='must be registered'):
        network.send(leader, follower, LogEntry(index=1, operation='SET', key='a', value=1))


def test_send_rejects_delivery_to_the_same_node() -> None:
    network = Network()
    leader = make_node(node_id='leader-1', role='leader')
    network.register_node(leader)

    with pytest.raises(ValueError, match='cannot be the same'):
        network.send(leader.id, leader.id, LogEntry(index=1, operation='SET', key='a', value=1))

def test_register_node_rejects_duplicate_node_ids() -> None:
    network = Network()
    node1 = make_node('follower-1')
    node2 = make_node(node1.id)  # Create a second node with the same ID as node1

    network.register_node(node1)

    with pytest.raises(ValueError, match='already registered'):
        network.register_node(node2)