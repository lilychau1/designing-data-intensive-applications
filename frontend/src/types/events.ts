export type EventType =
  | "node_removed"
  | "node_restarted"
  | "leader_elected";

export interface ClusterEvent {
  id: string;
  type: EventType;
  nodeId: string;
  message: string;
  timestamp: string;
}