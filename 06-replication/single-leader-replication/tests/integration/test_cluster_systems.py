"""
test_cluster_systems.py

Integration tests for the full single-leader replication system.

These tests exercise the system through the Cluster API and verify
interaction between:

    Cluster
        |
        +-- NodeProcess
        |       |
        |       +-- Node
        |
        +-- NetworkProcess
                |
                +-- NodeProcess
                        |
                        +-- Node
"""

from single_leader_replication.cluster import Cluster
from tests.helpers import make_configs


def test_cluster_full_lifecycle() -> None:
    """
    Test the full lifecycle of a cluster:

    1. Start a cluster with an initial leader.
    2. Verify the initial leader and followers.
    3. Write data through the cluster.
    4. Verify data was replicated to all nodes.
    5. Remove the leader.
    6. Verify a new leader is elected.
    7. Write data through the new leader.
    8. Verify the new write is replicated.
    """

    cluster = Cluster(
        make_configs(),
        leader_node_id="node-1",
    )

    cluster.start()

    try:
        # ---------------------------------------------------------
        # 1. Verify initial leader election
        # ---------------------------------------------------------

        assert cluster.leader_id == "node-1"

        states = cluster.get_node_states()

        assert states["node-1"].role == "leader"
        assert states["node-2"].role == "follower"
        assert states["node-3"].role == "follower"

        # ---------------------------------------------------------
        # 2. Client writes to the leader
        # ---------------------------------------------------------

        cluster.write("name", "Alice")
        cluster.write("age", 30)

        # ---------------------------------------------------------
        # 3. Verify the leader can read the written values
        # ---------------------------------------------------------

        assert cluster.read("name") == "Alice"
        assert cluster.read("age") == 30

        # ---------------------------------------------------------
        # 4. Verify writes were replicated to all nodes
        # ---------------------------------------------------------

        assert cluster.read_from_node("node-1", "name") == "Alice"
        assert cluster.read_from_node("node-2", "name") == "Alice"
        assert cluster.read_from_node("node-3", "name") == "Alice"

        assert cluster.read_from_node("node-1", "age") == 30
        assert cluster.read_from_node("node-2", "age") == 30
        assert cluster.read_from_node("node-3", "age") == 30

        # ---------------------------------------------------------
        # 5. Verify all nodes have applied both log entries
        # ---------------------------------------------------------

        states = cluster.get_node_states()

        assert states["node-1"].last_applied_index == 2
        assert states["node-2"].last_applied_index == 2
        assert states["node-3"].last_applied_index == 2

        # ---------------------------------------------------------
        # 6. Simulate leader failure
        # ---------------------------------------------------------
        cluster.wait_for_replication(expected_index=1)
        cluster.remove_node("node-1")

        # ---------------------------------------------------------
        # 7. Verify a new leader was elected
        # ---------------------------------------------------------

        assert cluster.leader_id in {
            "node-2",
            "node-3",
        }

        states = cluster.get_node_states()

        new_leader_id = cluster.leader_id

        assert new_leader_id is not None
        assert states[new_leader_id].role == "leader"

        # Exactly one remaining node should be leader.
        leaders = [
            node_id
            for node_id, state in states.items()
            if state.role == "leader"
        ]

        assert len(leaders) == 1
        assert leaders[0] == new_leader_id

        # The old leader has been removed, so only two nodes remain.
        assert set(states.keys()) == {
            "node-2",
            "node-3",
        }

        # ---------------------------------------------------------
        # 8. Verify replicated data survived leader failure
        # ---------------------------------------------------------

        assert cluster.read("name") == "Alice"
        assert cluster.read("age") == 30

        assert cluster.read_from_node("node-2", "name") == "Alice"
        assert cluster.read_from_node("node-3", "name") == "Alice"

        # ---------------------------------------------------------
        # 9. Write through the new leader
        # ---------------------------------------------------------

        cluster.write("city", "London")

        # ---------------------------------------------------------
        # 10. Verify the new leader can read the new value
        # ---------------------------------------------------------

        assert cluster.read("city") == "London"

        # ---------------------------------------------------------
        # 11. Verify the new write was replicated
        # ---------------------------------------------------------

        for node_id in ("node-2", "node-3"):
            assert cluster.read_from_node(
                node_id,
                "city",
            ) == "London"

        # ---------------------------------------------------------
        # 12. Verify the new log entry was applied everywhere
        # ---------------------------------------------------------

        states = cluster.get_node_states()

        assert states["node-2"].last_applied_index == 3
        assert states["node-3"].last_applied_index == 3

    finally:
        cluster.stop()


