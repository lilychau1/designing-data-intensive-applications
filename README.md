# Designing Data-Intensive Applications

A collection of small Python projects built while studying concepts from
Martin Kleppmann's *Designing Data-Intensive Applications*. Each project is a
learning implementation: the goal is to make a distributed-systems concept
concrete, not to provide production-ready infrastructure.

## Projects

| Chapter | Project | Focus |
| --- | --- | --- |
| 6. Replication | [Single-leader replication](06-replication/single-leader-replication) | Replicated writes, follower catch-up, leader failover, and an in-memory network layer |

## Single-leader replication

The current project models a small in-memory key-value database with one
leader and multiple followers. A write is appended to the leader's replication
log, applied locally, and delivered to each follower through a shared
`Network` abstraction.

```text
client write
    |
    v
leader Node ──append──> replication log ──apply──> leader storage
    |
    └────────────── Network.send() ─────────────> follower storage
```

It currently demonstrates:

- ordered replication-log entries;
- synchronous leader-to-follower replication;
- duplicate-entry protection;
- follower catch-up after missed writes;
- selecting the most up-to-date remaining node after leader removal; and
- a small FastAPI interface for writing and reading from the leader.

### Run it

Requirements: Python 3.12 and [Poetry](https://python-poetry.org/).

```bash
cd 06-replication/single-leader-replication
poetry install
PYTHONPATH=. poetry run python tests/test.py
```

The demonstration script prints the outcomes of storage, replication,
catch-up, duplicate-delivery, and failover scenarios.

### Run the API

From `06-replication/single-leader-replication`:

```bash
poetry run uvicorn single_leader_replication.app:app --reload
```

In another terminal:

```bash
curl -X POST http://127.0.0.1:8000/set \
  -H 'content-type: application/json' \
  -d '{"key": "colour", "value": "blue"}'

curl http://127.0.0.1:8000/get/colour
```

### Project layout

```text
06-replication/single-leader-replication/
├── single_leader_replication/
│   ├── app.py              # FastAPI endpoints
│   ├── cluster.py          # Leader selection and follower configuration
│   ├── network.py          # Registered-node message delivery
│   ├── node.py             # Node state and replication behaviour
│   ├── replication_log.py  # Ordered write log
│   └── storage.py          # In-memory key-value state
└── tests/test.py           # Executable learning scenarios
```

## Current limitations

Everything is deliberately in memory and synchronous. There is no durable
storage, real network transport, quorum/acknowledgement protocol, automatic
failure detection, or production-grade consensus algorithm. Those constraints
keep the examples focused on one idea at a time.
