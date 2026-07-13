
"""
test_node.py

Unit tests for the Node state machine and replication behaviour.
"""


from unittest.mock import Mock

import pytest

from single_leader_replication.models import LogEntry
from single_leader_replication.node import Node


def test_node_uses_supplied_id_and_has_follower_defaults() -> None:
    node = Node(id='node-1')

    assert node.id == 'node-1'
    assert node.role == 'follower'
    assert node.network is None
    assert node.last_applied_index == 0
    assert node.log == []


def test_node_generates_an_id_when_one_is_not_supplied() -> None:
    node = Node()

    assert node.id


@pytest.mark.parametrize('role', ['leader', 'follower'])
def test_set_role_accepts_supported_roles(role: str) -> None:
    node = Node()

    node.set_role(role)

    assert node.role == role


def test_set_role_rejects_an_unknown_role() -> None:
    node = Node()

    with pytest.raises(ValueError, match='Role must be either'):
        node.set_role('candidate')


def test_only_a_leader_can_add_a_follower() -> None:
    follower = Node()

    with pytest.raises(ValueError, match='Only leader nodes'):
        follower.add_follower(Node())


def test_leader_cannot_add_itself_as_a_follower() -> None:
    leader = Node(role='leader')

    with pytest.raises(ValueError, match='cannot be its own follower'):
        leader.add_follower(leader.id)


def test_adding_the_same_follower_twice_only_replicates_once() -> None:
    transport = Mock()
    leader = Node(id='leader-1', role='leader', network=transport)
    follower = Node(id='follower-1')

    leader.add_follower(follower.id)
    leader.add_follower(follower.id)

    entry = leader.write('colour', 'blue')

    transport.send.assert_called_once_with(
        sender_id=leader.id,
        receiver_id=follower.id,
        log_entry_message=entry,
    )


def test_set_network_updates_the_network_property() -> None:
    node = Node()
    network = Mock()

    node.set_network(network)

    assert node.network is network


def test_receive_log_entry_applies_the_next_entry() -> None:
    follower = Node()
    entry = LogEntry(index=1, operation='SET', key='colour', value='blue')

    follower.receive_log_entry(entry)

    assert follower.read('colour') == 'blue'
    assert follower.last_applied_index == 1
    assert follower.log == [entry]


def test_receive_log_entry_ignores_a_duplicate() -> None:
    follower = Node()
    first_entry = LogEntry(index=1, operation='SET', key='colour', value='blue')
    duplicate_entry = LogEntry(index=1, operation='SET', key='colour', value='green')
    follower.receive_log_entry(first_entry)

    follower.receive_log_entry(duplicate_entry)

    assert follower.read('colour') == 'blue'
    assert follower.last_applied_index == 1
    assert follower.log == [first_entry]


def test_receive_log_entry_rejects_an_out_of_order_entry() -> None:
    follower = Node()
    entry = LogEntry(index=2, operation='SET', key='colour', value='blue')

    with pytest.raises(ValueError, match='out-of-order'):
        follower.receive_log_entry(entry)


def test_sync_follower_requires_a_network() -> None:
    leader = Node(role='leader')

    with pytest.raises(ValueError, match='Network is not set'):
        leader.sync_follower(Node())

def test_follower_cannot_accept_client_writes() -> None:
    follower = Node()

    with pytest.raises(ValueError, match='Only leader nodes'):
        follower.write('colour', 'blue')


def test_leader_write_appends_and_applies_a_log_entry_locally() -> None:
    leader = Node(role='leader')

    entry = leader.write('colour', 'blue')

    assert entry == LogEntry(index=1, operation='SET', key='colour', value='blue')
    assert leader.log == [entry]
    assert leader.last_applied_index == 1
    assert leader.read('colour') == 'blue'


def test_read_returns_none_for_a_missing_key() -> None:
    node = Node()

    assert node.read('missing') is None
