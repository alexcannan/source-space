console.log("hello from js")


function connect() {
  window.ws = new WebSocket((window.location.protocol == 'https:' ? "wss://" : "ws://") + window.location.host + '/ws' + window.location.pathname + window.location.search);
  console.log(window.ws)
  ws.onmessage = function(event) {
      eval(event.data);
  };
  ws.onopen = function(event) {
      window.ws_backoff = 1000;
      console.log("Websocket connected.");
  };
  ws.onclose = function(event) {
      console.error(event);
      console.log(`Socket was closed, trying to reconnect in ${window.ws_backoff}ms.`);
      setTimeout(connect, window.ws_backoff);
      window.ws_backoff = window.ws_backoff * 2;
  };
}


window.addEventListener('DOMContentLoaded', function() {
  connect();
  mermaid.initialize({securityLevel: 'loose'});
});


async function updateMermaid(content) {
  console.log(content);
  var el = document.getElementById("treegraph");
  el.innerHTML = content;
  // we replace newlines with <br> when sending through websocket, change them back here
  content = content.replace(/<br>/g, '\n');
  el.innerHTML = await mermaid.render('idk', content);
}