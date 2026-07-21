"""
app.py

Exposes the HTTP API for interacting with a database node. 

This module should remain thin. It translates HTTP requests into calls
to the storage engine and returns responses to clients. 

As the project evolves, requests will eventually be delegated to a Node
object instead of directly interacting with Storage. 

"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from single_leader_replication.models import SetRequest, ValueResponse
from single_leader_replication.cluster import Cluster
from single_leader_replication.config import Config

def make_configs() -> list[Config]:
    """Create a list of Config objects for the cluster nodes."""
    return [
        Config(node_id='node-1', address='http://localhost:8001'),
        Config(node_id='node-2', address='http://localhost:8002'),
        Config(node_id='node-3', address='http://localhost:8003')
    ]

cluster = Cluster(
    node_configs=make_configs(), 
    leader_node_id='node-1'
)

@asynccontextmanager
async def lifespan(app: FastAPI): 
    # Start all node and network processes
    cluster.start()
    
    yield # This is where the application runs
    
    # Stop all node and network processes
    cluster.stop()

app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------------------------
# Leader API
# ---------------------------------------------------------------------------

@app.post(
    "/set",
    response_model=ValueResponse,
)
def set_value(request: SetRequest) -> ValueResponse:
    """
    Write a key-value pair through the current leader.
    """

    leader_id = cluster.leader_id

    if leader_id is None:
        raise HTTPException(
            status_code=503,
            detail="No leader available",
        )

    cluster.write(
        request.key,
        request.value,
    )

    return ValueResponse(
        node_id=leader_id,
        key=request.key,
        value=request.value,
    )


@app.get(
    "/get/{key}",
    response_model=ValueResponse,
)
def get_value(key: str) -> ValueResponse:
    """
    Read a value from the current leader.
    """

    leader_id = cluster.leader_id

    if leader_id is None:
        raise HTTPException(
            status_code=503,
            detail="No leader available",
        )

    value = cluster.read(key)

    return ValueResponse(
        node_id=leader_id,
        key=key,
        value=value,
    )


# ---------------------------------------------------------------------------
# Direct node API
# ---------------------------------------------------------------------------

@app.get(
    "/nodes/{node_id}/get/{key}",
    response_model=ValueResponse,
)
def get_value_from_node(
    node_id: str,
    key: str,
) -> ValueResponse:
    """
    Read a value directly from a specific node.

    This endpoint is primarily useful for demonstrating and testing
    replication between nodes.
    """

    try:
        value = cluster.read_from_node(
            node_id=node_id,
            key=key,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return ValueResponse(
        node_id=node_id,
        key=key,
        value=value,
    )