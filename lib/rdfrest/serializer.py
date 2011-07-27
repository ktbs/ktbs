#    This file is part of RDF-REST <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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

"""
I provide functionalities to register a number of serializers with
preference levels, associated content-types and file extensions. A
register also keeps track of preferred namespace prefixes.

There is a default register from which any specific register inherits.
"""

from bisect import insort
from rdflib import Graph, Literal, RDF, RDFS, URIRef
from rdfrest.namespaces import RDFREST

from rdfrest.exceptions import SerializeError

class SerializerRegister(object):
    """I provide functionalities for registering serializers.
    """

    __default = None

    @classmethod
    def get_default(cls):
        """I retun the default serializer register.
        """
        if SerializerRegister.__default is None:
            SerializerRegister.__default = SerializerRegister()
        return SerializerRegister.__default

    def __init__(self):
        default = SerializerRegister.__default
        if default is None: # self will become default
            self._by_pref = []
            self._by_ctype = {}
            self._by_ext = {}
            self._namespaces = {
                "rdf":     unicode(RDF),
                "rdfs":    unicode(RDFS),
                "rdfrest": RDFREST,
                }
        else:
            # access to protected members:
            self._by_pref = list(default._by_pref)       #pylint: disable=W0212
            self._by_ctype = dict(default._by_ctype)     #pylint: disable=W0212
            self._by_ext = dict(default._by_ext)         #pylint: disable=W0212
            self._namespaces = dict(default._namespaces) #pylint: disable=W0212

    def register(self, content_type, extension=None, preference=80):
        """I return a decorator for registering a serializer.

        The decorated function must have the same prototype as
        :func:`serialize_rdf_xml`.

        :param content_type: a content-type as a str
        :param extension:    the file extension associated with this serializer
        :param preference:   an int between 0 (low) and 100 (high)
        """
        assert 0 <= preference <= 100
        assert content_type not in self._by_ctype, \
            "%s serializer registered twice" % content_type
        assert extension not in self._by_ext, \
            "%s serializer registered twice" % extension
        def the_decorator(func):
            "Register `func` as a serializer"
            insort(self._by_pref,
                   (100-preference, func, content_type, extension))
            self._by_ctype[content_type] = (func, extension)
            self._by_ext[extension] = (func, content_type)
            return func
        return the_decorator

    def __iter__(self):
        """Iter over registered serializers in order of decreasing preference.

        :return: an iterator of tuples (function, content_type, extension)
        """
        return ( i[1:] for i in self._by_pref )

    def get_by_content_type(self, content_type):
        """I return the serializer associated with content_type, or None.

        :return: a tuple (function, extension)
        """
        return self._by_ctype.get(content_type)

    def get_by_extension(self, extension):
        """I return the serializer associated with extension, or None.

        :return: a tuple (function, content_type)
        """
        return self._by_ext.get(extension)

    @property
    def namespaces(self):
        """A fresh dict representing the registered namespace prefixes.
        """
        return dict(self._namespaces)

    def bind_prefix(self, prefix, namespace_uri):
        """Add a namespace prefix.

        `prefix` must not be already bound in :attr:`namespaces`.
        """
        assert prefix not in self._namespaces
        self._namespaces[prefix] = str(namespace_uri)


def register(content_type, extension=None, preference=80):
    """:meth:`~SerializerRegister.register Register` a serializer in
    the default register.
    """
    return SerializerRegister.get_default().register(content_type, extension,
                                                     preference)

def bind_prefix(prefix, namespace_uri):
    """:meth:`~SerializerRegister.bind_prefix Bind` a namespace prefix
    in the default register.
    """
    return SerializerRegister.get_default().bind_prefix(prefix, namespace_uri)

@register("application/rdf+xml", "rdf", 60)
@register("application/xml",     "xml", 20)
def serialize_rdf_xml(graph, sregister, base_uri=None):
    """I serialize an RDF graph as RDF/XML.

    :param graph:     an RDF graph
    :type  graph:     rdflib.Graph
    :param sregister: the serializer register this serializer comes from
                      (useful for getting namespace prefixes and other info)
    :type  sregister: SerializerRegister
    :param base_uri:  the base URI to be used to serialize

    :return: an iterable of UTF-8 encoded byte strings
    :raise: :class:`~rdfrest.exceptions.SerializeError` if the serializer can
            not serialize this given graph.

    .. important::

        Serializers that may raise a
        :class:`~rdfrest.exceptions.SerializeError` must *not* be implemented
        as generators, or the exception will be raised too late (i.e. when the
        `HttpFrontend` tries to send the response.
    """
    if False: # TODO MINOR actually perform some checking
        raise SerializeError("RDF/XML can not encode this graph")
    return _serialize_with_rdflib("xml", sregister, graph, base_uri)

