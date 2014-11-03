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

"""I provide functionalities to serialize RDF-REST resource in HTML.
"""
from rdflib import Literal, RDF, URIRef

def htmlize_node(bindings, node, base):
    """
    Generate simple HTML output for the given node.

    :param node:  a Node, unicode or ascii str
    :param base: a unicode or ascii str

    :rtype: unicode
    """
    #pylint: disable=R0911

    if isinstance(node, URIRef):
        curie = make_curie(bindings, node, base)
        if curie[0] == "&": # full URI
            return u"""<a href="%s">%s</a>""" % (
                node,
                make_curie(bindings, node, base),
            )
        else: # actual CURIE
            prefix, suffix = curie.split(":", 1)
            return (
                u'<a title="%s:%s" href="%s">'
                '<span class="prefix">%s:</span>%s'
                '</a>'
            ) % (prefix, suffix, node, prefix, suffix)
    elif isinstance(node, Literal):
        datatype = node.datatype
        value = unicode(node).replace("<", "&lt;")
        if '"' in node or '\n' in node:
            quoted = u'"""<pre style="display: inline">%s</pre>"""' % value
        else:
            quoted = u'"%s"' % value

        if datatype:
            if str(datatype) == "http://www.w3.org/2001/XMLSchema#integer":
                return unicode(node) # do not quote integers
            else:
                return u'%s^^%s' % (
                    quoted, htmlize_node(bindings, datatype, base),
                )
        elif node.language:
            return u'%s@"%s"' % (quoted, node.language)
        else:
            return quoted
    else:
        return u"_:%s" % node

def make_curie(bindings, uri, base):
    """
    Convert the given URI to a CURIE if possible.

    Parameters:
      uri: a Node, unicode or ascii str
      base: a unicode or ascii str

    Return:
      a unicode
    """
    for prefix, nsuri in bindings.items():
        if uri.startswith(nsuri) and str(uri) != str(nsuri):
            return u"%s:%s" % (prefix, uri[len(nsuri):])

    # TODO LATER improve this (this is an ugly way of relativizing a URI)
    base, filename = base.rsplit("/", 1)
    if uri.startswith(base+"/"):
        uri = uri[len(base)+1:]
        if uri == "" and filename:
            uri = "."
    else:
        parent, _ = base.rsplit("/", 1)
        if parent != "http:/" and uri.startswith(parent+"/"):
            uri = u"../" + uri[len(parent)+1:]

    return u"&lt;%s&gt;" % uri

def generate_crumbs(graph, resource, bindings, ctypes):
    """
    I generate bread crumbds by decomposing resource.uri.
    """
    ret = ""
    crumbs = resource.uri.split("/")
    crumbs[:3] = [ "/".join(crumbs[:3]) ]
    for i in xrange(len(crumbs)-1):
        link = "/".join(crumbs[:i+1]) + "/"
        ret += u'<a href="%s">%s</a>' % (link, crumbs[i] + "/",)
    ret += u'<a href="%s">%s</a>\n' % (resource.uri, crumbs[-1])
    return ret

def generate_formats(graph, resource, bindings, ctypes):
    """
    I generate a list of available formats, according to ctypes.
    """
    ret = "<div class='formats'>#\n"
    for ext in ctypes.itervalues():
        ret += u'<a href="%s.%s">%s</a>\n' % (resource.uri, ext, ext)
    ret += "</div>\n"
    return ret

def generate_prefixes(graph, resource, bindings, ctypes):
    """
    I generate a list of prefix declarations, according to bindings.
    """
    ret = '<div class="prefixes">\n'
    ret += u"<div>@base &lt;%s&gt; .</div>\n" % resource.uri
    for prefix, nsuri in bindings.items():
        ret += u"<div>@prefix %s: &lt;%s&gt; .</div>\n" % (prefix, nsuri)
    ret += "</div>\n"
    return ret

def generate_header(graph, resource, bindings, ctypes):
    """
    I generate a header with breadcrumbs, format list and prefix declarations.
    """
    return ("<h1># "
            + generate_crumbs(graph, resource, bindings, ctypes)
            + "</h1>\n"
            + generate_formats(graph, resource, bindings, ctypes)
            + generate_prefixes(graph, resource, bindings, ctypes))

def generate_htmlized_turtle(graph, resource, bindings, ctypes,
                             query="SELECT ?s ?p ?o WHERE {?s ?p ?o} "
                                   "ORDER BY ?s ?p ?o"):
    """
    I generate the actual turtle.
    """
    ret = ""
    uri = resource.uri
    old_subj = None
    old_pred = None
    for subj, pred, obj in graph.query(query):
        if subj != old_subj:
            if old_subj is not None:
                ret += ".</div></div></div>\n"
            ret += u'<div class="subj">%s\n' \
                   % htmlize_node(bindings, subj, uri)
            old_subj = subj
            old_pred = None
        if pred != old_pred:
            if old_pred is not None:
                ret += ";</div></div>\n"
            ret += u'\t<div class="pred">%s\n' \
                   % htmlize_node(bindings, pred, uri)
            old_pred = pred
        else:
            ret += ",</div>\n"
        ret += u'\t\t<div class="obj">%s\n' \
               % htmlize_node(bindings, obj, uri)
    ret += ".</div></div></div>\n"
    return ret

