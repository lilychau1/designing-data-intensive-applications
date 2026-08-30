import { useEffect, useMemo, useState } from "react";

import { readFromNode, writeData } from "../api/DataApi";
import {
  getNodeState,
  setNodeReplicationDelay,
} from "../api/ClusterApi";
import type { NodeInfo } from "../types/cluster";

interface ConsistentPrefixReadsPageProps {
  nodes: NodeInfo[];
  leaderId: string | null;
  onClusterUpdated: () => Promise<void>;
}

interface PrefixScenario {
  contextKey: string;
  dependentKey: string;
  requiredIndex: number;
  observedNodeId: string;
}

interface UnsafeResult extends PrefixScenario {
  laggingNodeId: string;
  laggingIndex: number;
  dependentValue: unknown;
  nodeStatuses: NodeInfo[];
}

interface MitigatedResult extends PrefixScenario {
  requestedNodeId: string;
  servedNodeId: string;
  servedIndex: number;
  contextValue: unknown;
  dependentValue: unknown;
  nodeStatuses: NodeInfo[];
}

interface NodeStatusComparisonProps {
  nodes: NodeInfo[];
  requiredIndex: number;
  selectedNodeId: string;
  observedNodeId: string;
  selectedLabel: string;
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
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

  throw new Error(`Timeout waiting for ${nodeId} to receive ${key}.`);
}

function displayValue(value: unknown): string {
  return value === null || value === undefined ? "(missing)" : String(value);
}

