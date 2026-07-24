import { useCallback, useEffect, useState } from "react";

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

  const handleRemoveNode = async (nodeId: string) => {
    setError(null);

    try {
      const clusterStatus = await removeNode(nodeId);

      setLeaderId(clusterStatus.leader_id);
      setNodes(clusterStatus.nodes);
    } catch (error) {
      console.error(`Failed to remove node ${nodeId}:`, error);

      setError(
        error instanceof Error
          ? error.message
          : `Failed to remove node ${nodeId}`
      );
    }
  };

  const handleRestartNode = async (nodeId: string) => {
    setError(null);

    try {
      const clusterStatus = await restartNode(nodeId);

      setLeaderId(clusterStatus.leader_id);
      setNodes(clusterStatus.nodes);
    } catch (error) {
      console.error(`Failed to restart node ${nodeId}:`, error);

      setError(
        error instanceof Error
          ? error.message
          : `Failed to restart node ${nodeId}`
      );
    }
  };

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

      <EventTimeline />
    </main>
  );
}

export default App;