@register("text/turtle",          "ttl")
@register("text/n3",              "n3",  20)
@register("text/x-turtle",        None,   20)
@register("application/turtle",   None,   20)
@register("application/x-turtle", None,   20)
def serialize_turtle(graph, sregister, base_uri=None):
    """I serialize an RDF graph as Turtle.

    See `serialize_rdf_xml` for prototype documentation.
    """
    return _serialize_with_rdflib("n3", sregister, graph, base_uri)

def _serialize_with_rdflib(rdflib_format, sregister, graph, base_uri):
    "Common implementation of all rdflib-based serialize functions."
    assert isinstance(rdflib_format, str)
    assert isinstance(sregister, SerializerRegister)
    assert isinstance(graph, Graph)
    assert isinstance(base_uri, URIRef)
    # copy in another graph to prevent polluting the original graph namespaces
    # TODO MINOR is there no better way of doing that??
    ser = Graph()
    ser_add = ser.add
    for triple in graph:
        ser_add(triple)
    for prefix, nsuri in sregister.namespaces.items():
        ser.bind(prefix, nsuri)
    yield ser.serialize(None, format=rdflib_format, base=base_uri)

@register("text/nt",    "nt",  40)
@register("text/plain", "txt", 20)
def serialize_ntriples(graph,  _sregister, _base_uri=None):
    """I serialize an RDF graph as N-Triples.

    See `serialize_rdf_xml` for prototype documentation.
    """
    # NB: we do not use _serialize_with_rdflib here, as N-Triples needs to
    # base_uri or namespace management.
    yield graph.serialize(format="nt")
    # TODO MAJOR this could be optimized by yielding one triple after another
    # for big graphs, this would allow HttpFrontend to send chunked content


@register("text/html", "html", 60)
def serialize_htmlized_turtle(graph, sregister, base_uri):
    """I serialize graph in a HTMLized simple turtle form.
    """
    #pylint: disable=R0914
    #    too many local variables

    namespaces = sregister.namespaces

    ret = "<h1># "
    crumbs = base_uri.split("/")
    crumbs[:3] = [ "/".join(crumbs[:3]) ]
    for i in xrange(len(crumbs)-1):
        link = "/".join(crumbs[:i+1]) + "/"
        ret += u'<a href="%s">%s</a>' % (link, crumbs[i] + "/",)
    ret += u'<a href="%s">%s</a></h1>\n' % (base_uri, crumbs[-1])

    ret += "<div>#\n"
    for _, _, ext in sregister:
        if ext is not None:
            ret += u'<a href="%s.%s">%s</a>\n' % (base_uri, ext, ext)
    ret += "</div>\n"

    ret += '<div class="prefixes">\n'
    ret += u"<div>@base &lt;%s&gt; .</div>\n" % base_uri
    for prefix, nsuri in namespaces.items():
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
                   % _htmlize_node(namespaces, subj, base_uri)
            old_subj = subj
            old_pred = None
        if pred != old_pred:
            if old_pred is not None:
                ret += ";</div></div>\n"
            ret += u'\t<div class="pred">%s\n' \
                   % _htmlize_node(namespaces, pred, base_uri)
            old_pred = pred
        else:
            ret += ",</div>\n"
        ret += u'\t\t<div class="obj">%s\n' \
               % _htmlize_node(namespaces, obj, base_uri)
    ret += ".</div></div></div>\n"

    page = u"""<html>
    <head>
    <title>%(base_uri)s</title>
    <style text="text/css">%(style)s</style>
    <script text="text/javascript">%(script)s</script>
    </head>
    <body onload="init_page()">
    %(body)s
    %(footer)s
    </body>\n</html>""" % {
        "base_uri": base_uri,
        "style": _HTML_STYLE,
        "script": _HTML_SCRIPT,
        "body": ret,
        "footer": _HTML_FOOTER,
    }

    yield page.encode("utf-8")


