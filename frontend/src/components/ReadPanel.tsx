import { useState } from "react";

interface ReadPanelProps {
  onRead: (
    key: string
  ) => Promise<{
    node_id: string;
    key: string;
    value: unknown;
  } | null>;
  loading: boolean;
}

function ReadPanel({
  onRead,
  loading,
}: ReadPanelProps) {
  const [key, setKey] = useState("");
  const [result, setResult] = useState<{
    node_id: string;
    key: string;
    value: unknown;
  } | null>(null);

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!key.trim()) {
      return;
    }

    const response = await onRead(
      key.trim()
    );

    setResult(response);
  }

  return (
    <section className="operation-panel">
      <h2>Read from Leader</h2>

      <p>
        Reads are served by the current leader.
      </p>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="read-key">
            Key
          </label>

          <input
            id="read-key"
            type="text"
            value={key}
            onChange={(event) =>
              setKey(event.target.value)
            }
            placeholder="e.g. name"
          />
        </div>

        <button
          type="submit"
          disabled={
            loading ||
            !key.trim()
          }
        >
          {loading
            ? "Reading..."
            : "Read"}
        </button>
      </form>

      {result && (
        <div className="read-result">
          <h3>Read Result</h3>

          <p>
            <strong>Served by:</strong>{" "}
            {result.node_id}
          </p>

          <p>
            <strong>Key:</strong>{" "}
            {result.key}
          </p>

          <p>
            <strong>Value:</strong>{" "}
            {String(result.value)}
          </p>
        </div>
      )}
    </section>
  );
}

export default ReadPanel;