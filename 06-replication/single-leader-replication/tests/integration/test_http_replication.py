"""HTTP replication integration tests.

Add tests here once each node runs as a separate process and exposes an
internal endpoint for receiving replication log entries.

The first scenario should verify that a write sent to a leader on one port is
replicated to a follower on a different port. Mark those tests with
``pytest.mark.integration``.
"""
