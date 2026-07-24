import { useCallback, useEffect, useState } from "react";

import type { ClusterEvent } from "./types/events";
import ClusterView from "./components/ClusterView";
import EventTimeline from "./components/EventTimeline";

import {
  getClusterStatus,
  removeNode,
  restartNode,
} from "./api/ClusterApi";

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

  // -------------------------------------------------------------------------
  // Remove node
  // -------------------------------------------------------------------------

  const handleRemoveNode = async (nodeId: string) => {
    try {
      // Remember the leader before removing the node.
      const previousLeaderId = leaderId;

      // Remove the node.
      await removeNode(nodeId);

      // Fetch the new cluster state.
      const status = await getClusterStatus();

      const newLeaderId = status.leader_id;

      // Update UI immediately.
      setNodes(status.nodes);
      setLeaderId(newLeaderId);

      // Add events.
      setEvents((previousEvents) => {
        const newEvents: ClusterEvent[] = [
          ...previousEvents,

          {
            id: crypto.randomUUID(),
            type: "node_removed",
            nodeId,
            message: `Node ${nodeId} was removed from the cluster.`,
            timestamp: new Date().toISOString(),
          },
        ];

        // Detect leader change.
        if (previousLeaderId !== newLeaderId) {
          if (newLeaderId) {
            newEvents.push({
              id: crypto.randomUUID(),
              type: "leader_elected",
              nodeId: newLeaderId,
              message: previousLeaderId
                ? `Leader changed from ${previousLeaderId} to ${newLeaderId}.`
                : `${newLeaderId} was elected as the new leader.`,
              timestamp: new Date().toISOString(),
            });
          } else if (previousLeaderId) {
            newEvents.push({
              id: crypto.randomUUID(),
              type: "leader_elected",
              nodeId: previousLeaderId,
              message: `Leader ${previousLeaderId} was removed. No leader is currently available.`,
              timestamp: new Date().toISOString(),
            });
          }
        }

        return newEvents;
      });
    } catch (error) {
      console.error(
        `Failed to remove node ${nodeId}:`,
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : `Failed to remove node ${nodeId}`
      );
    }
  };

  // -------------------------------------------------------------------------
  // Restart node
  // -------------------------------------------------------------------------

  const handleRestartNode = async (nodeId: string) => {
    try {
      // IMPORTANT:
      // Remember who the leader was BEFORE restarting the node.
      const previousLeaderId = leaderId;

      // Restart the node.
      await restartNode(nodeId);

      // IMPORTANT:
      // Get the cluster state AFTER restarting the node.
      const status = await getClusterStatus();

      const newLeaderId = status.leader_id;

      // Update the UI with the latest backend state.
      setNodes(status.nodes);
      setLeaderId(newLeaderId);

      // Build events.
      setEvents((previousEvents) => {
        const newEvents: ClusterEvent[] = [
          ...previousEvents,

          // Node restarted event.
          {
            id: crypto.randomUUID(),
            type: "node_restarted",
            nodeId,
            message: `Node ${nodeId} was restarted and added back to the cluster.`,
            timestamp: new Date().toISOString(),
          },
        ];

        // Detect whether restarting the node caused a leader election.
        if (previousLeaderId !== newLeaderId) {
          if (newLeaderId) {
            newEvents.push({
              id: crypto.randomUUID(),
              type: "leader_elected",
              nodeId: newLeaderId,
              message: previousLeaderId
                ? `Leader changed from ${previousLeaderId} to ${newLeaderId}.`
                : `${newLeaderId} was elected as the new leader.`,
              timestamp: new Date().toISOString(),
            });
          } else {
            newEvents.push({
              id: crypto.randomUUID(),
              type: "leader_elected",
              nodeId: nodeId,
              message: `Node ${nodeId} was restarted, but no leader is currently available.`,
              timestamp: new Date().toISOString(),
            });
          }
        }

        return newEvents;
      });
    } catch (error) {
      console.error(
        `Failed to restart node ${nodeId}:`,
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : `Failed to restart node ${nodeId}`
      );
    }
  };

  // -------------------------------------------------------------------------
  // Initial load
  // -------------------------------------------------------------------------

  useEffect(() => {
    refreshCluster();
  }, [refreshCluster]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

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