def generate_css(graph, resource, bindings, ctypes):
    """
    I generate the CSS for HTMLized turtle.
    """
    return """
    a { text-decoration: none; }
    .formats { font-size: 80%; font-style: italic; }
    .prefixes { font-size: 66%; float: right; }
    .prefix { display: none; }
    .subj { margin-top: 2ex; }
    .pred { margin-left: 2em ; }
    .obj  { margin-left: .5em ; display: inline; }
    #debug { font-size: 66%; color: blue }
    """

def generate_ajax_client_js(graph, resource, bindings, ctypes):
    """
    I generate the JS code for the embeded HTTP client.
    """
    return ("""var rdfrest_init_editor = function() {

    var ctypes = """ + repr(ctypes) + """;
    var metadata = {};
    var strip_ctype = /^[a-zA-Z0-9-]*\\/[a-zA-Z0-9-]*/;

    function toggle_editor() {
        var editor = document.getElementById("editor");
        var edit_button = document.getElementById("toggle");
        if (edit_button.value == "hide editor") {
            editor.hidden = true;
            edit_button.value = "show editor";
        } else {
            editor.hidden = false;
            if (edit_button.value == "edit") { // first time
                editor_get();
            }
            edit_button.value = "hide editor";
        }
    }

    function error_message(textarea, msg) {
        textarea.value = msg;
        textarea.style.color = "red";
    }

    function editor_get() {
        var textarea = document.getElementById("textarea");
        var ctype = document.getElementById("ctype");
        var debug = document.getElementById("debug");
        var req = make_req();
        var ext = ctypes[ctype.value];
        try {
            // we force the extension corresponding to the content-type,
            // so that we are not bothered by content-negociated cache
            req.open("GET", document.title + "." + ext, true);
            req.setRequestHeader("Accept", ctype.value);
            req.setRequestHeader("Cache-Control", "private");
        }
        catch(err) {
            error_message(textarea, "error while preparing request: " + err);
            return;
        }

        textarea.style.color = "";
        textarea.disabled = true;
        textarea.value = "loading..";

        req.onreadystatechange = function () {
            if (req.readyState != 4) {
                textarea.value += ".";
            } else {
                textarea.disabled = false;
                if (req.status == 200) {
                    textarea.value = req.responseText;
                    metadata.etag  = req.getResponseHeader("Etag");
                    debug.textContent = "etag: " + metadata.etag;
                    ctype.value = strip_ctype.exec(
                        req.getResponseHeader("Content-Type")
                    )[0];
                } else {
                    error_message(textarea,
                                  "error during GET: " + req.status +
                                  "\\n" + req.responseText);
                }
            }
        };
        req.send();
    };

    function editor_put() {
        var textarea = document.getElementById("textarea");
        var ctype = document.getElementById("ctype");
        var debug = document.getElementById("debug");
        var req = make_req();
        try {
            req.open("PUT", document.title, true);
            req.setRequestHeader("Accept", ctype.value);
            req.setRequestHeader("Content-Type", ctype.value);
            req.setRequestHeader("If-Match", metadata.etag);
        }
        catch(err) {
            error_message(textarea, "error while preparing PUT: " + err);
            return;
        }
        var payload = textarea.value;
        textarea.style.color = "";
        textarea.disabled = true;
        textarea.value = "loading..";

        req.onreadystatechange= function () {
            if (req.readyState != 4) {
                textarea.value += ".";
            } else {
                textarea.disabled = false;
                if (req.status == 200) {
                    textarea.value = req.responseText;
                    ctype.value = req.getResponseHeader("Content-Type");
                    metadata.etag   = req.getResponseHeader("Etag");
                    debug.textContent = "etag: " + metadata.etag;
                    window.location.assign(document.title+".html");                    
                } else {
                    error_message(textarea,
                                  "error during PUT: " + req.status +
                                  "\\n" + req.responseText);
                }
            }
        };
        req.send(payload);
    };

    function editor_post() {
        var textarea = document.getElementById("textarea");
        var ctype = document.getElementById("ctype");
        var req = make_req();
        try {
            req.open("POST", document.title, true);
            req.setRequestHeader("Content-Type", ctype.value);
        }
        catch(err) {
            error_message(textarea, "error while preparing POST: " + err);
            return;
        }

        var payload = textarea.value;
        textarea.style.color = "";
        textarea.disabled = true;
        textarea.value = "loading..";

        req.onreadystatechange= function () {
            if (req.readyState != 4) {
                textarea.value = textarea.value + ".";
            } else {
                textarea.disabled = false;
                if (req.status == 201) {
                    var location = req.getResponseHeader("Location");
                    window.location.assign(location)
                } else {
                    error_message(textarea,
                                  "error while posting: " + req.status +
                                  "\\n" + req.responseText);
                }
            }
        };
        req.send(payload);
    };

    function editor_delete() {
        var req = make_req();
        try {
            req.open("DELETE", document.title, true);
        }
        catch(err) {
            error_message(textarea, "error while preparing DELETE: " + err);
            return;
        }

        var payload = textarea.value;
        textarea.style.color = "";
        textarea.disabled = true;
        textarea.value = "loading..";

        req.onreadystatechange= function () {
            if (req.readyState != 4) {
                textarea.value = textarea.value + ".";
            } else {
                textarea.disabled = false;
                if (req.status == 204) {
                    // jump to parent
                    var cut = document.URL.slice(0, -1).lastIndexOf('/') + 1;
                    var location = document.URL.slice(0, cut);
                    window.location.assign(location);
                } else {
                    error_message(textarea,
                                  "error while deleting: " + req.status +
                                  "\\n" + req.responseText);
                }
            }
        };
        req.send();
    };

    function make_req() {
        var req;
        try  { req=new XMLHttpRequest(); }
        catch (e) {
            try { req=new ActiveXObject("Msxml2.XMLHTTP"); }
            catch (e) {
              try { req=new ActiveXObject("Microsoft.XMLHTTP"); }
              catch (e) {
                  alert("Your browser does not support AJAX!");
                  return false;
              }
          }
        }
        return req;
    }

    function ctype_change(evt) {
        var ctype = encodeURIComponent(evt.target.value);
        document.cookie = "rdfrest.ctype=" + ctype + ";path=/";
    }

    function get_prefered_ctype() {
        var ret = document.cookie.replace(/(?:(?:^|.*;\s*)rdfrest.ctype\s*\=\s*([^;]*).*$)|^.*$/, "$1");
        ret = decodeURIComponent(ret);
        return ret || "text/turtle" ;
    }

    document.getElementById("toggle").onclick = toggle_editor;
    document.getElementById("ctype").value = get_prefered_ctype();
    document.getElementById("ctype").onchange = ctype_change;
    document.getElementById("button_get").onclick = editor_get;
    document.getElementById("button_put").onclick = editor_put;
    document.getElementById("button_post").onclick = editor_post;
    document.getElementById("button_delete").onclick = editor_delete;

    if (document.referrer == document.location.href ||
        document.referrer == document.title) {
        // heuristic to detect we arrived here from the editor
        // then automatically re-open the editor
        toggle_editor();
    };

    };""")

