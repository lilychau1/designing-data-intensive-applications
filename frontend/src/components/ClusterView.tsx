import type { NodeInfo } from "../types/cluster";
import NodeCard from "./NodeCard";

interface ClusterViewProps {
  leaderId: string | null;
  nodes: NodeInfo[];
  onRemoveNode: (nodeId: string) => void;
  onRestartNode: (nodeId: string) => void;
}

export default function ClusterView({
  leaderId,
  nodes,
  onRemoveNode,
  onRestartNode,
}: ClusterViewProps) {
  return (
    <section>
      <h2>Cluster</h2>

      <p>
        Leader: {leaderId ?? "No leader"}
      </p>

      <div className="node-list">
        {nodes.map((node) => (
          <NodeCard
            key={node.node_id}
            node={node}
            isLeader={node.node_id === leaderId}
            onRemove={onRemoveNode}
            onRestart={onRestartNode}
          />
        ))}
      </div>
    </section>
  );
}