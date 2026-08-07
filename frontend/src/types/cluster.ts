export type NodeStatus =
  | "running"
  | "stopped"
  | "removed";

export type NodeRole =
  | "leader"
  | "follower";

export interface NodeInfo {
  node_id: string;
  role: NodeRole;
  status: NodeStatus;
  last_applied_index: number;
  replication_delay: number;
}

export interface NodeStatusResponse {
  leader_id: string | null;
  nodes: NodeInfo[];
}