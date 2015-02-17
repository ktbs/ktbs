# -*- coding=utf-8 -*-
#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RDF-REST is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with RDF-REST.  If not, see <http://www.gnu.org/licenses/>.

"""I provide a REST-Console, bundled in a single HTML file.
"""

REST_CONSOLE = r"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"></meta>
    <title>REST-Console</title>
    <style type="text/css">
/* importing rest-console.css */
#addressbar {
    width: 100%;
}

.combo {
    overflow-x: visible;
}

.combo *
{
    transition: all .3s;
}


.combo input:disabled ,
.combo input:enabled + select
{
    width: 0;
}
.combo input:disabled
{
    opacity: 0;
}

#method input:enabled ,
#method input:disabled + select
{
    width: 6em;
}

#ctype input:enabled ,
#ctype input:disabled + select
{
    width: 12em;
}

#payload {
    transition: all .5s;
    width: 100%;
    height: 20em;
}

#payload:disabled {
    height: 0;
    opacity: 0;
}
/* importing theme.css */
#response {
    transition: all .3s;
    border: 1px solid gray;
    background-color: lightYellow;
    padding: .5em;
}

#response.loading {
    border-color: darkGrey;
    background-color: lightGrey;
    color: darkGrey;
}

#response.error {
    border: 1px solid red;
    background-color: lightPink;
    color: red;
}

#response a {
    text-decoration: none;
}



#response-headers th {
    text-align: left;
}
    </style>
  </head>
  <body>

    <input id="addressbar">
    <div>

      <span id="method" class="combo">
        <input placeholder="GET" disabled>
        <select>
          <option>GET</option>
          <option>PUT</option>
          <option>POST</option>
          <option>DELETE</option>
          <option value="custom">custom</option>
        </select>
      </span>

      <span id="ctype" class="combo">
        <input placeholder="*/*" disabled>
        <select>
          <option>*/*</option>
          <option>application/json</option>
          <option>application/xml</option>
          <option>text/html</option>
          <option>text/plain</option>
          <option>text/turtle</option>
          <option value="custom">custom</option>
        </select>
      </span>

      <button id="send">Send</button>

    </div>

    <textarea id="payload" disabled></textarea>

    <pre id="response"></pre>

    <table id="response-headers"></table>

    <script type="application/javascript" 
>
/* importing rest-console.js */
// jshint browser:true, devel: true

