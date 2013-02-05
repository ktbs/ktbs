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

"""I provide functionalities to serialize RDF-REST resource.

I act as a registry of serializers. Serializers can be
`iterated by decreasing preference <iter_serializers>`func:, selected based on
`content-type <get_serializer_by_content_type>`:func: or
`extension <get_serializer_by_extension>`:func:, and dedicated serializers can
be registered for a given RDF type.

I provide a number of default serializers, but additional serializers can be
`added in the registry<register_serializer>`:func:.

Finally, a numer of default `namespace prefixes <bind_prefix>`:func` can be set.
They will be shared with all registered serializers (but some third-party
serializers may not honnor them).
"""
from rdflib import Graph, Literal, RDF, RDFS, URIRef
from rdflib.plugins.serializers.nt import _nt_row

from .exceptions import SerializeError
from .parsers import _FormatRegistry
from .utils import coerce_to_uri, wrap_exceptions

################################################################
#
# Serializer registration
#

_SREGISRIES = { None: _FormatRegistry() }
_NAMESPACES = {
    "rdf":     unicode(RDF),
    "rdfs":    unicode(RDFS),
    }

def register_serializer(content_type, extension=None, preference=80,
                        rdf_type=None):
    """I return a decorator for registering a serializer.
    
    The decorated function must have the same prototype as
    :func:`serialize_rdf_xml`.
    
    :param content_type: a content-type as a str
    :param extension:    the file extension associated with this serializer
    :param preference:   an int between 0 (low) and 100 (high)
    :param rdf_type:     if provided, the RDF type to which this serializer
                         applies

    The decorated function must have the same prototype as
    :func:`serialize_rdf_xml`, and should raise `~.exceptions.SerializeError`
    when it fails to serialize the given graph.
    """
    if rdf_type is not None:
        rdf_type = unicode(rdf_type)
    registry = _SREGISRIES.get(rdf_type)
    if registry is None:
        registry = _FormatRegistry()
        _SREGISRIES[rdf_type] = registry

    def decorator(func):
        """The decorator to register a serializer."""
        registry.register(func, content_type, extension, preference)
        return func
    return decorator

def iter_serializers(rdf_type=None):
    """Iter over all the serializers available for this rdf_type.

    :return: an iterator of tuples (serializer_function, contenttype, extension)

    Serializers are iterated in decreasing order of preference. Note that,
    if `rdf_type` is provided, a serializer associated with this type will
    always be preferred over a generic serializer (*i.e.* associated with no
    type), regardless of the preference score.
    """
    if rdf_type is not None:
        rdf_type = unicode(rdf_type)
        reg = _SREGISRIES.get(rdf_type)
        if reg:
            for i in reg:
                yield i
    for i in _SREGISRIES[None]:
        yield i

def get_serializer_by_content_type(content_type, rdf_type=None):
    """I return the best serializer associated with content_type, or None.

    :return: a tuple (serializer_function, extension) or (None, None)
    """
    if rdf_type is not None:
        rdf_type = unicode(rdf_type)
        reg = _SREGISRIES.get(rdf_type)
        if reg:
            ret = reg.get_by_content_type(content_type)
            if ret[0] is not None:
                return ret
    return _SREGISRIES[None].get_by_content_type(content_type)

def get_serializer_by_extension(extension, rdf_type=None):
    """Return the serializer associated with the best preference score.

    :return: a tuple (serializer_function, content_type) or (None, None)
    """
    if rdf_type is not None:
        rdf_type = unicode(rdf_type)
        reg = _SREGISRIES.get(rdf_type)
        if reg:
            ret = reg.get_by_extension(extension)
            if ret[0] is not None:
                return ret
    return _SREGISRIES[None].get_by_extension(extension)

def bind_prefix(prefix, namespace_uri):
    """I associate a namespace with a prefix for all registered serializers.
    """
    _NAMESPACES[prefix] = unicode(namespace_uri)

def get_prefix_bindings():
    """I return a fresh dict containing all the prefix bindings.

    :see also: :func:`bind_prefix`
    """
    return dict(_NAMESPACES)


