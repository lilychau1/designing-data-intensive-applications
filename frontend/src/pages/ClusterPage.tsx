import { useCallback, useEffect, useState } from "react";

import type { ClusterEvent } from "../types/events";
import type { NodeInfo } from "../types/cluster";

import ClusterView from "../components/ClusterView";
import EventTimeline from "../components/EventTimeline";

import {
  getClusterStatus,
  removeNode,
  restartNode,
} from "../api/ClusterApi";

interface ClusterPageProps {
  onEvent: (event: ClusterEvent) => void;
}

function ClusterPage({ onEvent }: ClusterPageProps) {
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

  const handleEvent = useCallback(
    (event: ClusterEvent) => {
      setEvents((previousEvents) => [
        ...previousEvents,
        event,
      ]);

      onEvent(event);
    },
    [onEvent]
  );

  const handleRemoveNode = async (nodeId: string) => {
    try {
      const previousLeaderId = leaderId;

      await removeNode(nodeId);

      const status = await getClusterStatus();

      const newLeaderId = status.leader_id;

      setNodes(status.nodes);
      setLeaderId(newLeaderId);

      // Record node removal.
      handleEvent({
        id: crypto.randomUUID(),
        type: "node_removed",
        nodeId,
        message: `Node ${nodeId} was removed from the cluster.`,
        timestamp: new Date().toISOString(),
      });

      // Record leader election if the leader changed.
      if (
        previousLeaderId !== null &&
        previousLeaderId !== newLeaderId
      ) {
        handleEvent({
          id: crypto.randomUUID(),
          type: "leader_elected",
          nodeId: newLeaderId ?? "",
          message: newLeaderId
            ? `Leader changed from ${previousLeaderId} to ${newLeaderId}.`
            : `Leader ${previousLeaderId} was removed. No leader is currently available.`,
          timestamp: new Date().toISOString(),
        });
      }
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

  const handleRestartNode = async (nodeId: string) => {
    try {
      const previousLeaderId = leaderId;

      await restartNode(nodeId);

      // Fetch the cluster state after restart.
      const status = await getClusterStatus();

      const newLeaderId = status.leader_id;

      setNodes(status.nodes);
      setLeaderId(newLeaderId);

      // Record restart event.
      handleEvent({
        id: crypto.randomUUID(),
        type: "node_restarted",
        nodeId,
        message: `Node ${nodeId} was restarted and added back to the cluster.`,
        timestamp: new Date().toISOString(),
      });

      // If there was no leader before the restart and the restarted
      // node became leader, record the election.
      if (
        previousLeaderId !== newLeaderId &&
        newLeaderId !== null
      ) {
        handleEvent({
          id: crypto.randomUUID(),
          type: "leader_elected",
          nodeId: newLeaderId,
          message: previousLeaderId
            ? `Leader changed from ${previousLeaderId} to ${newLeaderId}.`
            : `Node ${newLeaderId} was elected as the new leader.`,
          timestamp: new Date().toISOString(),
        });
      }
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
        {loading
          ? "Refreshing..."
          : "Refresh cluster"}
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

export default ClusterPage;