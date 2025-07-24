document.addEventListener('DOMContentLoaded', function () {
      const calendarEl = document.getElementById('calendar');
      const calendar = new FullCalendar.Calendar(calendarEl, {
        
        initialView: 'dayGridMonth', // or 'dayGridWeek'
        expandRows: true, 
        eventTimeFormat: {
        hour: 'numeric',
        minute: '2-digit',
        meridiem: 'short'
      },

       
        events: '/events',
        
        height:500,
        eventDidMount: function(info) {
      // If you want to customize tooltip
      info.el.title = `Title: ${info.event.title}\nDate: ${info.event.start.toLocaleString()}`;
      if (info.event.allDay) {
        // All-day event styling
        info.el.style.backgroundColor = '#524F81'; // pruple
        info.el.style.color = 'black';
        info.el.style.fontWeight = 'bold';
        info.el.style.border = 'none';
      } else {
        // Timed event styling
        info.el.style.backgroundColor = '#424242'; // grey
        info.el.style.color = 'white';
        info.el.style.borderRadius = '4px';
        info.el.style.padding = '0px 0px';
        info.el.style.fontWeight = '500';
      }
      
    },

    eventClick: function(info) {
      // Optional: prevent default behavior
      info.jsEvent.preventDefault();

      // Show alert (you can replace this with a popup or modal)
      alert(`Event: ${info.event.title}\nDate: ${info.event.start.toLocaleString()}`);
      
    }
        
      });
      calendar.render();
    });