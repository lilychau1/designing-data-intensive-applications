import { useCallback, useEffect, useState } from "react";

import type { ClusterEvent } from "./types/events";
import ClusterView from "./components/ClusterView";
import EventTimeline from "./components/EventTimeline";

import {
  getClusterStatus,
  removeNode,
  restartNode,
} from "./api/clusterApi";

import type { NodeInfo } from "./types/cluster";

function App() {
  const [leaderId, setLeaderId] = useState<string | null>(null);
  const [nodes, setNodes] = useState<NodeInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<ClusterEvent[]>([]);  
  
  const refreshCluster = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const clusterStatus = await getClusterStatus();

      setLeaderId(clusterStatus.leader_id);
      setNodes(clusterStatus.nodes);
    } catch (error) {
      console.error("Failed to refresh cluster:", error);

      setError(
        error instanceof Error
          ? error.message
          : "Failed to refresh cluster"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRemoveNode = async function handleRemoveNode(nodeId: string) {
    try {
      await removeNode(nodeId);

      const event: ClusterEvent = {
        id: crypto.randomUUID(),
        type: "node_removed",
        nodeId,
        message: `Node ${nodeId} was removed from the cluster.`,
        timestamp: new Date().toISOString(),
      };

      setEvents((previousEvents) => [
        ...previousEvents,
        event,
      ]);

      await refreshCluster();
    } catch (error) {
      console.error(
        `Failed to remove node ${nodeId}:`,
        error
      );
    }
  }

  const handleRestartNode = async function handleRestartNode(nodeId: string) {
    try {
      await restartNode(nodeId);

      const event: ClusterEvent = {
        id: crypto.randomUUID(),
        type: "node_restarted",
        nodeId,
        message: `Node ${nodeId} was restarted and added back to the cluster.`,
        timestamp: new Date().toISOString(),
      };

      setEvents((previousEvents) => [
        ...previousEvents,
        event,
      ]);

      await refreshCluster();
    } catch (error) {
      console.error(
        `Failed to restart node ${nodeId}:`,
        error
      );
    }
  }

  useEffect(() => {
    refreshCluster();
  }, [refreshCluster]);

  return (
    <main>
      <h1>Single-Leader Replication Cluster</h1>

      <button
        onClick={refreshCluster}
        disabled={loading}
      >
        {loading ? "Refreshing..." : "Refresh cluster"}
      </button>

      {error && (
        <p role="alert">
          Error: {error}
        </p>
      )}

      <ClusterView
        leaderId={leaderId}
        nodes={nodes}
        onRemoveNode={handleRemoveNode}
        onRestartNode={handleRestartNode}
      />

      <EventTimeline events={events} />
    </main>
  );
}

export default App;