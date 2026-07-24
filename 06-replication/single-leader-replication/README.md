# Single-Leader Replication

A small distributed in-memory key-value database demonstrating the core concepts behind **single-leader replication**, including replication logs, leader election, node removal, node restart, inter-process communication, and failover.

The project consists of a Python/FastAPI backend that runs a small cluster of database nodes and a React/TypeScript frontend that provides a visual interface for observing and interacting with the cluster.

The project is intentionally simplified and is designed as a learning project rather than a production-ready distributed database.

<img width="1133" height="843" alt="image" src="https://github.com/user-attachments/assets/27701525-49c1-4e88-91e5-86de33f9bcb3" />

---

## Overview

The system models a distributed in-memory key-value database consisting of:

- one leader node;
- multiple follower nodes;
- separate operating-system processes for each node;
- a dedicated network process for routing messages between nodes;
- inter-process communication using `multiprocessing.Queue`;
- replication logs for ordered writes;
- leader failover and election;
- follower reconfiguration after topology changes;
- node removal and restart;
- direct reads from individual replicas;
- a FastAPI HTTP API; and
- a React/TypeScript frontend for visualising cluster state and events.

The main purpose of the project is to make the concepts of replication, process isolation, message passing, and failover concrete and easy to experiment with.

---

# Architecture

The project is split into a backend distributed-system simulation and a frontend visualisation.

```
                         Browser
                            |
                            | HTTP
                            v
                  +---------------------+
                  | React / TypeScript   |
                  |      Frontend        |
                  +---------------------+
                            |
                            | REST API
                            v
                  +---------------------+
                  |       FastAPI        |
                  |       app.py         |
                  +---------------------+
                            |
                            v
                  +---------------------+
                  |       Cluster       |
                  |      Controller     |
                  +---------------------+
                            |
                     Client request
                        queues
                            |
                            v
       +---------------------------------------------+
       |              Node Processes                 |
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
               |     Router     |
               +----------------+
                       |
                       v
                Node process inboxes
```

Each node runs in its own operating-system process.

The `NetworkProcess` acts as a simple in-memory message router. Node processes send outgoing messages to the network process, which routes them to the appropriate node inbox.

The `Cluster` coordinates the overall system, including:

- starting and stopping node processes;
- configuring the leader and followers;
- sending client requests to the leader;
- collecting node state;
- electing a new leader;
- removing nodes;
- restarting previously removed nodes;
- reconfiguring follower relationships; and
- maintaining cluster membership and historical node state.

The React frontend communicates with the FastAPI application and visualises the current cluster state.

---

# Backend

The backend is implemented using:

- Python 3.12
- FastAPI
- Pydantic
- Poetry
- `multiprocessing.Process`
- `multiprocessing.Queue`

The backend is responsible for running the replication cluster simulation.

---

# Frontend

The frontend is implemented using:

- React
- TypeScript
- Vite

The frontend provides a visual interface for observing the cluster.

It currently provides:

- current leader identification;
- visual node cards;
- leader and follower roles;
- node running, stopped, and removed status;
- last applied replication-log index;
- node removal controls;
- node restart controls;
- leader election events;
- node removal events;
- node restart events; and
- an event timeline showing cluster changes.

The frontend is intended to be run locally alongside the FastAPI backend.

It is not currently deployed as a public website.

---

# Cluster Lifecycle

A typical cluster starts with three nodes:

```
             Leader
             Node 1
             /    \
            /      \
           v        v
        Node 2    Node 3
       follower  follower
```

If the leader is removed:

```
             Node 1
             REMOVED
                X

             Node 2
             Node 3
```

The cluster selects a new leader from the remaining active nodes.

For example:

```
             Leader
             Node 3
                |
                v
             Node 2
            follower
```

The frontend displays this change in the event timeline:

```
Node node-1 was removed from the cluster.

Leader changed from node-1 to node-3.
```

A previously removed node can then be restarted:

```
             Leader
             Node 3
             /    \
            v      v
         Node 2  Node 1
        follower follower
```

The restarted node is added back to the active cluster and configured as a follower of the current leader.

If the cluster has no leader when a node is restarted, the restarted node can become the new leader.

---

# Write Flow

A client write is sent to the current leader.

```
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
2. creates a replication log entry;
3. appends and applies the entry locally;
4. sends replication messages through the network process; and
5. followers apply the replicated log entries in order.

The implementation is intentionally simplified. It does not implement a production-grade quorum acknowledgement protocol or durable write-ahead log.

The frontend can be used to observe the `last_applied_index` of each node and demonstrate replication progress.

---

# Read Flow

A normal read is served by the current leader.

```
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

The API response identifies the node that served the read:

```
{
  "node_id": "node-1",
  "key": "name",
  "value": "Alice"
}
```

The project also provides a direct node-read endpoint.

This makes it possible to inspect individual replicas and demonstrate that replicated state exists across the cluster.

