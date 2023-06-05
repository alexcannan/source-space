console.log("hello from js")


function fetchServerSentEvents(url) {
  const sse = new EventSource(url, { });

  // see articlesa.types.StreamEvent for event types

  sse.addEventListener("stream_begin", (e) => {
    console.log("stream beginning");
  });

  sse.addEventListener("node_processing", (e) => {
    console.log("processing", e.data);
  });

  sse.addEventListener("node_render", (e) => {
    console.log("got data", e.data);
  });

  sse.addEventListener("node_failure", (e) => {
    console.log("failure", e.id);
  });

  sse.addEventListener("stream_end", (e) => {
    console.log("stream ending");
    sse.close();
  } );
};


window.addEventListener('DOMContentLoaded', function() {
  console.log("dom loaded");

  document.getElementById('sseForm').addEventListener('submit', function(event) {
    event.preventDefault();

    var url = document.getElementById('urlInput').value;

    fetchServerSentEvents(`/a/${url}`);
    });
});
