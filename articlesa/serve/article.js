console.log("hello from js")


window.addEventListener('DOMContentLoaded', function() {
  console.log("dom loaded");

  var cy = cytoscape({
    container: document.getElementById('graph'),
  });
  console.log(cy);

  function fetchServerSentEvents(url) {
    const sse = new EventSource(url, { });

    // see articlesa.types.StreamEvent for event types

    sse.addEventListener("stream_begin", (e) => {
      console.log("stream beginning");
    });

    sse.addEventListener("node_processing", (e) => {
      console.log("processing", e.data);  // urlhash; parent
      parsedData = JSON.parse(e.data);
      cy.add({
        group: 'nodes',
        data: { id: parsedData.urlhash, parent: parsedData.parent },
        position: { x: 0, y: 0 }
      });
    });

    sse.addEventListener("node_render", (e) => {
      console.log("got data", e.data);  // urlhash; parent; title; url; published;
    });

    sse.addEventListener("node_failure", (e) => {
      console.log("failure", e.id);
    });

    sse.addEventListener("stream_end", (e) => {
      console.log("stream ending");
      sse.close();
    } );
  };

  document.getElementById('sseForm').addEventListener('submit', function(event) {
    event.preventDefault();

    var url = document.getElementById('urlInput').value;

    fetchServerSentEvents(`/a/${url}`);
  });

});
