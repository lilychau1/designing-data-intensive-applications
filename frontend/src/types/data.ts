export interface ReplicaReadResult {
  nodeId: string;
  value: unknown;
  error?: string;
}