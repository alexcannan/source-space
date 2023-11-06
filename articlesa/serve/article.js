console.log("hello from js")


window.addEventListener('DOMContentLoaded', function() {
  console.log("dom loaded");

  var cy = cytoscape({
    container: document.getElementById('graph'),
  });

  cy.on('add', 'node', _evt => {
    console.log("got node add event...")
    var layout = cy.layout({
      name: 'concentric',
      concentric: function( node ){ // returns numeric value for each node, placing higher nodes in levels towards the centre
        return 10 - 2*node.data('depth');
        },
      });
    layout.run();
  })

  cy.style()
  .clear()
  .selector('node')
    .style({
      'background-color': 'gray',
      'shape': 'round-rectangle',
      'width': 90,
      'height': 60,
      'text-opacity': 0.7,
      'text-valign': 'center',
      'text-halign': 'center',
      'text-wrap': 'nowrap',
      'opacity': 0.7,
    })
  .selector('node.success')
    .style({
      'opacity': 1,
      'background-color': 'green',
    })
  .selector('node.failure')
    .style({
      'opacity': 1,
      'background-color': 'red',
    })
  .selector('edge')
      .style({
      'width': 3,
      'opacity': 0.9,
      'line-color': 'black',
      'mid-target-arrow-shape': 'triangle',
      'mid-target-arrow-color': 'black',
    })
  .update();

  window.cy = cy;

  window.cy.nodeHtmlLabel([
    {
      query: 'node', // cytoscape query selector
      halign: 'center', // title vertical position. Can be 'left',''center, 'right'
      valign: 'center', // title vertical position. Can be 'top',''center, 'bottom'
      halignBox: 'center', // title vertical position. Can be 'left',''center, 'right'
      valignBox: 'center', // title relative box vertical position. Can be 'top',''center, 'bottom'
      cssClass: 'nodeinfo', // any classes will be as attribute of <div> container for every title
      tpl(data) {
        // no idea why 3 <br>s and a newline are needed to get the title to show up
        // TODO: if the node is processing, we can display a loading thing here
        return `<div><div class="nodedepth">${data.depth}</div><span class="articlenetloc">${data.netloc}</span><br><span class="articletitle">${data.title}</span><br><a class="articlelink" href="${data.url}"><svg width="10" height="10"><use xlink:href="#outlinksvg"></use></svg></a></div>`;
      }
    }
  ]);

  function getHostname(url) {
    var a = document.createElement('a');
    a.href = url;
    return a.hostname;
  }

  var SSERunning = false;

  function fetchServerSentEvents(url) {
    if (SSERunning) {
      console.log("cool your jets, we're already running");
      return;
    }

    const sse = new EventSource(url, { });

    // see articlesa.types.StreamEvent for event types

    sse.addEventListener("stream_begin", (e) => {
      console.log("stream beginning");
      SSERunning = true;
      window.cy.elements().remove();  // clear the graph
    });

    sse.addEventListener("node_processing", (e) => {
      console.debug("processing", e.data);  // urlhash; parent
      parsedData = JSON.parse(e.data);
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
      console.debug("got data", e.data);  // urlhash; parent; title; url; published;
      parsedData = JSON.parse(e.data);
      parsedData.netloc = getHostname(parsedData.url);
      window.cy.$id(parsedData.urlhash).data(parsedData);
      window.cy.$id(parsedData.urlhash).addClass('success');
    });

    sse.addEventListener("node_failure", (e) => {
      console.debug("failure", e.data);
      parsedData = JSON.parse(e.data);
      parsedData.netloc = getHostname(parsedData.url);
      window.cy.$id(parsedData.urlhash).data(parsedData);
      window.cy.$id(parsedData.urlhash).addClass('failure');
    });

    sse.addEventListener("stream_end", (e) => {
      console.log("stream ending");
      sse.close();
      SSERunning = false;
    } );
  };

  document.getElementById('sseForm').addEventListener('submit', function(event) {
    event.preventDefault();

    var url = document.getElementById('urlInput').value;

    fetchServerSentEvents(`/a/${url}`);
  });

});
