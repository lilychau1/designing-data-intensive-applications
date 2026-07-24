export type ClusterEventType =
  | "node_removed"
  | "leader_changed"
  | "cluster_updated";

export interface ClusterEvent {
  id: string;
  type: ClusterEventType;
  message: string;
  timestamp: string;
}