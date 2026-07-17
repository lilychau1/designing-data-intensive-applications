"""
test_cluster_systems.py

Integration tests for the full single leader replication system.
"""

from single_leader_replication.cluster import Cluster
from tests.helpers import make_node

def test_cluster_full_lifecycle() -> None:
    # Create nodes
    node_1 = make_node('node-1')
    node_2 = make_node('node-2')
    node_3 = make_node('node-3')
    
    # Start cluster
    cluster = Cluster(
        [node_1, node_2, node_3],
        leader_node=node_1
    )
    
    # 1. Verify leader election
    assert cluster.leader is node_1
    assert node_1.role == 'leader'
    assert node_2.role == 'follower'
    assert node_3.role == 'follower'
    
    # 2. Client writes to leader
    cluster.leader.write('name', 'Alice')
    cluster.leader.write('age', 30)

    # 3. Verify leader-write and replication happened
    assert node_1.read('name') == 'Alice'
    assert node_1.read('age') == 30
    assert node_2.read('name') == 'Alice'
    assert node_2.read('age') == 30
    assert node_3.read('name') == 'Alice'
    assert node_3.read('age') == 30

    assert node_1.last_applied_index == 2
    assert node_2.last_applied_index == 2
    assert node_3.last_applied_index == 2
    
    # 4. Simulate leader failure
    cluster.remove_node(node_1)
    
    # 5. Verify new leader election
    new_leader = cluster.leader
    assert new_leader is not None
    assert new_leader is not node_1
    assert new_leader.role == 'leader'
    
    # 6. New leader accepts writes
    cluster.leader.write('city', 'London')
    
    # 7. Verify replication to remaining followers
    remaining_nodes = [node for node in cluster._nodes if node is not cluster.leader] 

    for node in remaining_nodes:
        assert node.read('city') == 'London'
        assert node.last_applied_index == 3
        
        
def test_cluster_handles_multiple_writes() -> None:
    leader, follower_one, follower_two = (
        make_node("leader"),
        make_node("follower-one"),
        make_node("follower-two"),
    )

    cluster = Cluster(
        [leader, follower_one, follower_two],
        leader_node=leader,
    )

    for i in range(100):
        cluster.leader.write(
            f"key-{i}",
            i,
        )

    for i in range(100):
        assert follower_one.read(f"key-{i}") == i
        assert follower_two.read(f"key-{i}") == i