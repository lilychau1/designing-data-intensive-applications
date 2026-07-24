import type { NodeInfo } from "../types/cluster";

interface NodeCardProps {
  node: NodeInfo;
  isLeader: boolean;
  onRemove: (nodeId: string) => void;
}

export function NodeCard({
  node,
  isLeader,
  onRemove,
}: NodeCardProps) {
  return (
    <div className="node-card">
      <h3>{node.node_id}</h3>

      <p>
        Role: {node.role}
      </p>

      <p>
        Status: {node.status}
      </p>

      <p>
        Last applied index: {node.last_applied_index}
      </p>

      {isLeader && (
        <strong>
          LEADER
        </strong>
      )}

      {node.status !== "removed" && (
        <button
          onClick={() => onRemove(node.node_id)}
        >
          Remove node
        </button>
      )}
    </div>
  );
}