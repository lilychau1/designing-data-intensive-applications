import { readFromNode } from "../api/DataApi";
import { getNodeState } from "../api/ClusterApi";
import type { NodeInfo } from "../types/cluster";
import type { NodeReadSnapshot } from "../components/NodeReadStatusPanel";

/** Fetch every active node's current status and value for one scenario key. */
export async function getNodeReadSnapshots(
  nodes: NodeInfo[],
  key: string,
): Promise<NodeReadSnapshot[]> {
  const snapshots: NodeReadSnapshot[] = [];

  // The backend routes replies through shared queues, so API calls remain
  // serial until that transport is replaced with per-request reply channels.
  for (const node of nodes) {
    if (node.status === "running") {
      const currentNode = await getNodeState(node.node_id);
      const response = await readFromNode(node.node_id, key);
      snapshots.push({ node: currentNode, value: response.value });
    }
  }

  return snapshots;
}
