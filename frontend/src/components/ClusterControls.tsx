interface ClusterControlsProps {
  onRefresh: () => void;
}

export function ClusterControls({
  onRefresh,
}: ClusterControlsProps) {
  return (
    <section>
      <button onClick={onRefresh}>
        Refresh cluster
      </button>
    </section>
  );
}