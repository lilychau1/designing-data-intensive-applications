# Designing Data-Intensive Applications

A collection of small Python projects built while studying concepts from
Martin Kleppmann's *Designing Data-Intensive Applications*. Each project is a
learning implementation: the goal is to make a distributed-systems concept
concrete, not to provide production-ready infrastructure.

## Projects

| Chapter        | Project                                                               | Focus                                                                                                      |
| -------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 6. Replication | [Single-leader replication](06-replication/single-leader-replication) | Replicated writes, follower catch-up, process separation, leader failover, and inter-process messaging |

---

# Single-leader replication

The current project models a small distributed in-memory key-value database
using a single-leader replication architecture.

The system consists of:

- one leader node;
- multiple follower nodes;
- separate operating-system processes for each node;
- a dedicated network process for routing messages between nodes;
- inter-process communication using `multiprocessing.Queue`;
- replication logs for ordered writes;
- leader failover and election;
- follower reconfiguration after topology changes; and
- a FastAPI interface for interacting with the cluster.

The project is intentionally simplified and is designed to demonstrate the
fundamental ideas behind single-leader replication rather than provide
production-ready distributed storage.

## Architecture

The system is split into several layers.

```text
                         HTTP Client
                              |
                              v
                     +----------------+
                     |    FastAPI     |
                     |     app.py     |
                     +----------------+
                              |
                              v
                     +----------------+
                     |    Cluster     |
                     |   Controller   |
                     +----------------+
                              |
                    Client request queues
                              |
                              v
        +---------------------------------------------+
        |             Node Processes                  |
        |                                             |
        |  +----------+   +----------+   +----------+ |
        |  |  Node 1  |   |  Node 2  |   |  Node 3  | |
        |  |  Leader  |   | Follower |   | Follower | |
        |  +----------+   +----------+   +----------+ |
        |       |               |               |      |
        +-------|---------------|---------------|------+
                |               |               |
                |   Outgoing    |               |
                +-------+-------+---------------+
                        |
                        v
                +----------------+
                | NetworkProcess |
                |    Router      |
                +----------------+
                        |
                        v
                Node process inboxes
```

Each node runs in its own operating-system process.

The `NetworkProcess` acts as a simple in-memory message router. Node processes
send messages to the network process, which then routes them to the appropriate
node inbox.

The `Cluster` coordinates the overall system, including:

- starting and stopping processes;
- configuring the leader and followers;
- sending client requests to the leader;
- collecting node state;
- electing a new leader;
- removing failed nodes; and
- reconfiguring follower relationships.

---

### Write flow

A client write is sent to the current leader.

```text
Client
  |
  | POST /set
  v
FastAPI
  |
  v
Cluster.write()
  |
  v
Leader NodeProcess
  |
  | append log entry
  | apply locally
  |
  +--------------------+
  |                    |
  v                    v
NetworkProcess      Leader storage
  |
  +------------------+
  |                  |
  v                  v
Follower 1        Follower 2
  |                  |
  v                  v
Apply log entry   Apply log entry
```

The leader:

1. receives the write request;
1. creates a replication log entry;
1. appends and applies the entry locally;
1. sends the entry to each follower through the network process; and
1. followers apply the entry in order.

---

### Read flow

A normal read is served by the current leader.

```text
Client
  |
  | GET /get/name
  v
FastAPI
  |
  v
Cluster.read()
  |
  v
Current Leader
  |
  v
Response
```

The API response includes the node that served the request:

```text
{
  "node_id": "node-1",
  "key": "name",
  "value": "Alice"
}
```

The project also provides a direct node-read endpoint. This makes it possible
to inspect individual replicas and demonstrate that replicated state exists on
each node.

```text
GET /nodes/node-1/get/name
GET /nodes/node-2/get/name
GET /nodes/node-3/get/name
```
Each request reads directly from the selected node.

---

### Leader failover

If the current leader is removed, the cluster:

1. stops the leader process;
1. removes the leader from the cluster membership;
1. collects state from the remaining nodes;
1. selects the most up-to-date node;
1. promotes the selected node to leader;
1. configures the remaining nodes as followers; and
1. continues accepting writes through the new leader.

```text
Before failure:

       Leader
       Node 1
       /    \
      v      v
   Node 2  Node 3
  follower follower


Node 1 fails
     X


After election:

       Leader
       Node 2
       |
       v
     Node 3
    follower
```

Leader selection is based on the latest applied replication-log index.

If multiple nodes have the same latest index, the node ID is used as a
deterministic tie-breaker.

---

### What the project demonstrates
The implementation currently demonstrates:

- single-leader replication;
- ordered replication-log entries;
- synchronous leader-to-follower replication;
- duplicate-entry protection;
- out-of-order replication detection;
- follower catch-up;
- separate processes for each node;
- a dedicated network routing process;
- inter-process communication using multiprocessing.Queue;
- request and response message types;
- leader and follower role transitions;
- collecting state from independent node processes;
- selecting the most up-to-date node during failover;
- leader removal and automatic leader election;
- follower reconfiguration after node removal;
- continuing writes after leader failover;
- direct reads from individual nodes; and
- a FastAPI interface for interacting with the cluster.

---
## Installation and testing

Requirements:

- Python 3.12
- Poetry

