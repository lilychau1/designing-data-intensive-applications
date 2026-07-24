import { useEffect, useState } from "react";

import {
  getClusterStatus,
  removeNode,
} from "./api/clusterApi";

import type {
  NodeInfo,
} from "./types/cluster";

import type {
  ClusterEvent,
} from "./types/events";

import { ClusterView } from "./components/ClusterView";
import { ClusterControls } from "./components/ClusterControls";
import { EventTimeline } from "./components/EventTimeline";

export default function App() {
  const [leaderId, setLeaderId] = useState<string | null>(null);

  const [nodes, setNodes] = useState<NodeInfo[]>([]);

  const [events, setEvents] = useState<ClusterEvent[]>([]);

  async function refreshCluster() {
    const status = await getClusterStatus();

    setLeaderId(status.leader_id);
    setNodes(status.nodes);
  }

  async function handleRemoveNode(nodeId: string) {
    const previousLeader = leaderId;

    const status = await removeNode(nodeId);

    setLeaderId(status.leader_id);
    setNodes(status.nodes);

    const newEvent: ClusterEvent = {
      id: crypto.randomUUID(),
      type: "node_removed",
      message: `${nodeId} was removed from the cluster`,
      timestamp: new Date().toISOString(),
    };

    setEvents((currentEvents) => [
      newEvent,
      ...currentEvents,
    ]);

    if (
      previousLeader !== status.leader_id
    ) {
      const leaderEvent: ClusterEvent = {
        id: crypto.randomUUID(),
        type: "leader_changed",
        message: `Leader changed from ${
          previousLeader ?? "none"
        } to ${
          status.leader_id ?? "none"
        }`,
        timestamp: new Date().toISOString(),
      };

      setEvents((currentEvents) => [
        leaderEvent,
        ...currentEvents,
      ]);
    }
  }

  useEffect(() => {
    refreshCluster();
  }, []);

  return (
    <main>
      <h1>
        Single-Leader Replication Cluster
      </h1>

      <ClusterControls
        onRefresh={refreshCluster}
      />

      <ClusterView
        leaderId={leaderId}
        nodes={nodes}
        onRemoveNode={handleRemoveNode}
      />

      <EventTimeline
        events={events}
      />
    </main>
  );
}