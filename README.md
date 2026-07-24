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

A small distributed in-memory key-value database using a single-leader replication architecture.
<img width="1133" height="843" alt="image" src="https://github.com/user-attachments/assets/27701525-49c1-4e88-91e5-86de33f9bcb3" />