For example:

```
GET /nodes/node-1/get/name
GET /nodes/node-2/get/name
GET /nodes/node-3/get/name
```

Each request reads directly from the selected node.

---

# Leader Failover

When the current leader is removed, the cluster:

1. stops the leader process;
2. removes the leader from the active cluster membership;
3. collects state from the remaining active nodes;
4. selects the most up-to-date running node;
5. promotes the selected node to leader;
6. configures the remaining active nodes as followers; and
7. continues accepting writes through the new leader.

Leader selection is based primarily on the latest applied replication-log index.

If multiple nodes have the same latest index, the node ID is used as a deterministic tie-breaker.

The frontend records leader changes in the event timeline.

Example:

```
Node node-1 was removed from the cluster.

Leader changed from node-1 to node-3.
```

---

# Node Restart

A previously removed node can be restarted through the frontend or API.

The restart process:

1. creates a new node inbox;
2. recreates the `NodeProcess`;
3. creates a new operating-system process;
4. adds the node back to active cluster membership;
5. starts the node process;
6. restores the node as a follower if a leader already exists;
7. promotes the restarted node if no leader exists; and
8. reconfigures the current leader's follower list.

The frontend records the restart as an event.

For example:

```
Node node-1 was restarted and added back to the cluster.
```

The implementation currently treats a restarted node as a new runtime process. Persistent storage and durable log recovery are not implemented.

---

# What the Project Demonstrates

The implementation currently demonstrates:

- single-leader replication;
- ordered replication-log entries;
- replication between leader and followers;
- duplicate-entry protection;
- out-of-order replication detection;
- follower catch-up;
- separate operating-system processes for each node;
- a dedicated network routing process;
- inter-process communication using `multiprocessing.Queue`;
- request and response message types;
- leader and follower role transitions;
- collecting state from independent node processes;
- selecting the most up-to-date node during failover;
- leader removal;
- automatic leader election;
- follower reconfiguration after node removal;
- continuing writes after leader failover;
- direct reads from individual nodes;
- restarting previously removed nodes;
- adding restarted nodes back to the cluster;
- leader election when no leader is available;
- FastAPI HTTP endpoints;
- a React/TypeScript cluster visualisation; and
- an event timeline for cluster topology and leadership changes.

---

# Installation and Testing

## Requirements

- Python 3.12
- Poetry
- Node.js and npm

---

## Backend Installation

From the backend project directory:

```
cd 06-replication/single-leader-replication
```

Install Python dependencies:

```
poetry install
```

---

## Frontend Installation

From the repository root:

```
cd frontend
```

Install JavaScript dependencies:

```
npm install
```

---

# Running the Application

The application consists of two separate processes:

```
React frontend
      |
      | HTTP
      v
FastAPI backend
      |
      v
Replication cluster
```

Both the backend and frontend need to be running locally.

---

## 1. Start the Backend

From:

```
06-replication/single-leader-replication
```

run:

```
poetry run uvicorn single_leader_replication.app:app --reload
```

The FastAPI application will be available at:

```
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```
http://127.0.0.1:8000/docs
```

The FastAPI application creates the cluster and starts the node and network processes when the application starts.

When the application shuts down, the cluster processes are stopped.

---

## 2. Start the Frontend

Open another terminal and navigate to:

```
frontend
```

Run:

```
npm run dev
```

Vite will provide a local development URL, typically:

```
http://localhost:5173
```

Open that URL in a browser.

The frontend communicates with the FastAPI backend running on port `8000`.

---

## 3. Run the Full System

The expected setup is:

Terminal 1:

```
cd 06-replication/single-leader-replication

poetry run uvicorn single_leader_replication.app:app --reload
```

Terminal 2:

```
cd frontend

