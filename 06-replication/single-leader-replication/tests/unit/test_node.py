"""
test_node.py

Unit tests for the Node state machine and local replication behaviour.
"""

import pytest

from single_leader_replication.models import LogEntry
from single_leader_replication.node import Node

from tests.helpers import make_config


def test_node_uses_supplied_id_and_has_follower_defaults() -> None:
    node = Node(
        config=make_config("node-1"),
    )

    assert node.id == "node-1"
    assert node.role == "follower"
    assert node.last_applied_index == 0
    assert node.log == []
    assert node.followers == []


@pytest.mark.parametrize("role", ["leader", "follower"])
def test_set_role_accepts_supported_roles(role: str) -> None:
    node = Node(
        config=make_config("node-1"),
    )

    node.set_role(role)

    assert node.role == role


def test_set_role_rejects_an_unknown_role() -> None:
    node = Node(
        config=make_config("node-1"),
    )

    with pytest.raises(
        ValueError,
        match="Role must be either",
    ):
        node.set_role("candidate")


def test_only_a_leader_can_add_a_follower() -> None:
    follower = Node(
        config=make_config("follower-1"),
    )

    with pytest.raises(
        ValueError,
        match="Only leader nodes",
    ):
        follower.add_follower("follower-2")


def test_leader_cannot_add_itself_as_a_follower() -> None:
    leader = Node(
        config=make_config("leader-1"),
        role="leader",
    )

    with pytest.raises(
        ValueError,
        match="cannot be its own follower",
    ):
        leader.add_follower(leader.id)


def test_adding_the_same_follower_twice_only_adds_it_once() -> None:
    leader = Node(
        config=make_config("leader-1"),
        role="leader",
    )

    leader.add_follower("follower-1")
    leader.add_follower("follower-1")

    assert leader.followers == ["follower-1"]


def test_clear_followers_removes_all_followers() -> None:
    leader = Node(
        config=make_config("leader-1"),
        role="leader",
    )

    leader.add_follower("follower-1")
    leader.add_follower("follower-2")

    leader.clear_followers()

    assert leader.followers == []


def test_promote_to_leader_changes_role() -> None:
    node = Node(
        config=make_config("node-1"),
    )

    node.promote_to_leader()

    assert node.role == "leader"


def test_promote_to_leader_clears_existing_followers() -> None:
    node = Node(
        config=make_config("node-1"),
    )

    node.promote_to_leader()
    node.add_follower("follower-1")

    node.promote_to_leader()

    assert node.role == "leader"
    assert node.followers == []


def test_demote_to_follower_changes_role() -> None:
    node = Node(
        config=make_config("node-1"),
        role="leader",
    )

    node.demote_to_follower()

    assert node.role == "follower"


def test_demote_to_follower_clears_followers() -> None:
    node = Node(
        config=make_config("node-1"),
        role="leader",
    )

    node.add_follower("follower-1")

    node.demote_to_follower()

    assert node.role == "follower"
    assert node.followers == []


def test_receive_log_entry_applies_the_next_entry() -> None:
    follower = Node(
        config=make_config("follower-1"),
    )

    entry = LogEntry(
        index=1,
        operation="SET",
        key="colour",
        value="blue",
    )

    follower.receive_log_entry(entry)

    assert follower.read("colour") == "blue"
    assert follower.last_applied_index == 1
    assert follower.log == [entry]


def test_receive_log_entry_ignores_a_duplicate() -> None:
    follower = Node(
        config=make_config("follower-1"),
    )

    first_entry = LogEntry(
        index=1,
        operation="SET",
        key="colour",
        value="blue",
    )

    duplicate_entry = LogEntry(
        index=1,
        operation="SET",
        key="colour",
        value="green",
    )

    follower.receive_log_entry(first_entry)
    follower.receive_log_entry(duplicate_entry)

    assert follower.read("colour") == "blue"
    assert follower.last_applied_index == 1
    assert follower.log == [first_entry]


def test_receive_log_entry_rejects_an_out_of_order_entry() -> None:
    follower = Node(
        config=make_config("follower-1"),
    )

    entry = LogEntry(
        index=2,
        operation="SET",
        key="colour",
        value="blue",
    )

    with pytest.raises(
        ValueError,
        match="out-of-order",
    ):
        follower.receive_log_entry(entry)


def test_follower_cannot_accept_client_writes() -> None:
    follower = Node(
        config=make_config("follower-1"),
    )

    with pytest.raises(
        ValueError,
        match="Only leader nodes",
    ):
        follower.write("colour", "blue")


def test_leader_write_appends_and_applies_a_log_entry_locally() -> None:
    leader = Node(
        config=make_config("leader-1"),
        role="leader",
    )

    entry = leader.write(
        "colour",
        "blue",
    )

    assert entry == LogEntry(
        index=1,
        operation="SET",
        key="colour",
        value="blue",
    )

    assert leader.log == [entry]
    assert leader.last_applied_index == 1
    assert leader.read("colour") == "blue"


def test_leader_can_write_multiple_entries() -> None:
    leader = Node(
        config=make_config("leader-1"),
        role="leader",
    )

    first_entry = leader.write(
        "colour",
        "blue",
    )

    second_entry = leader.write(
        "city",
        "London",
    )

    assert first_entry.index == 1
    assert second_entry.index == 2

    assert leader.last_applied_index == 2

    assert leader.read("colour") == "blue"
    assert leader.read("city") == "London"

    assert leader.log == [
        first_entry,
        second_entry,
    ]


def test_read_returns_none_for_a_missing_key() -> None:
    node = Node(
        config=make_config("node-1"),
    )

    assert node.read("missing") is None