################################################################
#
# Default serializer implementations
#

@register_serializer("application/rdf+xml", "rdf", 60)
@register_serializer("application/xml",     "xml", 20)
def serialize_rdf_xml(graph, resource, bindings=None):
    """I serialize an RDF graph as RDF/XML.

    :param graph:    the `~rdflib.Graph`:class: to serialize
    :param resource: the resource described by `graph` (its URI will used as
                     base URI)
    :param binding: a dict containing system-wide prefix bindings (defaults to
                    `get_prefix_bindings`:func:())

    :return: an iterable of UTF-8 encoded byte strings
    :raise: :class:`.exceptions.SerializeError` if the serializer can
            not serialize the given graph.

    .. important::

        Serializers that may raise a
        :class:`~rdfrest.exceptions.SerializeError` must *not* be implemented
        as generators, or the exception will be raised too late (i.e. when the
        `HttpFrontend` tries to send the response.
    """
    if False: # TODO LATER actually perform some checking
        raise SerializeError("RDF/XML can not encode this graph")
    bindings = bindings or dict(_NAMESPACES)
    return _serialize_with_rdflib("xml", graph, bindings, resource.uri)

@register_serializer("text/turtle",          "ttl")
@register_serializer("text/n3",              "n3",  20)
@register_serializer("text/x-turtle",        None,   20)
@register_serializer("application/turtle",   None,   20)
@register_serializer("application/x-turtle", None,   20)
def serialize_turtle(graph, uri, bindings=None):
    """I serialize an RDF graph as Turtle.

    See `serialize_rdf_xml` for prototype documentation.
    """
    bindings = bindings or dict(_NAMESPACES)
    return _serialize_with_rdflib("n3", graph, bindings, uri)

@wrap_exceptions(SerializeError)
def _serialize_with_rdflib(rdflib_format, graph, bindings, base_uri):
    "Common implementation of all rdflib-based serialize functions."
    assert isinstance(rdflib_format, str)
    assert isinstance(graph, Graph)
    # copy in another graph to prevent polluting the original graph namespaces
    # TODO LATER find an efficient way to serialize a graph with custom NSs
    ser = Graph()
    ser_add = ser.add
    for triple in graph:
        ser_add(triple)
    for prefix, nsuri in bindings.items():
        ser.bind(prefix, nsuri)
    if base_uri is not None and not isinstance(base_uri, URIRef):
        base_uri = coerce_to_uri(base_uri)
    # We return an iterable rather than implementing this as a generator,
    # so that exceptions would be raised above are raised immediately 
    return [ser.serialize(None, format=rdflib_format, base=base_uri)]

@register_serializer("text/nt",    "nt",  40)
@register_serializer("text/plain", "txt", 20)
@wrap_exceptions(SerializeError)
def serialize_ntriples(graph, uri, bindings=None):
    """I serialize an RDF graph as N-Triples.

    See `serialize_rdf_xml` for prototype documentation.
    """
    # 'binding' and 'uri' not used #pylint: disable=W0613
    # NB: we N-Triples needs no base_uri or namespace management.
    # Also, we re-implement our own NT serializer in order to yield each triple
    # individually; this allows WSGI host to send chuncked content.

    return ( _nt_row(triple).encode("ascii", "replace") for triple in graph )

    # We use an iterator expansion rather than a generator, to ensure that
    # exceptions are raised immediately

