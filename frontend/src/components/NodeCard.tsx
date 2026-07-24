import type { NodeInfo } from "../types/cluster";

interface NodeCardProps {
  node: NodeInfo;
  isLeader: boolean;
  onRemove: (nodeId: string) => void;
  onRestart: (nodeId: string) => void;
}

export default function NodeCard({
  node,
  isLeader,
  onRemove,
  onRestart,
}: NodeCardProps) {
  const isRemoved = node.status === "removed";
  const isRunning = node.status === "running";

  return (
    <div className="node-card">
      <h3>{node.node_id}</h3>

      <p>
        <strong>Role:</strong> {node.role}
      </p>

      <p>
        <strong>Status:</strong> {node.status}
      </p>

      <p>
        <strong>Last applied index:</strong>{" "}
        {node.last_applied_index}
      </p>

      {isLeader && (
        <strong>LEADER</strong>
      )}

      <div className="node-actions">
        <button
          onClick={() => onRemove(node.node_id)}
          disabled={isRemoved}
        >
          Remove node
        </button>

        <button
          onClick={() => onRestart(node.node_id)}
          disabled={isRunning}
        >
          Restart node
        </button>
      </div>
    </div>
  );
}