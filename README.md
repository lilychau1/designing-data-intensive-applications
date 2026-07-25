# Designing Data-Intensive Applications

A collection of small Python projects built while studying concepts from Martin Kleppmann's _Designing Data-Intensive Applications_. Each project is a learning implementation: the goal is to make distributed-systems concepts concrete rather than provide production-ready infrastructure.

## Projects

|Chapter|Project|Focus|
|---|---|---|
|6. Replication|[Single-leader replication](06-replication/single-leader-replication)|Replicated writes, follower catch-up, process separation, leader failover, and inter-process messaging|

---

# Single-leader replication

A small distributed in-memory key-value database that demonstrates **single-leader replication**.

The system consists of a leader and multiple follower nodes, with each node running in a separate operating-system process. Writes are handled by the leader and replicated to followers through an in-memory message-routing process.

<img width="1133" height="843" alt="image" src="https://github.com/user-attachments/assets/27701525-49c1-4e88-91e5-86de33f9bcb3" />

The project demonstrates:

- Leader and follower roles
- Ordered replication logs
- Replication of writes across multiple nodes
- Follower catch-up and reconfiguration
- Separate processes for individual database nodes
- Inter-process communication using `multiprocessing.Queue`
- A dedicated network routing process
- Leader removal and automatic leader election
- Failover to the most up-to-date available node
- Continued replication after leader failover
- Direct reads from individual replicas
- A FastAPI interface for interacting with the cluster

The implementation is intentionally simplified to make the core concepts of replication, process isolation, message passing, and failover easier to understand and experiment with.

# Learning Roadmap

The repository will gradually expand with projects exploring other topics from _Designing Data-Intensive Applications_.

The book covers the following major areas:

|Chapter|Topic|
|---|---|
|1|Reliable, Scalable, and Maintainable Applications|
|2|Data Models and Query Languages|
|3|Storage and Retrieval|
|4|Encoding and Evolution|
|5|Replication|
|6|Partitioning|
|7|Transactions|
|8|The Trouble with Distributed Systems|
|9|Consistency and Consensus|
|10|Batch Processing|
|11|Stream Processing|
|12|The Future of Data Systems|

The projects in this repository are developed incrementally as learning exercises, with each implementation focusing on a specific concept or group of concepts from the book.

For the full architecture, implementation details, API documentation, tests, and limitations, see the [Single-leader replication README](06-replication/single-leader-replication/README.md).