function NodeStatusComparison({
  nodes,
  requiredIndex,
  selectedNodeId,
  observedNodeId,
  selectedLabel,
}: NodeStatusComparisonProps) {
  return (
    <div className="prefix-node-statuses">
      <p className="prefix-node-statuses-heading">
        Live replica progress — minimum log position needed: {requiredIndex}
      </p>
      <div className="prefix-node-status-grid">
        {nodes.map((node) => {
          const isSelected = node.node_id === selectedNodeId;
          const isObserved = node.node_id === observedNodeId;
          const isCaughtUp = node.last_applied_index >= requiredIndex;

          return (
            <article
              key={node.node_id}
              className={[
                "prefix-node-status",
                isSelected ? "is-read-target" : "",
                isObserved ? "is-observed-node" : "",
                isCaughtUp ? "is-caught-up" : "is-behind",
              ].filter(Boolean).join(" ")}
            >
              <div className="prefix-node-status-title">
                <strong>{node.node_id}</strong>
                <span>{node.role}</span>
              </div>
              <p>
                Log index <strong>{node.last_applied_index}</strong>
              </p>
              <p className={isCaughtUp ? "prefix-node-ready" : "prefix-node-behind"}>
                {isCaughtUp ? "Caught up" : "Behind"}
              </p>
              {isSelected && (
                <p className="prefix-node-read-target">{selectedLabel}</p>
              )}
              {!isSelected && isObserved && (
                <p className="prefix-node-observed">First read here</p>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}

function ConsistentPrefixReadsPage({
  nodes,
  leaderId,
  onClusterUpdated,
}: ConsistentPrefixReadsPageProps) {
  const [laggingReplicaId, setLaggingReplicaId] = useState("");
  const [lagSeconds, setLagSeconds] = useState(2);
  const [firstKey, setFirstKey] = useState("first-write");
  const [firstValue, setFirstValue] = useState("First value");
  const [secondKey, setSecondKey] = useState("second-write");
  const [secondValue, setSecondValue] = useState("Second value");
  const [unsafeResult, setUnsafeResult] = useState<UnsafeResult | null>(null);
  const [mitigatedResult, setMitigatedResult] = useState<MitigatedResult | null>(null);
  const [unsafeLoading, setUnsafeLoading] = useState(false);
  const [mitigatedLoading, setMitigatedLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const followers = useMemo(
    () => nodes.filter((node) => node.node_id !== leaderId && node.status === "running"),
    [nodes, leaderId],
  );

  useEffect(() => {
    setLaggingReplicaId((currentId) =>
      followers.some((node) => node.node_id === currentId)
        ? currentId
        : followers[0]?.node_id ?? "",
    );
  }, [followers]);

  async function getLiveNodeStatuses(): Promise<NodeInfo[]> {
    const liveNodes: NodeInfo[] = [];

    // Query serially: the current backend exposes node-state replies through a
    // shared queue, so each API request must receive its own response first.
    for (const node of nodes) {
      if (node.status === "running") {
        liveNodes.push(await getNodeState(node.node_id));
      }
    }

    return liveNodes;
  }

  async function prepareScenario(): Promise<PrefixScenario> {
    if (!laggingReplicaId) {
      throw new Error("Select a lagging replica first.");
    }

    if (!firstKey.trim() || !secondKey.trim()) {
      throw new Error("Enter a key for both writes.");
    }

    if (firstKey === secondKey) {
      throw new Error("Use different keys so the two writes can be compared.");
    }

    const observedReplica = followers.find(
      (node) => node.node_id !== laggingReplicaId,
    );

    if (!observedReplica) {
      throw new Error("This demonstration needs two active follower replicas.");
    }

    await Promise.all(
      followers.map((node) => setNodeReplicationDelay(node.node_id, 0)),
    );

    const contextKey = firstKey.trim();
    const dependentKey = secondKey.trim();
    const contextValue = firstValue;
    const dependentValue = secondValue;

    // The context is causal predecessor of the dependent comment.
    await writeData(contextKey, contextValue);
    // The backend uses one shared response queue for direct reads. Keep these
    // requests serial so one request cannot consume another request's reply.
    await waitUntilReplicaHasValue(laggingReplicaId, contextKey, contextValue);
    await waitUntilReplicaHasValue(
      observedReplica.node_id,
      contextKey,
      contextValue,
    );

    await setNodeReplicationDelay(laggingReplicaId, lagSeconds);
    await onClusterUpdated();

    await writeData(dependentKey, dependentValue);
    await waitUntilReplicaHasValue(
      observedReplica.node_id,
      dependentKey,
      dependentValue,
    );

    const observedState = await getNodeState(observedReplica.node_id);
    return {
      contextKey,
      dependentKey,
      requiredIndex: observedState.last_applied_index,
      observedNodeId: observedReplica.node_id,
    };
  }

  async function runUnsafeScenario() {
    setUnsafeLoading(true);
    setUnsafeResult(null);
    setMessage(null);

    try {
      const scenario = await prepareScenario();
      // The client has observed the dependent entry, then a naive router ignores
      // that causal watermark and sends its next request to a stale replica.
      const laggingState = await getNodeState(laggingReplicaId);
      const dependentRead = await readFromNode(laggingReplicaId, scenario.dependentKey);
      const nodeStatuses = await getLiveNodeStatuses();

      setUnsafeResult({
        ...scenario,
        laggingNodeId: laggingReplicaId,
        laggingIndex: laggingState.last_applied_index,
        dependentValue: dependentRead.value,
        nodeStatuses,
      });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to run the unsafe scenario.");
    } finally {
      setUnsafeLoading(false);
    }
  }

  async function runMitigatedScenario() {
    setMitigatedLoading(true);
    setMitigatedResult(null);
    setMessage(null);

    try {
      const scenario = await prepareScenario();
      const requestedState = await getNodeState(laggingReplicaId);

      // A prefix-aware router only chooses a node that has applied the entire
      // causal prefix already observed by this client.
      const servedNodeId = requestedState.last_applied_index >= scenario.requiredIndex
        ? laggingReplicaId
        : scenario.observedNodeId;
      const servedState = await getNodeState(servedNodeId);
      const contextRead = await readFromNode(servedNodeId, scenario.contextKey);
      const dependentRead = await readFromNode(servedNodeId, scenario.dependentKey);
      const nodeStatuses = await getLiveNodeStatuses();

      setMitigatedResult({
        ...scenario,
        requestedNodeId: laggingReplicaId,
        servedNodeId,
        servedIndex: servedState.last_applied_index,
        contextValue: contextRead.value,
        dependentValue: dependentRead.value,
        nodeStatuses,
      });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to run the replica-selection scenario.");
    } finally {
      setMitigatedLoading(false);
    }
  }

  const ready = followers.length >= 2 && Boolean(laggingReplicaId);

  return (
    <main className="consistent-prefix-reads-page">
      <header className="lag-page-heading">
        <p className="lag-page-eyebrow">Mitigating Replication Lag</p>
        <h1>3: Consistent Prefix Reads</h1>
        <p>
          A client can get outdated data if it randomly chooses a replica to read
          from. The mitigation is to check each replica&apos;s log position and choose
          one that has caught up with everything the client has already seen.
        </p>
      </header>

      <section className="operation-panel demo-controls">
        <div className="demo-control-row">
          <label htmlFor="prefix-lagging-replica">Lagging replica</label>
          <select
            id="prefix-lagging-replica"
            value={laggingReplicaId}
            onChange={(event) => setLaggingReplicaId(event.target.value)}
            disabled={followers.length < 2}
          >
            {followers.map((node) => (
              <option key={node.node_id} value={node.node_id}>{node.node_id}</option>
            ))}
          </select>
        </div>

        <div className="demo-control-row">
          <label htmlFor="prefix-lag-seconds">Replica lag: {lagSeconds.toFixed(1)} seconds</label>
          <input
            id="prefix-lag-seconds"
            type="range"
            min="0.1"
            max="10"
            step="0.1"
            value={lagSeconds}
            onChange={(event) => setLagSeconds(Number(event.target.value))}
          />
        </div>

        <div className="demo-control-row">
          <label htmlFor="prefix-first-key">First write key</label>
          <input
            id="prefix-first-key"
            value={firstKey}
            onChange={(event) => setFirstKey(event.target.value)}
          />
        </div>

        <div className="demo-control-row">
          <label htmlFor="prefix-first-value">First write value</label>
          <input
            id="prefix-first-value"
            value={firstValue}
            onChange={(event) => setFirstValue(event.target.value)}
          />
        </div>

        <div className="demo-control-row">
          <label htmlFor="prefix-second-key">Second write key</label>
          <input
            id="prefix-second-key"
            value={secondKey}
            onChange={(event) => setSecondKey(event.target.value)}
          />
        </div>

        <div className="demo-control-row">
          <label htmlFor="prefix-second-value">Second write value</label>
          <input
            id="prefix-second-value"
            value={secondValue}
            onChange={(event) => setSecondValue(event.target.value)}
          />
        </div>
      </section>

      {message && <p className="operation-message">{message}</p>}

      <section className="read-your-writes-comparison">
        <article className="read-your-writes-card no-mitigation-card">
          <h2>No mitigation: ignore replica progress</h2>
          <p>
            The client reads from a caught-up replica, then a random choice sends
            its next read to a replica that is behind.
          </p>
          <button onClick={runUnsafeScenario} disabled={!ready || unsafeLoading}>
            {unsafeLoading ? "Running..." : "Read without a prefix check"}
          </button>

          {unsafeResult && (
            <div className="read-result">
              <p><strong>Observed through log index:</strong> {unsafeResult.requiredIndex} on {unsafeResult.observedNodeId}</p>
              <p><strong>{unsafeResult.laggingNodeId} is only at:</strong> {unsafeResult.laggingIndex}</p>
              <NodeStatusComparison
                nodes={unsafeResult.nodeStatuses}
                requiredIndex={unsafeResult.requiredIndex}
                selectedNodeId={unsafeResult.laggingNodeId}
                observedNodeId={unsafeResult.observedNodeId}
                selectedLabel="Read selected here"
              />
              <p><strong>Second write — key:</strong> {unsafeResult.dependentKey}</p>
              <p><strong>Value from lagging replica:</strong> <span className="missing-value">{displayValue(unsafeResult.dependentValue)}</span></p>
              <p role="alert" className="replica-caution">
                This replica has not caught up with what the client has already
                seen. Reading from it can return outdated data.
              </p>
            </div>
          )}
        </article>

        <article className="read-your-writes-card mitigation-card">
          <h2>Mitigation: route by required log index</h2>
          <p>
            The router checks how many log entries each replica has applied. If the
            requested replica is behind, it chooses one that has caught up instead.
          </p>
          <button onClick={runMitigatedScenario} disabled={!ready || mitigatedLoading}>
            {mitigatedLoading ? "Running..." : "Read with a prefix check"}
          </button>

          {mitigatedResult && (
            <div className="read-result">
              <p><strong>Minimum log position needed:</strong> {mitigatedResult.requiredIndex}</p>
              <p><strong>Requested:</strong> {mitigatedResult.requestedNodeId}; <strong>served by:</strong> {mitigatedResult.servedNodeId} (index {mitigatedResult.servedIndex})</p>
              <NodeStatusComparison
                nodes={mitigatedResult.nodeStatuses}
                requiredIndex={mitigatedResult.requiredIndex}
                selectedNodeId={mitigatedResult.servedNodeId}
                observedNodeId={mitigatedResult.observedNodeId}
                selectedLabel="Read selected here"
              />
              <p><strong>First write — key:</strong> {mitigatedResult.contextKey} <strong>value:</strong> <span className="replica-caught-up-value">{displayValue(mitigatedResult.contextValue)}</span></p>
              <p><strong>Second write — key:</strong> {mitigatedResult.dependentKey} <strong>value:</strong> <span className="replica-caught-up-value">{displayValue(mitigatedResult.dependentValue)}</span></p>
              <p className="read-your-write-success">
                This replica has caught up enough to return both writes together.
              </p>
            </div>
          )}
        </article>
      </section>
    </main>
  );
}

export default ConsistentPrefixReadsPage;
