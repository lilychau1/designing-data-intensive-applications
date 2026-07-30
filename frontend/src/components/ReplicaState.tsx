import type { NodeInfo } from "../types/cluster";

interface ReplicaStateProps {
  nodes: NodeInfo[];
  leaderId: string | null;
  selectedKey: string;
  results: Record<
    string,
    {
      value: unknown;
      error?: string;
    }
  >;
  loadingNodeId: string | null;
  onReadNode: (
    nodeId: string
  ) => Promise<void>;
}

function ReplicaState({
  nodes,
  leaderId,
  selectedKey,
  results,
  loadingNodeId,
  onReadNode,
}: ReplicaStateProps) {
  return (
    <section>
      <h2>Replica State</h2>

      <p>
        Read the same key directly from each
        node to inspect replicated state.
      </p>

      {!selectedKey && (
        <p>
          Enter a key above and write or read it
          before inspecting replicas.
        </p>
      )}

      <div className="replica-grid">
        {nodes.map((node) => {
          const result =
            results[node.node_id];

          const isLeader =
            node.node_id === leaderId;

          const isLoading =
            loadingNodeId === node.node_id;

          return (
            <article
              key={node.node_id}
              className={
                isLeader
                  ? "replica-card leader"
                  : "replica-card"
              }
            >
              <h3>
                {node.node_id}
              </h3>

              {isLeader && (
                <strong>
                  LEADER
                </strong>
              )}

              <p>
                Role: {node.role}
              </p>

              <p>
                Status: {node.status}
              </p>

              <p>
                Last applied index:{" "}
                {node.last_applied_index}
              </p>

              {result && (
                <div>
                  {result.error ? (
                    <p>
                      Error:{" "}
                      {result.error}
                    </p>
                  ) : (
                    <>
                      <p>
                        Key:{" "}
                        {selectedKey}
                      </p>

                      <p>
                        Value:{" "}
                        {String(
                          result.value
                        )}
                      </p>
                    </>
                  )}
                </div>
              )}

              <button
                onClick={() =>
                  onReadNode(
                    node.node_id
                  )
                }
                disabled={
                  !selectedKey ||
                  isLoading ||
                  node.status !== "running"
                }
              >
                {isLoading
                  ? "Reading..."
                  : "Read Node"}
              </button>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default ReplicaState;