"""
test_cluster.py

Unit tests for cluster orchestration, leader election,
node management, and message routing.
"""

from unittest.mock import MagicMock, patch
import pytest

from tests.helpers import make_configs

from single_leader_replication.cluster import Cluster
from single_leader_replication.config import Config
from single_leader_replication.messages import (
    ConfigureFollowersMessage,
    DemoteToFollowerMessage,
    GetNodeStateRequestMessage,
    GetNodeStateResponseMessage,
    PromoteToLeaderMessage,
    ReadRequestMessage,
    WriteRequestMessage,
)


def make_configs() -> list[Config]:
    return [
        Config(
            node_id="node-1",
            address="localhost:5001",
            peers={},
        ),
        Config(
            node_id="node-2",
            address="localhost:5002",
            peers={},
        ),
        Config(
            node_id="node-3",
            address="localhost:5003",
            peers={},
        ),
    ]


def test_cluster_initialises_node_processes() -> None:
    configs = make_configs()

    with patch(
        "single_leader_replication.cluster.NodeProcess"
    ) as mock_node_process:

        cluster = Cluster(configs)

    assert cluster.node_ids == [
        "node-1",
        "node-2",
        "node-3",
    ]

    assert set(cluster.processes.keys()) == {
        "node-1",
        "node-2",
        "node-3",
    }

    assert mock_node_process.call_count == 3

    created_configs = {
        call.kwargs["config"].node_id
        for call in mock_node_process.call_args_list
    }

    assert created_configs == {
        "node-1",
        "node-2",
        "node-3",
    }


def test_cluster_stores_supplied_leader_id() -> None:
    configs = make_configs()

    cluster = Cluster(
        configs,
        leader_node_id="node-2",
    )

    assert cluster.leader_id == "node-2"


def test_cluster_has_no_leader_when_none_supplied() -> None:
    configs = make_configs()

    cluster = Cluster(configs)

    assert cluster.leader_id is None


def test_configure_followers_sends_configuration_message() -> None:
    configs = make_configs()

    cluster = Cluster(
        configs,
        leader_node_id="node-1",
    )

    leader_queue = cluster._routes["node-1"]

    cluster.configure_followers()

    message = leader_queue.get()

    assert isinstance(message, ConfigureFollowersMessage)
    assert message.leader_id == "node-1"
    assert set(message.follower_ids) == {
        "node-2",
        "node-3",
    }


def test_configure_followers_does_nothing_without_leader() -> None:
    configs = make_configs()

    cluster = Cluster(configs)

    # This should not raise.
    cluster.configure_followers()


def test_choose_best_node_returns_node_with_latest_log_index() -> None:
    configs = make_configs()

    cluster = Cluster(configs)

    cluster.get_node_states = MagicMock(
        return_value={
            "node-1": GetNodeStateResponseMessage(
                request_id="request-1",
                node_id="node-1",
                role="follower",
                last_applied_index=1,
            ),
            "node-2": GetNodeStateResponseMessage(
                request_id="request-1",
                node_id="node-2",
                role="follower",
                last_applied_index=3,
            ),
            "node-3": GetNodeStateResponseMessage(
                request_id="request-1",
                node_id="node-3",
                role="follower",
                last_applied_index=2,
            ),
        }
    )

    assert cluster.choose_best_node() == "node-2"


def test_choose_best_node_uses_node_id_as_tiebreaker() -> None:
    configs = make_configs()

    cluster = Cluster(configs)

    cluster.get_node_states = MagicMock(
        return_value={
            "node-1": GetNodeStateResponseMessage(
                request_id="request-1",
                node_id="node-1",
                role="follower",
                last_applied_index=2,
            ),
            "node-2": GetNodeStateResponseMessage(
                request_id="request-1",
                node_id="node-2",
                role="follower",
                last_applied_index=2,
            ),
            "node-3": GetNodeStateResponseMessage(
                request_id="request-1",
                node_id="node-3",
                role="follower",
                last_applied_index=1,
            ),
        }
    )

    assert cluster.choose_best_node() == "node-2"


def test_choose_best_node_rejects_empty_cluster() -> None:
    cluster = Cluster([])

    with pytest.raises(
        RuntimeError,
        match="No nodes available",
    ):
        cluster.choose_best_node()


def test_elect_new_leader_promotes_best_node() -> None:
    configs = make_configs()

    cluster = Cluster(
        configs,
        leader_node_id="node-1",
    )

    cluster.choose_best_node = MagicMock(
        return_value="node-3"
    )

    cluster.elect_new_leader()

    assert cluster.leader_id == "node-3"

    # Old leader should receive demotion.
    old_leader_message = cluster._routes["node-1"].get()

    assert isinstance(
        old_leader_message,
        DemoteToFollowerMessage,
    )

    # New leader should receive promotion.
    new_leader_message = cluster._routes["node-3"].get()

    assert isinstance(
        new_leader_message,
        PromoteToLeaderMessage,
    )

    # New leader should receive follower configuration.
    configure_message = cluster._routes["node-3"].get()

    assert isinstance(
        configure_message,
        ConfigureFollowersMessage,
    )

    assert configure_message.leader_id == "node-3"
    assert set(configure_message.follower_ids) == {
        "node-1",
        "node-2",
    }


def test_elect_new_leader_without_existing_leader() -> None:
    configs = make_configs()

    cluster = Cluster(configs)

    cluster.choose_best_node = MagicMock(
        return_value="node-2"
    )

    cluster.elect_new_leader()

    assert cluster.leader_id == "node-2"

    promote_message = cluster._routes["node-2"].get()

    assert isinstance(
        promote_message,
        PromoteToLeaderMessage,
    )

    configure_message = cluster._routes["node-2"].get()

    assert isinstance(
        configure_message,
        ConfigureFollowersMessage,
    )


