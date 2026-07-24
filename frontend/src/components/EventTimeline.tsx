interface EventTimelineProps {
  events?: string[];
}

export default function EventTimeline({
  events = [],
}: EventTimelineProps) {
  return (
    <section>
      <h2>Event Timeline</h2>

      {events.length === 0 ? (
        <p>No events yet.</p>
      ) : (
        <ul>
          {events.map((event, index) => (
            <li key={index}>
              {event}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}