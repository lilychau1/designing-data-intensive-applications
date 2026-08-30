import { useEffect, useMemo, useState } from "react";

import {
  readFromLeader,
  readFromNode,
  writeData,
} from "../api/DataApi";

import {
  setNodeReplicationDelay,
} from "../api/ClusterApi";

import NodeReadStatusPanel, {
  type NodeReadSnapshot,
} from "../components/NodeReadStatusPanel";
import { getNodeReadSnapshots } from "../utils/getNodeReadSnapshots";
import type { NodeInfo } from "../types/cluster";

interface ReadYourOwnWritePageProps {
  nodes: NodeInfo[];
  leaderId: string | null;
  onClusterUpdated: () => Promise<void>;
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });
}

interface ScenarioResult {
  key: string;
  writtenValue: string;
  readValue: unknown;
  nodeId: string;
  lagSeconds?: number;
  delayedReadValue?: unknown;
  nodeSnapshots: NodeReadSnapshot[];
}

function displayValue(value: unknown): string {
  return value === null || value === undefined
    ? "(missing)"
    : String(value);
}

function isMissing(value: unknown): boolean {
  return value === null || value === undefined;
}

function ReadYourOwnWritePage({
  nodes,
  leaderId,
  onClusterUpdated,
}: ReadYourOwnWritePageProps) {


  const [lagSeconds, setLagSeconds] = useState(2);
  
  const [selectedFollowerId, setSelectedFollowerId] =
    useState("");

  const [value, setValue] = useState(
    "My new profile name"
  );

  const [unmitigatedResult, setUnmitigatedResult] =
    useState<ScenarioResult | null>(null);

  const [mitigatedResult, setMitigatedResult] =
    useState<ScenarioResult | null>(null);

  const [unmitigatedLoading, setUnmitigatedLoading] =
    useState(false);

  const [mitigatedLoading, setMitigatedLoading] =
    useState(false);

  const [message, setMessage] =
    useState<string | null>(null);

  const followers = useMemo(
    () =>
      nodes.filter(
        (node) =>
          node.node_id !== leaderId &&
          node.status === "running"
      ),
    [nodes, leaderId]
  );

  useEffect(() => {
    setSelectedFollowerId((currentFollowerId) => {
      const stillAvailable = followers.some(
        (node) => node.node_id === currentFollowerId
      );

      if (stillAvailable) {
        return currentFollowerId;
      }

      return followers[0]?.node_id ?? "";
    });
  }, [followers]);

  async function runUnmitigatedScenario() {
    if (!selectedFollowerId) {
      setMessage(
        "Select an active follower before running the demonstration."
      );
      return;
    }

    setUnmitigatedLoading(true);
    setMessage(null);
    setUnmitigatedResult(null);

    const key = `unmitigated-${crypto.randomUUID()}`;

    try {
      // Ensure that the selected replica receives replication later.
      await setNodeReplicationDelay(
        selectedFollowerId,
        lagSeconds
      );

      await onClusterUpdated();

      // The write is acknowledged by the leader.
      await writeData(key, value);

      // This intentionally bypasses the leader and may see stale data.
      const replicaRead = await readFromNode(
        selectedFollowerId,
        key
      );
      const nodeSnapshots = await getNodeReadSnapshots(nodes, key);

      setUnmitigatedResult({
        key,
        writtenValue: value,
        readValue: replicaRead.value,
        nodeId: selectedFollowerId,
        lagSeconds,
        nodeSnapshots,
      });
      
      await wait(lagSeconds * 1000);

        const caughtUpRead = await readFromNode(
        selectedFollowerId,
        key
        );

        setUnmitigatedResult((current) =>
        current?.key === key
            ? {
                ...current,
                delayedReadValue: caughtUpRead.value,
            }
            : current
        );

      setMessage(
        `Wrote "${key}" through the leader, then immediately read ${selectedFollowerId}.`
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Failed to run the unmitigated scenario."
      );
    } finally {
      setUnmitigatedLoading(false);
    }
  }

  async function readReplicaAgain() {
    if (!unmitigatedResult) {
      return;
    }

    try {
      const replicaRead = await readFromNode(
        unmitigatedResult.nodeId,
        unmitigatedResult.key
      );
      const nodeSnapshots = await getNodeReadSnapshots(
        nodes,
        unmitigatedResult.key
      );

      setUnmitigatedResult((current) =>
        current
          ? {
                ...current,
                readValue: replicaRead.value,
                nodeSnapshots,
            }
          : null
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Failed to read from the replica."
      );
    }
  }

  async function runMitigatedScenario() {
    if (!leaderId) {
      setMessage(
        "A leader is required for this demonstration."
      );
      return;
    }

    setMitigatedLoading(true);
    setMessage(null);
    setMitigatedResult(null);

    const key = `mitigated-${crypto.randomUUID()}`;

    try {
      await writeData(key, value);

      // Read-after-write strategy: read from the leader that accepted the write.
      const leaderRead = await readFromLeader(key);
      const nodeSnapshots = await getNodeReadSnapshots(nodes, key);

      setMitigatedResult({
        key,
        writtenValue: value,
        readValue: leaderRead.value,
        nodeId: leaderId,
        nodeSnapshots,
      });

      setMessage(
        `Wrote "${key}" and immediately read it from ${leaderId}.`
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Failed to run the mitigated scenario."
      );
    } finally {
      setMitigatedLoading(false);
    }
  }

  const replicaLooksStale =
    unmitigatedResult !== null &&
    unmitigatedResult.readValue !==
      unmitigatedResult.writtenValue;

  return (
    <main className="read-your-own-write-page">
      <header className="lag-page-heading">
        <p className="lag-page-eyebrow">
          Mitigating Replication Lag
        </p>

        <h1>1: Reading Your Own Write</h1>

        <p>
          Compare a direct read from a lagging replica with a
          read-after-write-consistent read from the leader.
        </p>
      </header>

      <section className="operation-panel demo-controls">
        <div className="demo-control-row">
          <label htmlFor="read-your-own-write-value">
            Value to write
          </label>

          <input
            id="read-your-own-write-value"
            value={value}
            onChange={(event) =>
              setValue(event.target.value)
            }
          />
        </div>

        <div className="demo-control-row">
          <label htmlFor="lagging-follower">
            Lagging follower
          </label>

          <select
            id="lagging-follower"
            value={selectedFollowerId}
            onChange={(event) =>
              setSelectedFollowerId(event.target.value)
            }
            disabled={followers.length === 0}
          >
            {followers.length === 0 && (
              <option value="">
                No active followers available
              </option>
            )}

            {followers.map((node) => (
              <option
                key={node.node_id}
                value={node.node_id}
              >
                {node.node_id}
              </option>
            ))}
          </select>
        </div>

        <div className="demo-control-row">
          <label htmlFor="replication-lag-seconds">
            Replica lag: {lagSeconds.toFixed(1)} seconds
          </label>

          <input
            id="replication-lag-seconds"
            type="range"
            min="0.1"
            max="10"
            step="0.1"
            value={lagSeconds}
            onChange={(event) =>
              setLagSeconds(Number(event.target.value))
            }
          />
        </div>
      </section>

      {message && (
        <p className="operation-message">
          {message}
        </p>
      )}

        <section className="read-your-writes-comparison">
        <article className="read-your-writes-card no-mitigation-card">
            <h2>No mitigation: read from lagging replica</h2>

            <p>
            The client writes to the leader, then immediately reads
            directly from a replica that has not caught up yet.
            </p>

            <button
            onClick={runUnmitigatedScenario}
            disabled={
                unmitigatedLoading ||
                !selectedFollowerId
            }
            >
            {unmitigatedLoading
                ? "Running..."
                : "Write, then read lagging replica"}
            </button>

            {unmitigatedResult && (
              <div className="read-result">
                <p>
                  <strong>Written value:</strong>{" "}
                  {unmitigatedResult.writtenValue}
                </p>

                <p>
                  <strong>Value read from </strong>
                  <strong>{unmitigatedResult.nodeId}</strong>
                  <strong>:</strong>{" "}
                  <span
                    className={
                      isMissing(unmitigatedResult.readValue)
                        ? "missing-value"
                        : undefined
                    }
                  >
                    {displayValue(unmitigatedResult.readValue)}
                  </span>
                </p>

                <NodeReadStatusPanel
                  snapshots={unmitigatedResult.nodeSnapshots}
                  keyName={unmitigatedResult.key}
                  selectedNodeIds={[unmitigatedResult.nodeId]}
                  readLabels={{ [unmitigatedResult.nodeId]: "Read selected here" }}
                />

                {replicaLooksStale ? (
                  <p
                    role="alert"
                    className="replica-caution"
                  >
                    The replica has not caught up. The client’s write
                    appears to have disappeared.
                  </p>
                ) : (
                  <p>
                    The replica has already caught up.
                  </p>
                )}

                {unmitigatedResult.delayedReadValue !== undefined && (
                  <p>
                    <strong>Value read from </strong>
                    <em className="replica-detail">
                      {unmitigatedResult.nodeId}
                    </em>
                    <strong> after </strong>
                    <em className="replica-detail">
                      {unmitigatedResult.lagSeconds?.toFixed(1)} seconds
                    </em>
                    <strong>:</strong>{" "}
                    <span
                      className={
                        isMissing(unmitigatedResult.delayedReadValue)
                          ? "missing-value"
                          : "replica-caught-up-value"
                      }
                    >
                      {displayValue(unmitigatedResult.delayedReadValue)}
                    </span>
                  </p>
                )}

                <button onClick={readReplicaAgain}>
                  Read replica again
                </button>
              </div>
            )}
        </article>

        <article className="read-your-writes-card mitigation-card">
            <h2>Mitigation: read from leader after writing</h2>

            <p>
            After writing, the client reads from the leader, which
            guarantees it sees its own acknowledged write.
            </p>

            <button
            onClick={runMitigatedScenario}
            disabled={mitigatedLoading || !leaderId}
            >
            {mitigatedLoading
                ? "Running..."
                : "Write, then read leader"}
            </button>

            {mitigatedResult && (
            <div className="read-result">
                <p>
                <strong>Written value:</strong>{" "}
                {mitigatedResult.writtenValue}
                </p>

                <p>
                  <strong>Value read from </strong>
                  <em className="replica-detail">
                    {mitigatedResult.nodeId}
                  </em>
                  {" "}(leader)
                  <strong>:</strong>{" "}
                  <span className="replica-caught-up-value">
                    {displayValue(mitigatedResult.readValue)}
                  </span>
                </p>

                <NodeReadStatusPanel
                  snapshots={mitigatedResult.nodeSnapshots}
                  keyName={mitigatedResult.key}
                  selectedNodeIds={[mitigatedResult.nodeId]}
                  readLabels={{ [mitigatedResult.nodeId]: "Read selected here" }}
                />

                <p className="read-your-write-success">
                  The leader applied the write before acknowledging it,
                  so this client can read its own write.
                </p>
            </div>
            )}
        </article>
        </section>
    </main>
  );
}

export default ReadYourOwnWritePage;
