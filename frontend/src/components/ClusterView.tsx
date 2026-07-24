import type { NodeInfo } from "../types/cluster";
import { NodeCard } from "./NodeCard";

interface ClusterViewProps {
  leaderId: string | null;
  nodes: NodeInfo[];
  onRemoveNode: (nodeId: string) => void;
}

export function ClusterView({
  leaderId,
  nodes,
  onRemoveNode,
}: ClusterViewProps) {
  return (
    <section>
      <h2>Cluster</h2>

      <p>
        Leader: {leaderId ?? "No leader"}
      </p>

      <div className="node-grid">
        {nodes.map((node) => (
          <NodeCard
            key={node.node_id}
            node={node}
            isLeader={node.node_id === leaderId}
            onRemove={onRemoveNode}
          />
        ))}
      </div>
    </section>
  );
}