console.log("hello from js")


function fetchServerSentEvents(url, onEventReceived) {
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    const eventData = JSON.parse(event.data);
    const eventType = eventData.event;
    const eventDataParsed = eventData.data;

    onEventReceived(eventType, eventDataParsed);
  };

  eventSource.onerror = (error) => {
    console.error('Error occurred while fetching server-sent events:', error);
    eventSource.close();
  };
}


window.addEventListener('DOMContentLoaded', function() {
  console.log("dom loaded");

  document.getElementById('sseForm').addEventListener('submit', function(event) {
    event.preventDefault();

    var url = document.getElementById('urlInput').value;

    fetchServerSentEvents(`/a/${url}`, function(eventType, eventData) {
      // Perform actions based on the event type
      console.log("event type", eventType)
      if (eventType === 'event_type_1') {
        // Handle event type 1
        console.log('Event type 1:', eventData);
      } else if (eventType === 'event_type_2') {
        // Handle event type 2
        console.log('Event type 2:', eventData);
      } else {
        // Handle other event types
        console.log('Unknown event type:', eventType);
      }
    });
  });
});
