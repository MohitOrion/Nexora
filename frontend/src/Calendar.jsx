
import { useEffect, useState } from 'react';
import './Calendar.css';

const STORAGE_KEY = 'nexora-calendar-events';

function dateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function Calendar() {
  const [currentMonth, setCurrentMonth] = useState(() => new Date());
  const [selectedDate, setSelectedDate] = useState(() => dateKey(new Date()));
  const [events, setEvents] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch {
      return {};
    }
  });
  const [eventTitle, setEventTitle] = useState('');
  const [eventTime, setEventTime] = useState('10:00');

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(events));
  }, [events]);

  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const calendarDays = [
    ...Array(firstDay).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  const selectedEvents = [...(events[selectedDate] || [])].sort(
    (a, b) => a.time.localeCompare(b.time)
  );

  function changeMonth(offset) {
    setCurrentMonth(new Date(year, month + offset, 1));
  }

  function addEvent(e) {
    e.preventDefault();
    const title = eventTitle.trim();
    if (!title) return;

    const newEvent = {
      id: `${Date.now()}-${Math.random()}`,
      title,
      time: eventTime,
    };

    setEvents(previous => ({
      ...previous,
      [selectedDate]: [...(previous[selectedDate] || []), newEvent],
    }));

    setEventTitle('');
  }

  function deleteEvent(id) {
    setEvents(previous => {
      const remaining = (previous[selectedDate] || []).filter(
        event => event.id !== id
      );
      const updated = { ...previous };

      if (remaining.length) updated[selectedDate] = remaining;
      else delete updated[selectedDate];

      return updated;
    });
  }

  function formatSelectedDate() {
    const [y, m, d] = selectedDate.split('-').map(Number);
    return new Date(y, m - 1, d).toLocaleDateString('en-IN', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  }

  const today = dateKey(new Date());

  return (
    <section className="nexora-calendar">
      <header className="calendar-heading">
        <div>
          <p className="calendar-eyebrow">PLAN YOUR JOURNEY</p>
          <h2>My Calendar</h2>
          <p className="calendar-subtitle">
            Keep track of deadlines, interviews and important events.
          </p>
        </div>
        <button
          className="calendar-today"
          onClick={() => {
            const now = new Date();
            setCurrentMonth(now);
            setSelectedDate(dateKey(now));
          }}
        >
          Today
        </button>
      </header>

      <div className="calendar-layout">
        <div className="calendar-month-panel">
          <div className="calendar-month-header">
            <button
              className="calendar-nav"
              onClick={() => changeMonth(-1)}
              aria-label="Previous month"
            >
              &#8592;
            </button>

            <h3>
              {currentMonth.toLocaleDateString('en-US', {
                month: 'long',
                year: 'numeric',
              })}
            </h3>

            <button
              className="calendar-nav"
              onClick={() => changeMonth(1)}
              aria-label="Next month"
            >
              &#8594;
            </button>
          </div>

          <div className="calendar-grid">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div className="calendar-weekday" key={day}>
                {day}
              </div>
            ))}

            {calendarDays.map((day, index) => {
              if (!day) {
                return <div className="calendar-empty" key={`empty-${index}`} />;
              }

              const date = dateKey(new Date(year, month, day));
              const isSelected = date === selectedDate;
              const isToday = date === today;
              const hasEvents = Boolean(events[date]?.length);

              return (
                <button
                  key={date}
                  className={[
                    'calendar-day',
                    isSelected ? 'selected' : '',
                    isToday ? 'is-today' : '',
                  ].filter(Boolean).join(' ')}
                  onClick={() => setSelectedDate(date)}
                  aria-pressed={isSelected}
                  aria-label={`${date}${hasEvents ? ', has events' : ''}`}
                >
                  <span>{day}</span>
                  {hasEvents && <i className="calendar-event-dot" />}
                </button>
              );
            })}
          </div>

          <div className="calendar-legend">
            <span><i className="legend-today" /> Today</span>
            <span><i className="legend-event" /> Has events</span>
          </div>
        </div>

        <aside className="calendar-events-panel">
          <p className="calendar-eyebrow">YOUR SCHEDULE</p>
          <h3>{formatSelectedDate()}</h3>

          <form className="calendar-event-form" onSubmit={addEvent}>
            <label htmlFor="calendar-event-title">Event or reminder</label>
            <input
              id="calendar-event-title"
              value={eventTitle}
              onChange={e => setEventTitle(e.target.value)}
              placeholder="e.g. Scholarship deadline"
              maxLength={120}
              required
            />

            <label htmlFor="calendar-event-time">Time</label>
            <input
              id="calendar-event-time"
              type="time"
              value={eventTime}
              onChange={e => setEventTime(e.target.value)}
              required
            />

            <button className="calendar-add-button" type="submit">
              + Add event
            </button>
          </form>

          <div className="calendar-event-list">
            <h4>Events ({selectedEvents.length})</h4>

            {selectedEvents.length === 0 ? (
              <div className="calendar-no-events">
                <span className="calendar-empty-icon">&#128197;</span>
                <p>No events planned</p>
                <small>Add a reminder for this date.</small>
              </div>
            ) : (
              selectedEvents.map(event => (
                <article className="calendar-event-card" key={event.id}>
                  <div className="calendar-event-accent" />
                  <div className="calendar-event-details">
                    <strong>{event.title}</strong>
                    <span>
                      {event.time}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="calendar-delete"
                    onClick={() => deleteEvent(event.id)}
                    aria-label={`Delete ${event.title}`}
                    title="Delete event"
                  >
                    &#10005;
                  </button>
                </article>
              ))
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}
