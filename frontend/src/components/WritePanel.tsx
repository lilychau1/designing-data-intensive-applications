import { useState } from "react";

interface WritePanelProps {
  onWrite: (
    key: string,
    value: string
  ) => Promise<void>;
  loading: boolean;
}

function WritePanel({
  onWrite,
  loading,
}: WritePanelProps) {
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!key.trim()) {
      return;
    }

    await onWrite(
      key.trim(),
      value
    );

    setKey("");
    setValue("");
  }

  return (
    <section className="operation-panel">
      <h2>Write to Cluster</h2>

      <p>
        Writes are sent to the current leader and
        replicated to the followers.
      </p>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="write-key">
            Key
          </label>

          <input
            id="write-key"
            type="text"
            value={key}
            onChange={(event) =>
              setKey(event.target.value)
            }
            placeholder="e.g. name"
          />
        </div>

        <div>
          <label htmlFor="write-value">
            Value
          </label>

          <input
            id="write-value"
            type="text"
            value={value}
            onChange={(event) =>
              setValue(event.target.value)
            }
            placeholder="e.g. Alice"
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
            ? "Writing..."
            : "Write"}
        </button>
      </form>
    </section>
  );
}

export default WritePanel;