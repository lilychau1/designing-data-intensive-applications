import NodeCard from "./NodeCard";
import type { NodeInfo } from "../types/cluster";

interface ClusterViewProps {
  nodes: NodeInfo[];
  leaderId: string | null;
  onRemoveNode: (nodeId: string) => void;
  onRestartNode: (nodeId: string) => void;
}

export default function ClusterView({
  nodes,
  leaderId,
  onRemoveNode,
  onRestartNode,
}: ClusterViewProps) {
  return (
    <section>
      <h2>Cluster</h2>

      <p>
        Leader: {leaderId ?? "No leader"}
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "20px",
        }}
      >
        {nodes.map((node) => (
          <NodeCard
            key={node.node_id}
            node={node}
            leaderId={leaderId}
            onRemove={onRemoveNode}
            onRestart={onRestartNode}
          />
        ))}
      </div>
    </section>
  );
}