@register_serializer("text/html", "html", 60)
@wrap_exceptions(SerializeError)
def serialize_htmlized_turtle(graph, resource, bindings=None):
    """I serialize graph in a HTMLized simple turtle form.
    """
    #pylint: disable=R0914
    #    too many local variables
    uri = resource.uri
    bindings = bindings or dict(_NAMESPACES)
    ret = "<h1># "
    crumbs = uri.split("/")
    crumbs[:3] = [ "/".join(crumbs[:3]) ]
    for i in xrange(len(crumbs)-1):
        link = "/".join(crumbs[:i+1]) + "/"
        ret += u'<a href="%s">%s</a>' % (link, crumbs[i] + "/",)
    ret += u'<a href="%s">%s</a></h1>\n' % (uri, crumbs[-1])

    ret += "<div class='formats'>#\n"
    rdf_types = list(graph.objects(uri, RDF.type)) + [None]
    ctypes = {}
    for typ in rdf_types:
        for _, ctype, ext in iter_serializers(typ):
            if ext is not None  and  ctype not in ctypes:
                ctypes[ctype] = ext
                ret += u'<a href="%s.%s">%s</a>\n' % (uri, ext, ext)
    ret += "</div>\n"

    ret += '<div class="prefixes">\n'
    ret += u"<div>@base &lt;%s&gt; .</div>\n" % uri
    for prefix, nsuri in bindings.items():
        ret += u"<div>@prefix %s: &lt;%s&gt; .</div>\n" % (prefix, nsuri)
    ret += "</div>\n"

    query = "SELECT ?s ?p ?o WHERE {?s ?p ?o} ORDER BY ?s ?p ?o"
    old_subj = None
    old_pred = None
    for subj, pred, obj in graph.query(query):
        if subj != old_subj:
            if old_subj is not None:
                ret += ".</div></div></div>\n"
            ret += u'<div class="subj">%s\n' \
                   % _htmlize_node(bindings, subj, uri)
            old_subj = subj
            old_pred = None
        if pred != old_pred:
            if old_pred is not None:
                ret += ";</div></div>\n"
            ret += u'\t<div class="pred">%s\n' \
                   % _htmlize_node(bindings, pred, uri)
            old_pred = pred
        else:
            ret += ",</div>\n"
        ret += u'\t\t<div class="obj">%s\n' \
               % _htmlize_node(bindings, obj, uri)
    ret += ".</div></div></div>\n"

    page = u"""<html>
    <head>
    <title>%(uri)s</title>
    <style text="text/css">%(style)s</style>
    <script text="text/javascript">%(script)s</script>
    </head>
    <body onload="rdfrest_init_editor()">
    %(body)s
    %(footer)s
    </body>\n</html>""" % {
        "uri": uri,
        "style": _HTML_STYLE,
        "script": _HTML_SCRIPT(ctypes),
        "body": ret,
        "footer": _HTML_FOOTER(ctypes),
    }

    return [page.encode("utf-8")]


def _htmlize_node(bindings, node, base):
    """
    Generate simple HTML output for the given node.

    :param uri:  a Node, unicode or ascii str
    :param base: a unicode or ascii str

    :rtype: unicode
    """
    #pylint: disable=R0911

    if isinstance(node, URIRef):
        curie = _make_curie(bindings, node, base)
        if curie[0] == "&": # full URI
            return u"""<a href="%s">%s</a>""" % (
                node,
                _make_curie(bindings, node, base),
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
            quoted = u'"""%s"""' % value
        else:
            quoted = u'"%s"' % value

        if datatype:
            if str(datatype) == "http://www.w3.org/2001/XMLSchema#integer":
                return unicode(node) # do not quote integers
            else:
                return u'%s^^%s' % (
                    quoted, _htmlize_node(bindings, datatype, base),
                )
        elif node.language:
            return u'%s@"%s"' % (quoted, node.language)
        else:
            return quoted
    else:
        return u"_:%s" % node

def _make_curie(bindings, uri, base):
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

_HTML_STYLE = """
    a { text-decoration: none; }
    .formats { font-size: 80%; font-style: italic; }
    .prefixes { font-size: 66%; float: right; }
    .prefix { display: none; }
    .subj { margin-top: 2ex; }
    .pred { margin-left: 2em ; }
    .obj  { margin-left: .5em ; display: inline; }
    #debug { font-size: 66%; color: blue }
    """

def _HTML_SCRIPT(ctypes):
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

    document.getElementById("toggle").onclick = toggle_editor;
    document.getElementById("ctype").value = "text/turtle";
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

def _HTML_FOOTER(ctypes):
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
       