def test_cluster_handles_multiple_writes() -> None:
    """
    Verify that multiple writes are replicated to every node.
    """

    cluster = Cluster(
        make_configs(),
        leader_node_id="node-1",
    )

    cluster.start()

    try:
        # ---------------------------------------------------------
        # 1. Perform multiple writes through the cluster
        # ---------------------------------------------------------

        for i in range(100):
            cluster.write(
                f"key-{i}",
                i,
            )

        # ---------------------------------------------------------
        # 2. Verify all writes reached every node
        # ---------------------------------------------------------

        for i in range(100):
            key = f"key-{i}"

            assert cluster.read_from_node(
                "node-1",
                key,
            ) == i

            assert cluster.read_from_node(
                "node-2",
                key,
            ) == i

            assert cluster.read_from_node(
                "node-3",
                key,
            ) == i

        # ---------------------------------------------------------
        # 3. Verify every node applied all 100 log entries
        # ---------------------------------------------------------

        states = cluster.get_node_states()

        assert states["node-1"].last_applied_index == 100
        assert states["node-2"].last_applied_index == 100
        assert states["node-3"].last_applied_index == 100

    finally:
        cluster.stop()


def test_cluster_elects_new_leader_after_removal() -> None:
    """
    Verify that removing the current leader causes a new leader
    to be elected based on node state.
    """

    cluster = Cluster(
        make_configs(),
        leader_node_id="node-1",
    )

    cluster.start()

    try:
        # ---------------------------------------------------------
        # 1. Verify initial leader
        # ---------------------------------------------------------

        assert cluster.leader_id == "node-1"

        # ---------------------------------------------------------
        # 2. Create replicated state
        # ---------------------------------------------------------

        cluster.write("name", "Alice")

        # ---------------------------------------------------------
        # 3. Remove the current leader
        # ---------------------------------------------------------
        cluster.wait_for_replication(expected_index=1)
        cluster.remove_node("node-1")

        # ---------------------------------------------------------
        # 4. Verify a new leader was elected
        # ---------------------------------------------------------

        assert cluster.leader_id in {
            "node-2",
            "node-3",
        }

        states = cluster.get_node_states()

        leaders = [
            node_id
            for node_id, state in states.items()
            if state.role == "leader"
        ]

        # There must be exactly one leader.
        assert len(leaders) == 1

        # The elected leader must match Cluster's leader ID.
        assert leaders[0] == cluster.leader_id

        # ---------------------------------------------------------
        # 5. Verify the new leader retained replicated state
        # ---------------------------------------------------------
        
        assert cluster.read("name") == "Alice"

        # ---------------------------------------------------------
        # 6. Verify the new leader can accept writes
        # ---------------------------------------------------------

        cluster.write("city", "London")

        assert cluster.read("city") == "London"

        # ---------------------------------------------------------
        # 7. Verify the new write was replicated
        # ---------------------------------------------------------

        for node_id in ("node-2", "node-3"):
            assert cluster.read_from_node(
                node_id,
                "city",
            ) == "London"

    finally:
        cluster.stop()


def test_cluster_removes_follower() -> None:
    """
    Verify that removing a follower leaves the leader and remaining
    follower operational.
    """

    cluster = Cluster(
        make_configs(),
        leader_node_id="node-1",
    )

    cluster.start()

    try:
        # ---------------------------------------------------------
        # 1. Verify initial cluster
        # ---------------------------------------------------------

        assert set(cluster.node_ids) == {
            "node-1",
            "node-2",
            "node-3",
        }

        assert cluster.leader_id == "node-1"

        # ---------------------------------------------------------
        # 2. Write initial data
        # ---------------------------------------------------------

        cluster.write("name", "Alice")

        # ---------------------------------------------------------
        # 3. Remove a follower
        # ---------------------------------------------------------
        cluster.wait_for_replication(expected_index=1)
        cluster.remove_node("node-3")

        # ---------------------------------------------------------
        # 4. Verify node was removed
        # ---------------------------------------------------------

        assert set(cluster.node_ids) == {
            "node-1",
            "node-2",
        }

        assert cluster.leader_id == "node-1"

        # ---------------------------------------------------------
        # 5. Verify remaining nodes still have existing state
        # ---------------------------------------------------------

        assert cluster.read_from_node(
            "node-1",
            "name",
        ) == "Alice"

        assert cluster.read_from_node(
            "node-2",
            "name",
        ) == "Alice"

        # ---------------------------------------------------------
        # 6. Verify new writes still replicate
        # ---------------------------------------------------------

        cluster.write("city", "London")

        assert cluster.read_from_node(
            "node-1",
            "city",
        ) == "London"

        assert cluster.read_from_node(
            "node-2",
            "city",
        ) == "London"

    finally:
        cluster.stop()