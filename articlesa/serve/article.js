console.log("hello from js")


function fetchServerSentEvents(url) {
  const sse = new EventSource(`/a/${url}`);

  // see articlesa.types.StreamEvent for event types

  sse.addEventListener("stream_begin", (e) => {
    console.log("stream beginning");
  });

  sse.addEventListener("node_processing", (e) => {
    console.log("processing", e.id);
  });

  sse.addEventListener("node_render", (e) => {
    console.log(e.data);
  });

  sse.addEventListener("node_failure", (e) => {
    console.log("failure", e.id);
  });

  sse.addEventListener("stream_end", (e) => {
    console.log("stream ending");
  } );
};


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