def test_elect_new_leader_rejects_empty_cluster() -> None:
    cluster = Cluster([])

    with pytest.raises(
        RuntimeError,
        match="No nodes available",
    ):
        cluster.elect_new_leader()


def test_get_node_states_sends_request_to_every_node() -> None:
    configs = make_configs()

    cluster = Cluster(configs)

    # Put responses into the state response queue before
    # calling get_node_states().
    request_id = "test-request"

    responses = [
        GetNodeStateResponseMessage(
            request_id=request_id,
            node_id="node-1",
            role="follower",
            last_applied_index=1,
        ),
        GetNodeStateResponseMessage(
            request_id=request_id,
            node_id="node-2",
            role="follower",
            last_applied_index=2,
        ),
        GetNodeStateResponseMessage(
            request_id=request_id,
            node_id="node-3",
            role="follower",
            last_applied_index=3,
        ),
    ]

    # Mock uuid.uuid4 so we know the request ID.
    with patch(
        "single_leader_replication.cluster.uuid.uuid4",
        return_value=request_id,
    ):
        for response in responses:
            cluster._state_responses.put(response)

        states = cluster.get_node_states()

    assert set(states.keys()) == {
        "node-1",
        "node-2",
        "node-3",
    }

    assert states["node-1"].last_applied_index == 1
    assert states["node-2"].last_applied_index == 2
    assert states["node-3"].last_applied_index == 3

    # Every node should have received a state request.
    for node_id in cluster.node_ids:
        message = cluster._routes[node_id].get()

        assert isinstance(
            message,
            GetNodeStateRequestMessage,
        )

        assert message.request_id == request_id


def test_write_sends_write_request_to_leader() -> None:
    configs = make_configs()

    cluster = Cluster(
        configs,
        leader_node_id="node-1",
    )

    cluster.write(
        "colour",
        "blue",
    )

    message = cluster._routes["node-1"].get()

    assert isinstance(
        message,
        WriteRequestMessage,
    )

    assert message.key == "colour"
    assert message.value == "blue"


def test_write_rejects_cluster_without_leader() -> None:
    configs = make_configs()

    cluster = Cluster(configs)

    with pytest.raises(
        RuntimeError,
        match="No leader available",
    ):
        cluster.write(
            "colour",
            "blue",
        )

def test_read_sends_read_request_to_leader() -> None:
    configs = make_configs()

    cluster = Cluster(
        configs,
        leader_node_id="node-1",
    )

    request_id = "test-request"

    response = MagicMock()
    response.request_id = request_id
    response.value = "blue"

    # Replace the real multiprocessing response queue with a mock.
    # This prevents the test from blocking on a real multiprocessing queue.
    cluster._client_responses = MagicMock()
    cluster._client_responses.get.return_value = response

    with patch(
        "single_leader_replication.cluster.uuid.uuid4",
        return_value=request_id,
    ):
        value = cluster.read("colour")

    assert value == "blue"

    # The request sent to the leader should be waiting in its inbox.
    message = cluster._routes["node-1"].get()

    assert isinstance(
        message,
        ReadRequestMessage,
    )

    assert message.request_id == request_id
    assert message.key == "colour"


def test_read_rejects_cluster_without_leader() -> None:
    configs = make_configs()

    cluster = Cluster(configs)

    with pytest.raises(
        RuntimeError,
        match="No leader available",
    ):
        cluster.read("colour")


def test_read_from_node_rejects_unknown_node() -> None:
    configs = make_configs()

    cluster = Cluster(configs)

    with pytest.raises(
        ValueError,
        match="Unknown node",
    ):
        cluster.read_from_node(
            "does-not-exist",
            "colour",
        )


def test_remove_follower_keeps_current_leader() -> None:
    configs = make_configs()

    cluster = Cluster(
        configs,
        leader_node_id="node-1",
    )

    # Replace the real process with a mock so the test does not
    # wait for an actual multiprocessing.Process.
    cluster._processes["node-2"] = MagicMock()

    # configure_followers() sends a message to the leader.
    # We don't need to test that behaviour here.
    cluster.configure_followers = MagicMock()

    cluster.remove_node("node-2")

    assert cluster.leader_id == "node-1"

    assert cluster.node_ids == [
        "node-1",
        "node-3",
    ]

    assert "node-2" not in cluster.processes
    assert "node-2" not in cluster._node_configs

    cluster.configure_followers.assert_called_once_with()


def test_remove_leader_elects_new_leader() -> None:
    configs = make_configs()

    cluster = Cluster(
        configs,
        leader_node_id="node-1",
    )

    # Replace the real process with a mock so remove_node()
    # does not wait for an actual multiprocessing.Process.
    cluster._processes["node-1"] = MagicMock()

    # Avoid the real leader-election logic, which would request
    # state from the node processes and wait for responses.
    cluster.elect_new_leader = MagicMock()

    cluster.remove_node("node-1")

    # remove_node() should clear the old leader before
    # calling elect_new_leader().
    assert cluster.leader_id is None

    assert cluster.node_ids == [
        "node-2",
        "node-3",
    ]

    assert "node-1" not in cluster.processes
    assert "node-1" not in cluster._node_configs

    cluster.elect_new_leader.assert_called_once_with()


def test_remove_unknown_node_does_nothing() -> None:
    configs = make_configs()

    cluster = Cluster(
        configs,
        leader_node_id="node-1",
    )

    original_node_ids = cluster.node_ids.copy()

    cluster.remove_node("does-not-exist")

    assert cluster.node_ids == original_node_ids
    assert cluster.leader_id == "node-1"