(function() {
    window.addEventListener("load", function() {
        var addressbar = document.getElementById("addressbar"),
            methodCombo = document.getElementById("method"),
            methodInput = methodCombo.children[0],
            methodSelect = methodCombo.children[1],
            ctypeCombo = document.getElementById("ctype"),
            ctypeInput = ctypeCombo.children[0],
            ctypeSelect = ctypeCombo.children[1],
            send = document.getElementById("send"),
            payload = document.getElementById("payload"),
            response = document.getElementById("response"),
            responseHeaders = document.getElementById("response-headers"),
            etag = null;

        // define functions

        function updateCombo(evt) {
            var select = evt.target;
            var input = evt.target.parentNode.children[0];
            var val = select.selectedOptions[0].value;
            if (val === "custom") {
                input.disabled = false;
                input.focus();
            } else {
                input.value = val;
                input.disabled = true;
            }
            if (evt.target === methodSelect) {
                payload.disabled = (val === "GET" || val === "DELETE");
                if (val === "PUT") {
                    payload.value = response.textContent;
                }
            }
        }

        function enhanceResponse(req) {
            var ctype = req.getResponseHeader("content-type");
            var html = response.innerHTML;
            if (/json/.test(ctype) || /html/.test(ctype) || /xml/.test(ctype)) {
                html = html.replace(/""/g, '<a href="">""</a>');
                html = html.replace(/"([^">\n]+)"/g, '"<a href="$1">$1</a>"');
            } else {
                html = html.replace(/&lt;&gt;/g, '<a href="">&lt;&gt;</a>');
                html = html.replace(/&lt;([^&\n]+)&gt;/g, '&lt;<a href="$1">$1</a>&gt;');
            }
            response.innerHTML = html;
        }

        function updateCtypeSelect(newCtype) {
            var options = ctypeSelect.children;
            for(var i=0; i<options.length; i++) {
                if (options[i].value === newCtype) {
                    ctypeSelect.selectedIndex = i;
                    break;
                } else if (options[i].value === "custom") {
                    ctypeSelect.selectedIndex = i;
                    ctypeInput.value = newCtype;
                    console.log(ctypeInput.value);
                }
            }
            updateCombo({ target: ctypeSelect });
        }


        var LOADING_NEXT = {
            "": "loading |",
            "loading |": "loading /",
            "loading /": "loading —",
            "loading —": "loading \\",
            "loading \\": "loading |"
        };

        function sendRequest(evt) {
            if (!evt) evt = {};
            if (evt.forceget) {
                // unless ran as the Send event handler, force GET
                methodSelect.selectedIndex = 0;
                updateCombo({ target: methodSelect });
            }
            var req = new XMLHttpRequest(),
                method = methodInput.value || "GET",
                url = addressbar.value;
            url = url.split("#", 1)[0];
            if (method === "GET" || method === "HEAD") {
                // use JQuery hack to prevent cache
                var uncache = "_=" + Number(new Date());
                if (/\?/.test(addressbar.value)) {
                    url += "&" + uncache;
                } else {
                    url += "?" + uncache;
                }
            }
            req.open(method, url);
            req.setRequestHeader("cache-control", "private;no-cache");
            req.setRequestHeader("accept", ctypeInput.value);
            if (method !== "GET") {
                req.setRequestHeader("content-type", ctypeInput.value);
            }
            if (method === "PUT" || method === "DELETE") {
                if (etag) {
                    req.setRequestHeader("if-match", etag);
                }
            }
            if (!evt.poppingState && String(window.location) !== addressbar.value) {
                try {
                    window.history.pushState({}, addressbar.value, addressbar.value);
                }
                catch(err) {
                    if (err.name !== "SecurityError") throw err;
                    console.log("SecurityError prevented to pushState REST Console " +
                                addressbar.value);
                    // TODO is this ok or should we manage history more cleverly?
                }
            }
            response.textContent = "";
            response.classList.remove("error");
            response.classList.add("loading");
            responseHeaders.innerHTML = "";

            req.onreadystatechange = function() {
                response.textContent = LOADING_NEXT[response.textContent];
                if (req.readyState === 2) {
                    etag = null;
                    req.getAllResponseHeaders().split("\n").forEach(function(rh) {
                        if (!rh) return;
                        var match = /([^:]+): *(.*)/.exec(rh);
                        var key = match[1];
                        var val = match[2];
                        if (/location/i.test(key) || /link/i.test(key)) {
                            val = '<a href="' + val + '">' + val + '</a>';
                        }
                        if (/etag/i.test(key)) {
                            etag = val;
                        }
                        if (/content-type/i.test(key)) {
                            updateCtypeSelect(val.split(";", 1)[0]);
                        }
                        var row = document.createElement("tr");
                        row.innerHTML = "<th>" + key + "</th><td>" + val + "</th>";
                        responseHeaders.appendChild(row);
                    });
                } else if (req.readyState === 4) {
                    document.title = "REST Console - " + window.location;
                    response.classList.remove("loading");
                    if (Math.floor(req.status / 100) === 2) {
                        response.classList.remove("error");
                        response.textContent = req.responseText;
                        enhanceResponse(req);
                    } else {
                        response.classList.add("error");
                        if (req.statusText) {
                            response.textContent =
                                req.status + " " + req.statusText + "\n\n" +
                                req.responseText;
                        } else {
                            response.textContent = "Can not reach " + addressbar.value;
                        }
                    }
                }
            };
            if (payload.disabled) req.send();
            else req.send(payload.value);
        }

        function interceptLinks (evt) {
            if (evt.target.nodeName === "A") {
                evt.preventDefault();
                addressbar.value = evt.target.href;
                sendRequest({ forceget: true });
            }
        }

        // add event listeners

        window.addEventListener("popstate", function(e) {
            addressbar.value = window.location;
            sendRequest({ forceget: true, poppingState: true });
        });        

        window.addEventListener("keydown", function(evt) {
            if (evt.keyCode === 13 && evt.ctrlKey) { // ctrl+enter
                sendRequest();
            }
        });
        
        addressbar.addEventListener("keypress", function(evt) {
            if (evt.keyCode === 13) { // enter
                sendRequest({ forceget: true });
            }
        });

        payload.addEventListener("keydown", function(evt) {
            if (evt.keyCode === 9) { // tab
                // TODO insert  "   " properly
                evt.preventDefault();
            }
        });


        methodSelect.addEventListener("change", updateCombo);
        ctypeSelect.addEventListener("change", updateCombo);
        send.addEventListener("click", sendRequest);
        response.addEventListener("click", interceptLinks);
        responseHeaders.addEventListener("click", interceptLinks);


        // do immediately on load

        addressbar.value = window.location;
        updateCombo({ target: methodSelect });
        updateCombo({ target: ctypeSelect });
        sendRequest({ forceget: true });

    });
})();
</script>

  </body>
</html>
"""
