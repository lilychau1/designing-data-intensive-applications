import { useState } from "react";

import type { NodeInfo } from "../types/cluster";
import type { ClusterEvent } from "../types/events";

interface OperationActivityProps {
  nodes: NodeInfo[];
  leaderId: string | null;
  operation: "write" | "read" | null;
  operationKey: string;
  value: unknown;
  events: ClusterEvent[];
  onReplicationDelayChange: (
    nodeId: string, 
    delay: number
  ) => Promise<void>;
}

function OperationActivity({
  nodes,
  leaderId,
  operation,
  operationKey,
  value,
  events,
  onReplicationDelayChange,
}: OperationActivityProps) {

  const [draftDelays, setDraftDelays] = useState<
    Record<string, number>
  >({});

  return (
    <section className="replication-activity-card">
      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "20px",
        }}
      >
        {nodes.map((node) => {
          const isLeader =
            node.node_id === leaderId;

          const nodeEventsForThisNode =
            events.filter(
              (event) =>
                event.nodeId === node.node_id
            );
          const delay =
            draftDelays[node.node_id] ?? 
            node.replication_delay ?? 
            0;

          return (
            <article
              key={node.node_id}
              className={[
                "node-card",
                isLeader
                  ? "leader"
                  : "",
                node.status === "removed"
                  ? "removed"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {/* Node header */}
              <div className="node-card-header">
                <h3 className="node-card-title">
                  {node.node_id}
                </h3>

                {isLeader && (
                  <span className="node-card-leader-badge">
                    LEADER
                  </span>
                )}
              </div>

              {/* Node information */}
              <div className="node-card-info">
                <div className="node-card-info-row">
                  <span className="node-card-label">
                    Role
                  </span>

                  <span>
                    {node.role}
                  </span>
                </div>

                <div className="node-card-info-row">
                  <span className="node-card-label">
                    Status
                  </span>

                  <span>
                    {node.status}
                  </span>
                </div>

                <div className="node-card-info-row">
                  <span className="node-card-label">
                    Last applied index
                  </span>

                  <span>
                    {node.last_applied_index}
                  </span>
                </div>
                
                <div className="node-card-info-row">
                  <span className="node-card-label">
                    Replication delay
                  </span>

                  <span>
                    {node.replication_delay.toFixed(1)} seconds
                  </span>
                </div>
              </div>

              <div className="node-replication-delay-control">
                <label htmlFor={`replication-delay-${node.node_id}`}>
                  Replication delay: {(node.replication_delay ?? 0).toFixed(1)} seconds
                </label>

                <input
                  id={`replication-delay-${node.node_id}`}
                  type="range"
                  min="0"
                  max="5"
                  step="0.1"
                  value={delay}
                  disabled={node.node_id === leaderId}
                  onChange={(event) => {
                    const nextDelay = Number(event.target.value);

                    setDraftDelays((current) => ({
                      ...current,
                      [node.node_id]: nextDelay,
                    }));
                  }}
                  onPointerUp={(event) => {
                    void onReplicationDelayChange(
                      node.node_id,
                      Number(event.currentTarget.value)
                    );
                  }}
                />
              </div>
              
              {/* Current operation */}
              <div className="node-operation">
                {operation === "write" ? (
                  <>
                    <strong>
                      {isLeader
                        ? "Directly written"
                        : "Replicated"}
                    </strong>

                    <span>
                      {operationKey} ={" "}
                      {String(value)}
                    </span>
                  </>
                ) : operation === "read" ? (
                  <>
                    <strong>
                      Read operation
                    </strong>

                    <span>
                      Key: {operationKey}
                    </span>
                  </>
                ) : (
                  <>
                    <strong>
                      Waiting for operation
                    </strong>

                    <span>
                      No read or write operation yet.
                    </span>
                  </>
                )}
              </div>

              {/* Node event timeline */}
              <div className="node-event-timeline">
                <h4>
                  Event Timeline
                </h4>

                {nodeEventsForThisNode.length ===
                0 ? (
                  <p>
                    No events yet.
                  </p>
                ) : (
                  <div>
                    {nodeEventsForThisNode
                      .slice()
                      .reverse()
                      .map((event) => (
                        <div
                          key={event.id}
                          className="node-event"
                        >
                          <div className="node-event-header">
                            <strong>
                              {event.type ===
                              "write_direct"
                                ? "Directly written"
                                : event.type ===
                                  "write_replicated"
                                ? "Replicated"
                                : event.type ===
                                  "read_operation"
                                ? "Read"
                                : event.type}
                            </strong>

                            <span>
                              {new Date(
                                event.timestamp
                              ).toLocaleTimeString()}
                            </span>
                          </div>

                          <p>
                            {event.message}
                          </p>

                          {event.key !==
                            undefined && (
                            <div>
                              <strong>
                                Key:
                              </strong>{" "}
                              {event.key}
                            </div>
                          )}

                          {event.value !==
                            undefined && (
                            <div>
                              <strong>
                                Value:
                              </strong>{" "}
                              {String(
                                event.value
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default OperationActivity;
