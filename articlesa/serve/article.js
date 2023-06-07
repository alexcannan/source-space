console.log("hello from js")


window.addEventListener('DOMContentLoaded', function() {
  console.log("dom loaded");

  var cy = cytoscape({
    container: document.getElementById('graph'),
  });

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
      'width': 90,
      'height': 60,
      'text-opacity': 0.7,
      'text-valign': 'center',
      'text-halign': 'center',
      'text-wrap': 'wrap',
      'opacity': 0.7,
    })
  .selector('node.success')
    .style({
      'opacity': 0.9,
      'background-color': 'green',
    })
  .selector('node.failure')
    .style({
      'opacity': 0.9,
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
      cssClass: '', // any classes will be as attribute of <div> container for every title
      tpl(data) {
        // no idea why 3 <br>s and a newline are needed to get the title to show up
        // TODO: if no title, show loading spinner
        return `<span class="netloc">${data.netloc}</span><br><br><br>\n<span class="title">${data.title}</span>`;
      }
    }
  ]);

  function getHostname(url) {
    var a = document.createElement('a');
    a.href = url;
    return a.hostname;
  }

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
      parsedData.netloc = getHostname(parsedData.url);
      window.cy.$id(parsedData.urlhash).data(parsedData);
      window.cy.$id(parsedData.urlhash).addClass('success');
    });

    sse.addEventListener("node_failure", (e) => {
      console.log("failure", e.data);
      parsedData = JSON.parse(e.data);
      parsedData.netloc = getHostname(parsedData.url);
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
