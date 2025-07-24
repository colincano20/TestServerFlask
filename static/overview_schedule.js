document.addEventListener('DOMContentLoaded', function () {
      const calendarEl = document.getElementById('schedule');
      const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridDay',
        weekends: false,
        contentHeight: 'auto',
        expandRows: true,    
              // Allow vertical compression
        slotMinTime: "08:00:00", // 🕗 Start the calendar at 8:00 AM
        slotMaxTime: "22:00:00",      // End at 10 PM
        allDaySlot: false,
        slotDuration: "01:00:00", // Optional: make slots shorter
        headerToolbar: false,
        events: '/class_events',
        eventDidMount: function(info) {
          info.el.title = `${info.event.title}\n${info.event.start.toLocaleString()}`;
        }
      });

      calendar.render();
    });