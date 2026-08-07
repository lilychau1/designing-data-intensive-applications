import type { ClusterEvent } from "../types/events";

const API_BASE_URL = "http://localhost:8000";

export interface WriteResponse {
  node_id: string;
  key: string;
  value: unknown;
  events: ApiClusterEvent[];
}

/** The event shape exposed by the Python API. */
interface ApiClusterEvent {
  node_id: string;
  event_type: "WRITE_DIRECT" | "WRITE_REPLICATION";
  timestamp: string;
  key?: string;
  value?: unknown;
  message?: string | null;
}

export interface ReadResponse {
  node_id: string;
  key: string;
  value: unknown;
}

function toEventType(
  eventType: ApiClusterEvent["event_type"]
): ClusterEvent["type"] {
  switch (eventType) {
    case "WRITE_DIRECT":
      return "write_direct";
    case "WRITE_REPLICATION":
      return "write_replicated";
  }
}

/** Convert the Python API contract once, before data reaches UI components. */
export function toClusterEvent(
  event: ApiClusterEvent
): ClusterEvent {
  const type = toEventType(event.event_type);

  return {
    // The API has no event id. These fields identify an emitted event and allow
    // the UI to de-duplicate the write response from the later /events poll.
    id: [event.node_id, type, event.timestamp, event.key ?? ""].join(":"),
    type,
    nodeId: event.node_id,
    timestamp: event.timestamp,
    key: event.key,
    value: event.value,
    message: event.message ?? `${event.node_id} ${type}`,
  };
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

/** Retrieve emitted node events, including asynchronous follower replication. */
export async function getClusterEvents(): Promise<ClusterEvent[]> {
  const response = await fetch(`${API_BASE_URL}/events`);

  if (!response.ok) {
    throw new Error("Failed to retrieve cluster events");
  }

  const events: ApiClusterEvent[] = await response.json();
  return events.map(toClusterEvent);
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
