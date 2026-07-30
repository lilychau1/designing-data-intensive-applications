import type { ClusterEvent } from "../types/events";

interface NodeEventTimelineProps {
  events: ClusterEvent[];
}

function NodeEventTimeline({
  events,
}: NodeEventTimelineProps) {
  return (
    <div className="node-event-timeline">
      <h4>Event Timeline</h4>

      {events.length === 0 ? (
        <p className="node-event-empty">
          No events for this node yet.
        </p>
      ) : (
        <div className="node-event-list">
          {events.map((event) => (
            <div
              key={event.id}
              className="node-event"
            >
              <div className="node-event-header">
                <span className="node-event-type">
                  {event.type}
                </span>

                <span className="node-event-time">
                  {new Date(
                    event.timestamp
                  ).toLocaleTimeString()}
                </span>
              </div>

              <div className="node-event-message">
                {event.message}
              </div>

              {event.key !== undefined && (
                <div className="node-event-detail">
                  <strong>Key:</strong>{" "}
                  {event.key}
                </div>
              )}

              {event.value !== undefined && (
                <div className="node-event-detail">
                  <strong>Value:</strong>{" "}
                  {String(event.value)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default NodeEventTimeline;