npm run dev
```

Then open the Vite development URL in your browser.

---

# Testing

Run the complete backend test suite:

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
- node restart;
- replication after failover;
- direct node reads; and
- FastAPI integration behaviour.

---

# API Endpoints

## Write Through the Leader

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

Example response:

```
{
  "node_id": "node-1",
  "key": "name",
  "value": "Alice"
}
```

The request is sent to the current leader and replicated to the followers.

---

## Read From the Leader

```
GET /get/{key}
```

Example:

```
curl http://127.0.0.1:8000/get/name
```

Example response:

```
{
  "node_id": "node-1",
  "key": "name",
  "value": "Alice"
}
```

The `node_id` field identifies which node served the read.

---

## Read Directly From a Specific Node

```
GET /nodes/{node_id}/get/{key}
```

Example:

```
curl http://127.0.0.1:8000/nodes/node-2/get/name
```

Example response:

```
{
  "node_id": "node-2",
  "key": "name",
  "value": "Alice"
}
```

This endpoint is primarily intended for testing and demonstrating replication.

After writing:

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

Each active node should return the replicated value with the corresponding `node_id`.

---

## Get Cluster Status

```
GET /cluster/node-statuses
```

Returns information about all known nodes, including nodes that have been removed from the active cluster.

Example:

```
{
  "leader_id": "node-3",
  "nodes": [
    {
      "node_id": "node-1",
      "role": "follower",
      "status": "removed",
      "last_applied_index": 0
    },
    {
      "node_id": "node-2",
      "role": "follower",
      "status": "running",
      "last_applied_index": 1
    },
    {
      "node_id": "node-3",
      "role": "leader",
      "status": "running",
      "last_applied_index": 1
    }
  ]
}
```

---

## Get Active Cluster Status

```
GET /cluster/active-node-statuses
```

Returns information about currently active nodes.

Removed nodes are excluded from the active cluster view.

---

## Get a Specific Node

```
GET /cluster/nodes/{node_id}
```

Returns the current or last known state of a node.

---

## Remove a Node

```
POST /cluster/nodes/{node_id}/remove
```

Removes a node from the active cluster.

If the removed node is the leader, a new leader is elected from the remaining active nodes.

---

## Restart a Node

```
POST /cluster/nodes/{node_id}/restart
```

Restarts a previously removed node and adds it back to the active cluster.

If a leader exists, the restarted node rejoins as a follower.

If no leader exists, the restarted node can become the new leader.

---

# Example Demonstration

A simple demonstration of the system can follow these steps.

### 1. Start the cluster

Initially:

```
node-1  LEADER
node-2  FOLLOWER
node-3  FOLLOWER
```

### 2. Write data

```
curl -X POST http://127.0.0.1:8000/set \
  -H 'content-type: application/json' \
  -d '{"key": "name", "value": "Alice"}'
```

### 3. Check replication

Read the value from each node:

```
curl http://127.0.0.1:8000/nodes/node-1/get/name

curl http://127.0.0.1:8000/nodes/node-2/get/name

curl http://127.0.0.1:8000/nodes/node-3/get/name
```

### 4. Remove the leader

Remove `node-1`:

```
curl -X POST \
  http://127.0.0.1:8000/cluster/nodes/node-1/remove
```

The cluster elects a new leader.

For example:

```
node-1  REMOVED
node-2  FOLLOWER
node-3  LEADER
```

### 5. Write through the new leader

The cluster can continue accepting writes through the newly elected leader.

### 6. Restart the removed node

```
curl -X POST \
  http://127.0.0.1:8000/cluster/nodes/node-1/restart
```

The node is added back to the active cluster.

The resulting cluster may be:

```
node-1  FOLLOWER
node-2  FOLLOWER
node-3  LEADER
```

### 7. Observe the frontend

The React frontend provides a visual representation of:

- the current leader;
- follower nodes;
- node status;
- replication-log progress;
- node removal;
- node restart; and
- leader election events.

---

# Project Layout

```
designing-data-intensive-applications/
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── clusterApi.tsx
│   │   ├── components/
│   │   │   ├── ClusterView.tsx
│   │   │   ├── NodeCard.tsx
│   │   │   └── EventTimeline.tsx
│   │   ├── types/
│   │   │   ├── cluster.ts
│   │   │   └── events.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
└── 06-replication/
    └── single-leader-replication/
        ├── single_leader_replication/
        │   ├── app.py
        │   ├── cluster.py
        │   ├── config.py
        │   ├── messages.py
        │   ├── models.py
        │   ├── network_process.py
        │   ├── node_process.py
        │   ├── node.py
        │   ├── replication_log.py
        │   └── storage.py
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

# Current Limitations

This project is intentionally simplified and is not intended to be a production-ready distributed database.

Current limitations include:

- all data is stored in memory;
- there is no durable storage;
- node processes are local operating-system processes;
- the network is simulated using `multiprocessing.Queue`;
- there is no real network transport between database nodes;
- there is no network partition simulation;
- there is no message persistence;
- there is no quorum or acknowledgement protocol;
- writes do not require confirmation from a configurable number of replicas;
- there is no automatic failure detector;
- leader failure is simulated by explicitly removing a node;
- there is no persistent cluster membership;
- there is no snapshotting or log compaction;
- there is no transaction support;
- restarted nodes do not recover from durable persistent storage; and
- leader election is a simplified deterministic selection process rather than a production consensus algorithm such as Raft.

The frontend is also a local development interface rather than a deployed production application.

These constraints are deliberate. The purpose of the project is to make the core concepts of single-leader replication, process isolation, message passing, and failover concrete and easy to experiment with.

---

# Learning Goals

This project is part of a broader exploration of the concepts described in Martin Kleppmann's _Designing Data-Intensive Applications_.

The main goal is to understand how a replicated system can be decomposed into independent processes and how those processes communicate through messages.

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
        |
        v
Node removal and restart
        |
        v
Visual cluster monitoring
```

