import type { ClusterEvent } from "../types/events";

interface EventTimelineProps {
  events: ClusterEvent[];
}

export function EventTimeline({
  events,
}: EventTimelineProps) {
  return (
    <section>
      <h2>Event Timeline</h2>

      {events.length === 0 ? (
        <p>No events yet.</p>
      ) : (
        <ul>
          {events.map((event) => (
            <li key={event.id}>
              <strong>
                {event.type}
              </strong>

              <p>
                {event.message}
              </p>

              <small>
                {new Date(event.timestamp).toLocaleString()}
              </small>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}