"""
test_config.py

Unit tests for the Config class in config.py.
"""
from single_leader_replication.config import Config

def test_config_initialisation():
    config = Config(
        node_id='node-1',
        role='leader',
        address='127.0.0.1:8001',
        peers={
            'node-2': '127.0.0.1:8002',
            'node-3': '127.0.0.1:8003', 
        },
        follower_ids=['node-2', 'node-3']
    )

    assert config.node_id == 'node-1'
    assert config.role == 'leader'
    assert config.address == '127.0.0.1:8001'
    assert config.peers == {
        'node-2': '127.0.0.1:8002',
        'node-3': '127.0.0.1:8003',
    }
    assert config.follower_ids == ['node-2', 'node-3']