def _htmlize_node(namespaces, node, base):
    """
    Generate simple HTML output for the given node.

    :param uri:  a Node, unicode or ascii str
    :param base: a unicode or ascii str

    :rtype: unicode
    """
    #pylint: disable=R0911

    if isinstance(node, URIRef):
        curie = _make_curie(namespaces, node, base)
        if curie[0] == "&": # full URI
            return u"""<a href="%s">%s</a>""" % (
                node,
                _make_curie(namespaces, node, base),
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
        if '"' in node or '\n' in node:
            quoted = u'"""%s"""' % node
        else:
            quoted = u'"%s"' % node

        if datatype:
            if str(datatype) == "http://www.w3.org/2001/XMLSchema#integer":
                return unicode(node) # do not quote integers
            else:
                return u'%s^^%s' % (
                    quoted, _htmlize_node(namespaces, datatype, base),
                )
        elif node.language:
            return u'%s@"%s"' % (quoted, node.language)
        else:
            return quoted
    else:
        return u"_:%s" % node

def _make_curie(namespaces, uri, base):
    """
    Convert the given URI to a CURIE if possible.

    Parameters:
      uri: a Node, unicode or ascii str
      base: a unicode or ascii str

    Return:
      a unicode
    """
    for prefix, nsuri in namespaces.items():
        if uri.startswith(nsuri) and str(uri) != str(nsuri):
            return u"%s:%s" % (prefix, uri[len(nsuri):])

    # TODO MINOR improve this (this is an ugly way of relativizing a URI)
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
    .prefixes { font-size: 66%%; float: right; }
    .prefix { display: none; }
    .subj { margin-top: 2ex; }
    .pred { margin-left: 2em ; }
    .obj  { margin-left: .5em ; display: inline; }
    #debug { font-size: 66%%; color: blue }
    """

_HTML_SCRIPT = r"""

    metadata = {};

    function init_page() {
        if (document.referrer == document.location.href ||
            document.referrer == document.title) {
            // heuristic to detect we arrived here from the editor
            // then automatically re-open the editor
            toggle_editor();
        }
    }

    function toggle_editor() {
        var editor = document.getElementById("editor");
        var edit_button = document.getElementById("toggle");
        if (edit_button.value == "hide editor") {
            editor.hidden = true;
            edit_button.value = "show editor";
        } else {
            editor.hidden = false;
            if (edit_button.value == "edit") { // first time
                reload_editor();
            }
            edit_button.value = "hide editor";
        }
    }

    function error_message(textarea, msg) {
        textarea.disabled = 1;
        textarea.value = msg;
        document.getElementById("save").disabled = false;
    }

    function reload_editor() {
        var textarea = document.getElementById("textarea");
        var ctype = document.getElementById("ctype");
        var debug = document.getElementById("debug");
        var req = make_req();
        try {
            req.open("GET", document.title, true);
            req.setRequestHeader("Accept", ctype.value);
            req.setRequestHeader("If-None-Match", "\"(force-reload)\"");
        }
        catch(err) {
            error_message(textarea, "error while preparing request: " + err);
            return;
        }
        req.onreadystatechange= function () {
            if (req.readyState == 4) {
                if (req.status == 200) {
                    textarea.value = req.responseText;
                    ctype.value    = req.getResponseHeader("Content-Type");
                    metadata.etag  = req.getResponseHeader("Etag");
                    debug.textContent = "etag: " + metadata.etag;
                    document.getElementById("save").disabled = false;
                    textarea.disabled = false;
                } else {
                    error_message(textarea,
                                  "error while loading: " + req.status +
                                  "\n" + req.responseText);
                }
            } else {
                textarea.value = textarea.value + ".";
            }
        };
        textarea.value = "loading..";
        req.send();
    };

    function save_editor() {
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
            error_message(textarea, "error while preparing request: " + err);
            return;
        }
        req.onreadystatechange= function () {
            if (req.readyState == 4) {
                if (req.status == 200) {
                    textarea.value = req.responseText;
                    ctype.value = req.getResponseHeader("Content-Type");
                    metadata.etag   = req.getResponseHeader("Etag");
                    debug.textContent = "etag: " + metadata.etag;
                    window.location.assign(document.title+".html");                    
                } else {
                    error_message(textarea,
                                  "error while saving: " + req.status +
                                  "\n" + req.responseText);
                }
            } else {
                textarea.value = textarea.value + ".";
            }
        };
        var payload = textarea.value;
        textarea.value = "loading..";
        req.send(payload);
    };

    function post_editor() {
        var textarea = document.getElementById("textarea");
        var ctype = document.getElementById("ctype");
        var req = make_req();
        try {
            req.open("POST", document.title, true);
            req.setRequestHeader("Content-Type", ctype.value);
        }
        catch(err) {
            error_message(textarea, "error while preparing request: " + err);
            return;
        }
        req.onreadystatechange= function () {
            if (req.readyState == 4) {
                if (req.status == 201) {
                    var location = req.getResponseHeader("Location");
                    window.location.assign(location)
                } else {
                    error_message(textarea,
                                  "error while posting: " + req.status +
                                  "\n" + req.responseText);
                }
            } else {
                textarea.value = textarea.value + ".";
            }
        };
        var payload = textarea.value;
        textarea.value = "loading..";
        req.send(payload);
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
    """

_HTML_FOOTER = """<br /><br /><hr />
    <input type="button" value="edit"
           id="toggle" onclick="toggle_editor()" />
    <div id="editor" hidden="">
      <textarea id="textarea" cols="80" rows="16"></textarea>
      <br />
      <input type="button" value="save" disabled=""
             id="save" onclick="save_editor()" />
      <input type="button" value="reload"
             id="reload" onclick="reload_editor()" />
      <input type="button" value="post new object"
             id="post" onclick="post_editor()" />
      <input id="ctype" value="*/*" />
      <div id="debug" style="text-color: blue" hidden=""></div>
    </div>
    """
       
