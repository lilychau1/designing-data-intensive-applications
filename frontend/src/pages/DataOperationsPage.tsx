import { useState } from "react";

import WritePanel from "../components/WritePanel";
import ReadPanel from "../components/ReadPanel";
import OperationActivity from "../components/OperationActivity";

import {
  writeData,
  readFromLeader,
  toClusterEvent,
} from "../api/DataApi";

import type { NodeInfo } from "../types/cluster";
import type { ClusterEvent } from "../types/events";

interface DataOperationsPageProps {
  nodes: NodeInfo[];
  leaderId: string | null;
  events: ClusterEvent[];
  onClusterUpdated: () => Promise<void>;

  onEvent: (event: ClusterEvent) => void;

  onDataOperation: (
    operation: "write" | "read",
    key: string,
    value: unknown
  ) => void;
}

function DataOperationsPage({
  nodes,
  leaderId,
  events,
  onClusterUpdated,
  onEvent,
  onDataOperation,
}: DataOperationsPageProps) {
  const [writeLoading, setWriteLoading] =
    useState(false);

  const [readLoading, setReadLoading] =
    useState(false);

  const [message, setMessage] =
    useState<string | null>(null);

  const [lastOperation, setLastOperation] =
    useState<"write" | "read" | null>(null);

  const [lastOperationKey, setLastOperationKey] =
    useState("");

  const [lastOperationValue, setLastOperationValue] =
    useState<unknown>(null);

  async function handleWrite(
    key: string,
    value: string
  ) {
    setWriteLoading(true);
    setMessage(null);

    try {
      if (!leaderId) {
        throw new Error(
          "Cannot write because there is no current leader."
        );
      }

      const response = await writeData(
        key,
        value
      );

      console.log("WRITE RESPONSE:", response);

      response.events.forEach((event) => {
        onEvent(toClusterEvent(event));
      });

      setLastOperation("write");
      setLastOperationKey(key);
      setLastOperationValue(value);

      await onClusterUpdated();

      setMessage(
        `Successfully wrote "${key} = ${value}" through ${leaderId}.`
      );

    } catch (error) {
      console.error("Failed to write data:", error);

      setMessage(
        error instanceof Error
          ? error.message
          : "Failed to write data."
      );
    } finally {
      setWriteLoading(false);
    }
  }

  async function handleRead(
    key: string
  ) {
    setReadLoading(true);
    setMessage(null);

    try {
      const response =
        await readFromLeader(key);

      setLastOperation("read");
      setLastOperationKey(key);
      setLastOperationValue(
        response.value
      );

      onDataOperation(
        "read",
        key,
        response.value
      );

      setMessage(
        `Read "${key}" from ${
          leaderId ?? "the leader"
        }.`
      );

      return response;
    } catch (error) {
      console.error(
        "Failed to read from leader:",
        error
      );

      setMessage(
        error instanceof Error
          ? error.message
          : "Failed to read from leader."
      );

      return null;
    } finally {
      setReadLoading(false);
    }
  }

  return (
    <main className="data-operations-page">

      {/* =========================================
          PAGE HEADER
      ========================================= */}

      <div className="data-operations-heading">
        <h1>Data Operations</h1>
      </div>


      {/* =========================================
          CURRENT LEADER STATUS
      ========================================= */}

      <div className="cluster-status-bar">
        <span className="status-label">
          Current leader:
        </span>

        <strong className="status-value">
          {leaderId ?? "No leader"}
        </strong>
      </div>


      {/* =========================================
          SUCCESS / ERROR MESSAGE
      ========================================= */}

      {message && (
        <div className="operation-message">
          {message}
        </div>
      )}


      {/* =========================================
          WRITE + READ PANELS
      ========================================= */}

      <section className="operations-section">

        <div className="operation-cards">

          {/* WRITE */}
          <div className="operation-card">
            <WritePanel
              onWrite={handleWrite}
              loading={writeLoading}
            />
          </div>


          {/* READ */}
          <div className="operation-card">
            <ReadPanel
              onRead={handleRead}
              loading={readLoading}
            />
          </div>

        </div>

      </section>


      {/* =========================================
          REPLICATION ACTIVITY
      ========================================= */}

      <section className="replication-activity-section">

        <h2>
          Replication Activity
        </h2>


        {/* Node cards / operation timelines */}

        <OperationActivity
          nodes={nodes}
          leaderId={leaderId}
          operation={lastOperation}
          operationKey={lastOperationKey}
          value={lastOperationValue}
          events={events}
        />

      </section>

    </main>
  );
}

export default DataOperationsPage;
