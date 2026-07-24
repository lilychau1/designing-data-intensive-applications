import type { ClusterEvent } from "../types/events";

interface EventTimelineProps {
  events: ClusterEvent[];
}

export default function EventTimeline({
  events,
}: EventTimelineProps) {
  return (
    <section>
      <h2>Event Timeline</h2>

      {events.length === 0 ? (
        <p>No events yet.</p>
      ) : (
        <div>
          {events.map((event) => (
            <div key={event.id}>
              <strong>
                {event.type}
              </strong>

              <p>
                {event.message}
              </p>

              <small>
                {new Date(
                  event.timestamp
                ).toLocaleTimeString()}
              </small>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}