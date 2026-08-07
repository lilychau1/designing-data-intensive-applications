import "./NodeCard.css";
import type { NodeInfo } from "../types/cluster";

interface NodeCardProps {
  node: NodeInfo;
  leaderId: string | null;
  onRemove: (nodeId: string) => void;
  onRestart: (nodeId: string) => void;
}

export default function NodeCard({
  node,
  leaderId,
  onRemove,
  onRestart,
}: NodeCardProps) {
  const isLeader = node.node_id === leaderId;
  const isRemoved = node.status === "removed";

  return (
    <div
      className={[
        "node-card",
        isLeader ? "leader" : "",
        isRemoved ? "removed" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="node-card-header">
        <h3 className="node-card-title">{node.node_id}</h3>

        {isLeader && (
          <span className="node-card-leader-badge">
            LEADER
          </span>
        )}
      </div>

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

      <div className="node-card-actions">
        <button
          type="button"
          disabled={isRemoved}
          onClick={() => onRemove(node.node_id)}
        >
          Remove node
        </button>

        <button
          type="button"
          disabled={!isRemoved}
          onClick={() => onRestart(node.node_id)}
        >
          Restart node
        </button>
      </div>
    </div>
  );
}