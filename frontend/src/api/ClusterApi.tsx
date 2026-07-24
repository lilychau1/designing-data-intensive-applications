import type {
  NodeInfo,
  NodeStatusResponse,
} from "../types/cluster";

const API_BASE_URL = "http://localhost:8000";

export async function getClusterStatus(): Promise<NodeStatusResponse> {
  const response = await fetch(
    `${API_BASE_URL}/cluster/node-statuses`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch cluster status");
  }

  return response.json();
}

export async function getActiveClusterStatus(): Promise<NodeStatusResponse> {
  const response = await fetch(
    `${API_BASE_URL}/cluster/active-node-statuses`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch active cluster status");
  }

  return response.json();
}

export async function getNodeState(
  nodeId: string
): Promise<NodeInfo> {
  const response = await fetch(
    `${API_BASE_URL}/cluster/nodes/${nodeId}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch node ${nodeId}`);
  }

  return response.json();
}

export async function removeNode(
  nodeId: string
): Promise<NodeStatusResponse> {
  const response = await fetch(
    `${API_BASE_URL}/cluster/nodes/${nodeId}/remove`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to remove node ${nodeId}`);
  }

  return response.json();
}