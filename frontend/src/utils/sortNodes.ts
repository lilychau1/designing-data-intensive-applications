import type { NodeInfo } from "../types/cluster";

export function sortNodes(
  nodes: NodeInfo[]
): NodeInfo[] {
  return [...nodes].sort((left, right) =>
    left.node_id.localeCompare(
      right.node_id,
      undefined,
      { numeric: true }
    )
  );
}