def generate_ajax_client_html(graph, resource, bindings, ctypes):
    """
    I generate the HTML code for the embeded HTTP client.
    """
    return (
    """<br /><br /><hr />
    <input type="button" value="edit" id="toggle"/>
    <div id="editor" hidden="">
      <textarea id="textarea" cols="80" rows="16"></textarea>
      <br />
      <select id="ctype">
      """
    + "".join("<option>%s</option>" % i for i in ctypes)
    + """</select>
      <input type="button" value="GET"    id="button_get" />
      <input type="button" value="PUT"    id="button_put" />
      <input type="button" value="POST"   id="button_post" />
      <input type="button" value="DELETE" id="button_delete" />
      <div id="debug" style="color: blue" hidden=""></div>
    </div>
    """)
       

def serialize_htmlized_turtle(graph, resource, bindings, ctypes,
                              generate_style=generate_css,
                              generate_script=generate_ajax_client_js,
                              generate_header=generate_header,
                              generate_body=generate_htmlized_turtle,
                              generate_footer=generate_ajax_client_html,):
    """I serialize graph in a HTMLized simple turtle form.
    """
    #pylint: disable=R0914
    #    too many local variables

    page = u"""<!DOCTYPE html>
    <html>
    <head>
    <meta name="robots" content="noindex,nofollow">
    <meta charset="utf-8">
    <title>%(uri)s</title>
    <style type="text/css">%(style)s</style>
    <script type="text/javascript">%(script)s</script>
    </head>
    <body onload="rdfrest_init_editor()">
    %(header)s
    %(body)s
    %(footer)s
    </body>\n</html>""" % {
        "uri": resource.uri,
        "style": generate_style(graph, resource, bindings, ctypes),
        "script": generate_script(graph, resource, bindings, ctypes),
        "header": generate_header(graph, resource, bindings, ctypes),
        "body": generate_body(graph, resource, bindings, ctypes),
        "footer": generate_footer(graph, resource, bindings, ctypes),
    }

    # We use yield to prevent the serialization to happen if a 304 is returned
    yield page.encode("utf-8")
