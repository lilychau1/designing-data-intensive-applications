export type EventType =
  | "node_removed"
  | "node_restarted"
  | "leader_elected"
  | "write_direct"
  | "write_replicated"
  | "read_operation";

export interface ClusterEvent {
  id: string;
  type: EventType;
  nodeId: string;
  message: string;
  timestamp: string;

  // Data operation information
  key?: string;
  value?: unknown;
}