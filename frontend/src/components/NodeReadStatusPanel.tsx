import type { NodeInfo } from "../types/cluster";

export interface NodeReadSnapshot {
  node: NodeInfo;
  value: unknown;
}

interface NodeReadStatusPanelProps {
  snapshots: NodeReadSnapshot[];
  keyName: string;
  selectedNodeIds: string[];
  readLabels: Record<string, string>;
}

function displayValue(value: unknown): string {
  return value === null || value === undefined ? "(missing)" : String(value);
}

function NodeReadStatusPanel({
  snapshots,
  keyName,
  selectedNodeIds,
  readLabels,
}: NodeReadStatusPanelProps) {
  return (
    <div className="node-read-statuses">
      <p className="node-read-statuses-heading">Live node status and value for key: {keyName}</p>
      <div className="node-read-status-grid">
        {snapshots.map(({ node, value }) => {
          const selected = selectedNodeIds.includes(node.node_id);
          const readLabel = readLabels[node.node_id];

          return (
            <article
              key={node.node_id}
              className={[
                "node-read-status",
                selected ? "is-read-target" : "",
                value === null || value === undefined ? "is-missing-value" : "is-present-value",
              ].filter(Boolean).join(" ")}
            >
              <div className="node-read-status-title">
                <strong>{node.node_id}</strong>
                <span>{node.role}</span>
              </div>
              <p>Log index <strong>{node.last_applied_index}</strong></p>
              <p>Value: <strong>{displayValue(value)}</strong></p>
              {readLabel && <p className="node-read-target-label">{readLabel}</p>}
            </article>
          );
        })}
      </div>
    </div>
  );
}

export default NodeReadStatusPanel;
