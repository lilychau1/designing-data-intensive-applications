const API_BASE_URL = "http://localhost:8000";

export interface WriteResponse {
  node_id: string;
  key: string;
  value: unknown;
}

export interface ReadResponse {
  node_id: string;
  key: string;
  value: unknown;
}

export async function writeData(
  key: string,
  value: string
): Promise<WriteResponse> {
  const response = await fetch(`${API_BASE_URL}/set`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      key,
      value,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to write data");
  }

  return response.json();
}

export async function readFromLeader(
  key: string
): Promise<ReadResponse> {
  const response = await fetch(
    `${API_BASE_URL}/get/${encodeURIComponent(key)}`
  );

  if (!response.ok) {
    throw new Error("Failed to read data from leader");
  }

  return response.json();
}

export async function readFromNode(
  nodeId: string,
  key: string
): Promise<ReadResponse> {
  const response = await fetch(
    `${API_BASE_URL}/nodes/${encodeURIComponent(nodeId)}/get/${encodeURIComponent(key)}`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to read data from node ${nodeId}`
    );
  }

  return response.json();
}