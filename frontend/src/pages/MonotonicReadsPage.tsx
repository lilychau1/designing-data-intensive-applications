import { useMemo, useState } from "react";

import {
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

interface MonotonicReadsPageProps {
    nodes: NodeInfo[];
    leaderId: string | null;
    onClusterUpdated: () => Promise<void>;
}

function wait(milliseconds: number): Promise<void> {
    return new Promise((resolve) => {
        setTimeout(resolve, milliseconds);
    });
}

async function waitUntilReplicaHasValue(
    nodeId: string, 
    key: string, 
    expectedValue: string, 
): Promise<void> {
    const deadline = Date.now() + 2_000; 

    while (Date.now() < deadline) {
        const response = await readFromNode(nodeId, key);

        if (response.value === expectedValue) {
            return;
        }

        await wait(50); 
    }

    throw new Error(
        `Timeout waiting for replica ${nodeId} to have value "${expectedValue}" for key "${key}".`
    );
}

interface MonotonicReadResult {
    key: string;
    firstNodeId: string;
    firstValue: unknown;
    secondNodeId: string;
    secondValue: unknown;
    nodeSnapshots: NodeReadSnapshot[];
}

function MonotonicReadsPage({
    nodes,
    leaderId,
    onClusterUpdated,
}: MonotonicReadsPageProps) {

    const [firstReplicaId, setFirstReplicaId] = useState("");
    const [laggingReplicaId, setLaggingReplicaId] = useState("");
    const [lagSeconds, setLagSeconds] = useState(2);

    const followers = useMemo(
    () =>
        nodes.filter(
        (node) =>
            node.node_id !== leaderId &&
            node.status === "running"
        ),
    [nodes, leaderId]
    );

    const [unmitigatedResult, setUnmitigatedResult] = useState<MonotonicReadResult | null>(null);
    const [mitigatedResult, setMitigatedResult] = useState<MonotonicReadResult | null>(null);

    const [unmitigatedLoading, setUnmitigatedLoading] = useState(false);
    const [mitigatedLoading, setMitigatedLoading] = useState(false);

    const [message, setMessage] = useState<string | null>(null);

    async function prepareScenario(
        key: string,
    ): Promise<void> {
        await setNodeReplicationDelay(firstReplicaId, 0);
        await setNodeReplicationDelay(laggingReplicaId, 0);

        await writeData(key, "version 1");
        await waitUntilReplicaHasValue(firstReplicaId, key, "version 1");
        await waitUntilReplicaHasValue(laggingReplicaId, key, "version 1");

        await setNodeReplicationDelay(laggingReplicaId, lagSeconds);
        await onClusterUpdated();
    }

    async function runUnmitigatedScenario() {
        if (
            !firstReplicaId ||
            !laggingReplicaId ||
            firstReplicaId === laggingReplicaId
        ) {
            setMessage(
                "Please select two different replicas before running the scenario."
            );
            return;
        }
        
        setUnmitigatedLoading(true);
        setUnmitigatedResult(null);
        setMessage(null);

        const key = `monotonic-unmitigated-${crypto.randomUUID()}`;

        try {
            await prepareScenario(key);
            await writeData(key, "version 2");
            await waitUntilReplicaHasValue(firstReplicaId, key, "version 2");

            const firstRead = await readFromNode(firstReplicaId, key);
            const secondRead = await readFromNode(laggingReplicaId, key);
            const nodeSnapshots = await getNodeReadSnapshots(nodes, key);

            setUnmitigatedResult({
                key,
                firstNodeId: firstReplicaId,
                firstValue: firstRead.value,
                secondNodeId: laggingReplicaId,
                secondValue: secondRead.value,
                nodeSnapshots,
            });
        } catch (error) {
            setMessage(
                error instanceof Error
                ? error.message
                : "Failed to run the monotonic reads demostration."
            );
        } finally {
            setUnmitigatedLoading(false);
        }
    }

    async function runMitigatedScenario() {
        if (!firstReplicaId || !laggingReplicaId) {
            setMessage("Please select two active replicas before running the scenario.");
            return;
        }

        setMitigatedLoading(true);
        setMitigatedResult(null);
        setMessage(null);

        const key = `monotonic-mitigated-${crypto.randomUUID()}`;

        try {
            await prepareScenario(key);
            await writeData(key, "version 2");
            await waitUntilReplicaHasValue(firstReplicaId, key, "version 2");

            const firstRead = await readFromNode(firstReplicaId, key);
            const secondRead = await readFromNode(firstReplicaId, key);
            const nodeSnapshots = await getNodeReadSnapshots(nodes, key);

            setMitigatedResult({
                key,
                firstNodeId: firstReplicaId,
                firstValue: firstRead.value,
                secondNodeId: firstReplicaId,
                secondValue: secondRead.value,
                nodeSnapshots,
            });
        } catch (error) {
            setMessage(
                error instanceof Error
                    ? error.message
                    : "Failed to run the monotonic-read mitigation."
            );
        } finally {
            setMitigatedLoading(false);
        }
    }

    return (
    <main className="monotonic-reads-page">
      <header className="lag-page-heading">
        <p className="lag-page-eyebrow">
          Mitigating Replication Lag
        </p>

        <h1>2: Monotonic Reads</h1>

        <p>
          Once a client has observed newer data, it should not
          later observe an older version.
        </p>
      </header>

        <section className="operation-panel demo-controls">
        <div className="demo-control-row">
            <label htmlFor="first-read-replica">
            First read replica
            </label>

            <select
            id="first-read-replica"
            value={firstReplicaId}
            onChange={(event) =>
                setFirstReplicaId(event.target.value)
            }
            disabled={followers.length < 2}
            >
            <option value="">
                Select a replica
            </option>

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
            <label htmlFor="lagging-replica">
            Second, lagging replica
            </label>

            <select
            id="lagging-replica"
            value={laggingReplicaId}
            onChange={(event) =>
                setLaggingReplicaId(event.target.value)
            }
            disabled={followers.length < 2}
            >
            <option value="">
                Select a different replica
            </option>

            {followers
                .filter(
                (node) =>
                    node.node_id !== firstReplicaId
                )
                .map((node) => (
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
            <label htmlFor="monotonic-lag-seconds">
            Replica lag: {lagSeconds.toFixed(1)} seconds
            </label>

            <input
            id="monotonic-lag-seconds"
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
            <p className="operation-message">{message}</p>
        )}

        <section className="monotonic-reads-comparison">
        <article className="monotonic-read-card no-mitigation-card">
            <h2>No mitigation: switch replicas</h2>

            <p>
            The client first reads a newer value from one replica,
            then reads an older value from a lagging replica.
            </p>

            <button
            onClick={runUnmitigatedScenario}
            disabled={
                !firstReplicaId ||
                !laggingReplicaId ||
                firstReplicaId === laggingReplicaId ||
                unmitigatedLoading
            }
            >
            {unmitigatedLoading
                ? "Running..."
                : "Demonstrate monotonic-read violation"}
            </button>

            {unmitigatedResult && (
                <div className="read-result">
                    <p>
                        <strong>First read from </strong>
                        <em className="replica-detail">
                            {unmitigatedResult.firstNodeId}
                        </em>
                        <strong>:</strong>{" "}
                        <span className="replica-caught-up-value">
                            {String(unmitigatedResult.firstValue)}
                        </span>
                    </p>

                    <p>
                        <strong>Second read from </strong>
                        <em className="replica-detail">
                            {unmitigatedResult.secondNodeId}
                        </em>
                        <strong>:</strong>{" "}
                        <span className="missing-value">
                            {String(unmitigatedResult.secondValue)}
                        </span>
                    </p>

                    <NodeReadStatusPanel
                        snapshots={unmitigatedResult.nodeSnapshots}
                        keyName={unmitigatedResult.key}
                        selectedNodeIds={[
                            unmitigatedResult.firstNodeId,
                            unmitigatedResult.secondNodeId,
                        ]}
                        readLabels={{
                            [unmitigatedResult.firstNodeId]: "First read",
                            [unmitigatedResult.secondNodeId]: "Second read",
                        }}
                    />

                    <p role="alert" className="replica-caution">
                        The client switched replicas and observed an older value.
                        This violates monotonic reads.
                    </p>
                </div>
            )}
        </article>

        <article className="monotonic-read-card mitigation-card">
            <h2>Mitigation: keep the client on one replica</h2>

            <p>
            The client stays on the same replica after its first
            read, so it does not observe an older value.
            </p>

            <button
            onClick={runMitigatedScenario}
            disabled={!firstReplicaId || !laggingReplicaId || mitigatedLoading}
            >
            {mitigatedLoading
                ? "Running..."
                : "Demonstrate session stickiness"}
            </button>

            {mitigatedResult && (
                <div className="read-result">
                    <p>
                        <strong>First read from </strong>
                        <em className="replica-detail">
                            {mitigatedResult.firstNodeId}
                        </em>
                        <strong>:</strong>{" "}
                        <span className="replica-caught-up-value">
                            {String(mitigatedResult.firstValue)}
                        </span>
                    </p>

                    <p>
                        <strong>Second read from the same replica </strong>
                        <em className="replica-detail">
                            {mitigatedResult.secondNodeId}
                        </em>
                        <strong>:</strong>{" "}
                        <span className="replica-caught-up-value">
                            {String(mitigatedResult.secondValue)}
                        </span>
                    </p>

                    <NodeReadStatusPanel
                        snapshots={mitigatedResult.nodeSnapshots}
                        keyName={mitigatedResult.key}
                        selectedNodeIds={[mitigatedResult.firstNodeId]}
                        readLabels={{
                            [mitigatedResult.firstNodeId]: "First and second read",
                        }}
                    />

                    <p className="read-your-write-success">
                        The client stayed on the same replica and did not observe
                        an older value.
                    </p>
                </div>
            )}
        </article>
        </section>
        
    </main>

    
  );
}

export default MonotonicReadsPage;
