import {
  useCallback,
  useEffect,
  useState,
} from "react";

import type {
  ClusterEvent,
} from "./types/events";

import type {
  NodeInfo,
} from "./types/cluster";

import ClusterView from "./components/ClusterView";
import EventTimeline from "./components/EventTimeline";

import DataOperationsPage from "./pages/DataOperationsPage";

import {
  getClusterStatus,
  removeNode,
  restartNode,
} from "./api/ClusterApi";

function App() {
  const [page, setPage] = useState<
    "cluster" | "data"
  >("cluster");

  const [leaderId, setLeaderId] =
    useState<string | null>(null);

  const [nodes, setNodes] =
    useState<NodeInfo[]>([]);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [events, setEvents] =
    useState<ClusterEvent[]>([]);

  /*
   * Refresh cluster state from backend.
   */
  const refreshCluster =
    useCallback(async () => {
      setLoading(true);
      setError(null);

      try {
        const clusterStatus =
          await getClusterStatus();

        setLeaderId(
          clusterStatus.leader_id
        );

        setNodes(
          clusterStatus.nodes
        );
      } catch (error) {
        console.error(
          "Failed to refresh cluster:",
          error
        );

        setError(
          error instanceof Error
            ? error.message
            : "Failed to refresh cluster"
        );
      } finally {
        setLoading(false);
      }
    }, []);

  /*
   * Remove node.
   */
  async function handleRemoveNode(
    nodeId: string
  ) {
    try {
      const previousLeaderId =
        leaderId;

      await removeNode(nodeId);

      const status =
        await getClusterStatus();

      const newLeaderId =
        status.leader_id;

      setNodes(
        status.nodes
      );

      setLeaderId(
        newLeaderId
      );

      setEvents(
        (previousEvents) => {
          const newEvents: ClusterEvent[] = [
            ...previousEvents,

            {
              id: crypto.randomUUID(),
              type: "node_removed",
              nodeId,
              message:
                `Node ${nodeId} was removed from the cluster.`,
              timestamp:
                new Date().toISOString(),
            },
          ];

          if (
            previousLeaderId !== null &&
            previousLeaderId !==
              newLeaderId
          ) {
            newEvents.push({
              id: crypto.randomUUID(),
              type: "leader_elected",
              nodeId:
                newLeaderId ?? "",
              message:
                newLeaderId
                  ? `Leader changed from ${previousLeaderId} to ${newLeaderId}.`
                  : `Leader ${previousLeaderId} was removed. No leader is currently available.`,
              timestamp:
                new Date().toISOString(),
            });
          }

          return newEvents;
        }
      );
    } catch (error) {
      console.error(
        `Failed to remove node ${nodeId}:`,
        error
      );
    }
  }

  /*
   * Restart node.
   */
  async function handleRestartNode(
    nodeId: string
  ) {
    try {
      await restartNode(nodeId);

      setEvents(
        (previousEvents) => [
          ...previousEvents,

          {
            id: crypto.randomUUID(),
            type: "node_restarted",
            nodeId,
            message:
              `Node ${nodeId} was restarted and added back to the cluster.`,
            timestamp:
              new Date().toISOString(),
          },
        ]
      );

      await refreshCluster();
    } catch (error) {
      console.error(
        `Failed to restart node ${nodeId}:`,
        error
      );
    }
  }

  /*
   * Handle a successful data operation.
   *
   * WRITE:
   *   Leader -> write_direct
   *   Followers -> write_replicated
   *
   * READ:
   *   Leader -> read_operation
   */
  function handleDataOperation(
    operation: "write" | "read",
    key: string,
    value: unknown
  ) {
    const timestamp =
      new Date().toISOString();

    /*
     * READ
     */
    if (operation === "read") {
      if (!leaderId) {
        console.warn(
          "Cannot record read event because there is no leader."
        );

        return;
      }

      const readEvent: ClusterEvent = {
        id: crypto.randomUUID(),
        type: "read_operation",
        nodeId: leaderId,
        message:
          `Read "${key}".`,
        timestamp,
        key,
        value,
      };

      console.log(
        "[EVENT] Adding read event:",
        readEvent
      );

      setEvents(
        (previousEvents) => [
          ...previousEvents,
          readEvent,
        ]
      );

      return;
    }

    /*
     * WRITE
     */
    if (operation === "write") {
      const writeEvents: ClusterEvent[] =
        nodes.map((node) => {
          const isLeader =
            node.node_id === leaderId;

          const event: ClusterEvent = {
            id: crypto.randomUUID(),

            type:
              isLeader
                ? "write_direct"
                : "write_replicated",

            nodeId:
              node.node_id,

            message:
              isLeader
                ? `Directly wrote "${key}" = ${String(value)}.`
                : `Replicated "${key}" = ${String(value)}.`,

            timestamp,

            key,

            value,
          };

          return event;
        });

      console.log(
        "[EVENT] Adding write events:",
        writeEvents
      );

      setEvents(
        (previousEvents) => [
          ...previousEvents,
          ...writeEvents,
        ]
      );
    }
  }

  /*
   * Initial cluster load.
   */
  useEffect(() => {
    refreshCluster();
  }, [refreshCluster]);

  return (
    <main>
      <header>
        <h1>
          Single-Leader Replication Cluster
        </h1>

        <nav>
          <button
            onClick={() =>
              setPage("cluster")
            }
            disabled={
              page === "cluster"
            }
          >
            Cluster Overview
          </button>

          <button
            onClick={() =>
              setPage("data")
            }
            disabled={
              page === "data"
            }
          >
            Data Operations
          </button>
        </nav>
      </header>

      {error && (
        <p role="alert">
          Error: {error}
        </p>
      )}

      {page === "cluster" && (
        <>
          <button
            onClick={refreshCluster}
            disabled={loading}
          >
            {loading
              ? "Refreshing..."
              : "Refresh cluster"}
          </button>

          <ClusterView
            leaderId={leaderId}
            nodes={nodes}
            onRemoveNode={
              handleRemoveNode
            }
            onRestartNode={
              handleRestartNode
            }
          />

          <EventTimeline
            events={events}
          />
        </>
      )}

      {page === "data" && (
        <DataOperationsPage
          nodes={nodes}
          leaderId={leaderId}
          events={events}
          onClusterUpdated={
            refreshCluster
          }
          onDataOperation={
            handleDataOperation
          }
        />
      )}
    </main>
  );
}

export default App;