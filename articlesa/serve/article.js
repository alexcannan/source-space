console.log("hello from js")


window.addEventListener('DOMContentLoaded', function() {
  console.log("dom loaded");

  var cy = cytoscape({
    container: document.getElementById('graph'),
  });

  let options = {
    name: 'concentric',

    fit: true, // whether to fit the viewport to the graph
    padding: 30, // the padding on fit
    startAngle: 1 / 2 * Math.PI, // where nodes start in radians
    sweep: undefined, // how many radians should be between the first and last node (defaults to full circle)
    clockwise: true, // whether the layout should go clockwise (true) or counterclockwise/anticlockwise (false)
    equidistant: false, // whether levels have an equal radial distance betwen them, may cause bounding box overflow
    minNodeSpacing: 10, // min spacing between outside of nodes (used for radius adjustment)
    avoidOverlap: true, // prevents node overlap, may overflow boundingBox if not enough space
    nodeDimensionsIncludeLabels: false, // Excludes the label when calculating node bounding boxes for the layout algorithm
    spacingFactor: undefined, // Applies a multiplicative factor (>0) to expand or compress the overall area that the nodes take up
    concentric: function( node ){ // returns numeric value for each node, placing higher nodes in levels towards the centre
      return node.data.depth;
    },
    levelWidth: function( nodes ){ // the variation of concentric values in each level
      return nodes.maxDegree() / 4;
    },
    animate: true, // whether to transition the node positions
  };

  const layout = cy.layout( options );
  cy.on('add', 'node', _evt => {
    layout.run();
  })

  this.window.cy = cy;

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
        data: { id: parsedData.urlhash, parent: parsedData.parent },
        position: { x: cy.width() / 2, y: cy.height() / 2 },
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
