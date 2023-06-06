console.log("hello from js")


window.addEventListener('DOMContentLoaded', function() {
  console.log("dom loaded");

  var cy = cytoscape({
    container: document.getElementById('graph'),
  });

  let options = {
    name: 'random',
  };

  cy.on('add', 'node', _evt => {
    console.log("got node add event...")
    var layout = cy.layout({ name: 'cose' });
    layout.run();
  })

  cy.style()
  .clear()
  .selector('node')
    .style({
      'background-color': 'gray',
      'shape': 'round-rectangle',
      'text-opacity': 0.7,
    })
  .selector('node.success')
    .style({
      'background-color': 'green',
      'label': 'data(title)',
    })
  .selector('node.failure')
    .style({
      'background-color': 'red',
      'label': 'data(status)',
    })
  .selector('edge')
      .style({
      'width': 3,
      'line-color': 'black',
      'mid-target-arrow-shape': 'triangle',
      'mid-target-arrow-color': 'black',
    })
  .update();

  window.cy = cy;



  function fetchServerSentEvents(url) {
    const sse = new EventSource(url, { });

    // see articlesa.types.StreamEvent for event types

    sse.addEventListener("stream_begin", (e) => {
      console.log("stream beginning");
    });

    sse.addEventListener("node_processing", (e) => {
      console.log("processing", e.data);  // urlhash; parent
      parsedData = JSON.parse(e.data);
      console.log("parsed", parsedData)
      cy.add({
        data: { id: parsedData.urlhash },
      });
      if (parsedData.parent) {
        edgeObject = {
          id: `${parsedData.parent}->${parsedData.urlhash}`,
          source: parsedData.parent,
          target: parsedData.urlhash
        }
        cy.add({data: edgeObject})
      }
    });

    sse.addEventListener("node_render", (e) => {
      console.log("got data", e.data);  // urlhash; parent; title; url; published;
      parsedData = JSON.parse(e.data);
      window.cy.$id(parsedData.urlhash).data(parsedData);
      window.cy.$id(parsedData.urlhash).addClass('success');
    });

    sse.addEventListener("node_failure", (e) => {
      console.log("failure", e.data);
      parsedData = JSON.parse(e.data);
      window.cy.$id(parsedData.urlhash).data(parsedData);
      window.cy.$id(parsedData.urlhash).addClass('failure');
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
