"""
app.py

Exposes the HTTP API for interacting with a database node. 

This module should remain thin. It translates HTTP requests into calls
to the storage engine and returns responses to clients. 

As the project evolves, requests will eventually be delegated to a Node
object instead of directly interacting with Storage. 

"""

from fastapi import FastAPI, HTTPException

from single_leader_replication.models import SetRequest
from single_leader_replication.node import Node
from single_leader_replication.cluster import Cluster

app = FastAPI(title='Replicated Database')

# storage = Storage()
# replication_log = ReplicationLog()
# leader: Node = Node(role='leader')
# follower_1: Node = Node()
# follower_2: Node = Node()

# leader.add_follower(follower_1)
# leader.add_follower(follower_2)

node_1 = Node()
node_2 = Node()
node_3 = Node()

cluster = Cluster(
    nodes=[
        node_1,
        node_2,
        node_3
    ], 
    leader_node=node_1
)

@app.post('/set')
def set_value(request: SetRequest) -> dict[str, str]:
    """Store a key-value pair in the database."""
    cluster.leader.write(key=request.key, value=request.value)
    return {'status': 'success'}

@app.get('/get/{key}')
def get_value(key:str) -> dict[str, str | None]:
    """Retrieve a value from the database by key."""
    value = cluster.leader.read(key)
    if value is None: 
        raise HTTPException(status_code=404, detail='Key not found')
    return {'key': key, 'value': value}