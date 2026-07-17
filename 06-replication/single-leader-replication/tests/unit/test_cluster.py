"""
test_cluster.py

Tests for cluster configuration, replication, and failover.
"""


import pytest

from single_leader_replication.cluster import Cluster
from single_leader_replication.models import LogEntry
from single_leader_replication.node import Node

from tests.helpers import make_node


def make_nodes() -> tuple[Node, Node, Node]:
    return make_node('node-1'), make_node('node-2'), make_node('node-3')


def test_cluster_configures_the_supplied_leader_and_shared_network() -> None:
    leader, follower_one, follower_two = make_nodes()

    cluster = Cluster([leader, follower_one, follower_two], leader_node=leader)

    assert cluster.leader is leader
    assert leader.role == 'leader'
    assert leader.network is not None
    assert follower_one.network is leader.network
    assert follower_two.network is leader.network


def test_cluster_leader_write_replicates_to_all_followers() -> None:
    leader, follower_one, follower_two = make_nodes()
    cluster = Cluster([leader, follower_one, follower_two], leader_node=leader)

    cluster.leader.write('colour', 'blue')

    assert leader.read('colour') == 'blue'
    assert follower_one.read('colour') == 'blue'
    assert follower_two.read('colour') == 'blue'


def test_leader_property_raises_when_no_leader_is_configured() -> None:
    cluster = Cluster([make_node('node-1')])

    with pytest.raises(RuntimeError, match='No leader'):
        _ = cluster.leader


def test_choose_best_node_returns_the_node_with_the_latest_log_entry() -> None:
    node_one, node_two, node_three = make_nodes()
    node_two.receive_log_entry(LogEntry(index=1, operation='SET', key='a', value=1))
    node_three.receive_log_entry(LogEntry(index=1, operation='SET', key='a', value=1))
    node_three.receive_log_entry(LogEntry(index=2, operation='SET', key='b', value=2))
    cluster = Cluster([node_one, node_two, node_three])

    assert cluster.choose_best_node() is node_three


def test_choose_best_node_rejects_an_empty_cluster() -> None:
    cluster = Cluster([])

    with pytest.raises(RuntimeError, match='No nodes available'):
        cluster.choose_best_node()


def test_elect_new_leader_promotes_the_most_up_to_date_node() -> None:
    node_one, node_two, node_three = make_nodes()
    node_three.receive_log_entry(LogEntry(index=1, operation='SET', key='a', value=1))
    cluster = Cluster([node_one, node_two, node_three])

    cluster.elect_new_leader()

    assert cluster.leader is node_three
    assert node_three.role == 'leader'


def test_removing_a_follower_keeps_the_current_leader() -> None:
    leader, follower_one, follower_two = make_nodes()
    cluster = Cluster([leader, follower_one, follower_two], leader_node=leader)

    cluster.remove_node(follower_one)

    assert cluster.leader is leader


def test_removing_a_leader_elects_the_most_up_to_date_node_and_replication_continues() -> None:
    old_leader, node_two, node_three = make_nodes()

    cluster = Cluster(
        [old_leader, node_two, node_three],
        leader_node=old_leader,
    )

    cluster.leader.write("before-failover", 1)

    latest = LogEntry(
        index=2,
        operation="SET",
        key="latest",
        value=2,
    )

    # Only node_three has the newest entry
    node_three.receive_log_entry(latest)

    # Bring node_two up before the new write
    node_two.receive_log_entry(latest)

    cluster.remove_node(old_leader)

    assert cluster.leader is node_three

    cluster.leader.write("after-failover", 3)

    assert node_two.read("after-failover") == 3