From the project directory:

```
cd 06-replication/single-leader-replication
```

Install dependencies:

```
poetry install
```
Run the complete test suite:

```
poetry run pytest
```
Run unit tests:

```
poetry run pytest tests/unit
```
Run integration tests:
```
poetry run pytest tests/integration
```
Run a specific test module:
```
poetry run pytest tests/unit/test_cluster.py -v
```
Run a specific integration test:
```
poetry run pytest tests/integration/test_cluster_systems.py -v
```
The test suite covers:

- storage behaviour;
- replication-log ordering;
- node state transitions;
- node replication behaviour;
- inter-process message handling;
- network routing;
- cluster configuration;
- leader election;
- leader failover;
- follower removal;
- replication after failover;
- direct node reads; and
- FastAPI integration behaviour.

---
## Running the API

From:
```
06-replication/single-leader-replication
```
start the application with:
```
poetry run uvicorn single_leader_replication.app:app --reload
```
The FastAPI application creates the cluster and starts the node and network
processes when the application starts.

When the application shuts down, the cluster processes are stopped.

The API will be available at:
```
http://127.0.0.1:8000
```
FastAPI's interactive API documentation is available at:
```
http://127.0.0.1:8000/docs
```
--- 
## API endpoints
### Write through the leader
```
POST /set
```
Request:
```
{
  "key": "name",
  "value": "Alice"
}
```
Example:
```
curl -X POST http://127.0.0.1:8000/set \
  -H 'content-type: application/json' \
  -d '{"key": "name", "value": "Alice"}'
```
Response:
```
{
  "node_id": "node-1",
  "key": "name",
  "value": "Alice"
}
```
The request is sent to the current leader and replicated to the followers.

### Read from the leader
```
GET /get/{key}
```
Example:
```
curl http://127.0.0.1:8000/get/name
```
Response:
```
{
  "node_id": "node-1",
  "key": "name",
  "value": "Alice"
}
```
The `node_id` field identifies which node served the read.

Read directly from a specific node
```
GET /nodes/{node_id}/get/{key}
```
Example:
```
curl http://127.0.0.1:8000/nodes/node-2/get/name
```
Response:
```
{
  "node_id": "node-2",
  "key": "name",
  "value": "Alice"
}
```
This endpoint is primarily intended for testing and demonstrating
replication.

For example, after writing:
```
curl -X POST http://127.0.0.1:8000/set \
  -H 'content-type: application/json' \
  -d '{"key": "name", "value": "Alice"}'
```
the same value can be read from each replica:
```
curl http://127.0.0.1:8000/nodes/node-1/get/name

curl http://127.0.0.1:8000/nodes/node-2/get/name

curl http://127.0.0.1:8000/nodes/node-3/get/name
```
Each node should return:
```
{
  "key": "name",
  "value": "Alice"
}
```
with the corresponding `node_id`.

---
## Project layout
```
06-replication/single-leader-replication/
├── single_leader_replication/
│   ├── app.py                  # FastAPI application and HTTP endpoints
│   ├── cluster.py              # Cluster coordination and leader election
│   ├── config.py               # Node configuration
│   ├── messages.py             # Inter-process message definitions
│   ├── models.py               # Shared data models
│   ├── network_process.py      # Network routing process
│   ├── node_process.py         # Process wrapper around node behaviour
│   ├── node.py                 # Node state and replication behaviour
│   ├── replication_log.py      # Ordered replication log
│   └── storage.py              # In-memory key-value storage
│
└── tests/
    ├── unit/
    │   ├── test_cluster.py
    │   ├── test_node.py
    │   ├── test_node_process.py
    │   ├── test_network_process.py
    │   ├── test_replication_log.py
    │   └── test_storage.py
    │
    └── integration/
        └── test_cluster_systems.py
```


---
## Current limitations

This project is intentionally simplified and is not intended to be a production-ready distributed database.

Current limitations include:

- all data is stored in memory;
- there is no durable storage;
- node processes are local operating-system processes;
- the network is simulated using multiprocessing.Queue;
- there is no real network transport;
- there is no network partition simulation;
- there is no message persistence;
- there is no quorum or acknowledgement protocol;
- writes do not require confirmation from a configurable number of replicas;
- there is no automatic failure detector;
- leader failure is simulated by explicitly removing a node;
- there is no persistent cluster membership;
- there is no snapshotting or log compaction;
- there is no transaction support; and
- leader election is a simplified deterministic selection process rather than a production consensus algorithm such as Raft.

These constraints are deliberate. The purpose of the project is to make the core concepts of single-leader replication, process isolation, message passing, and failover concrete and easy to experiment with.

---

## Learning goals

This project is part of a broader exploration of the concepts described in
Martin Kleppmann's _Designing Data-Intensive Applications_.

The main goal of this implementation is to understand how a replicated system
can be decomposed into independent processes and how those processes
communicate through messages.

The project focuses on the progression from:

```
Single in-memory node
        |
        v
Leader + followers
        |
        v
Replication log
        |
        v
Separate node processes
        |
        v
Inter-process messaging
        |
        v
Leader failure
        |
        v
Leader election
        |
        v
Continued replication
```
The implementation intentionally leaves more advanced distributed-systems
problems for future projects and experiments.