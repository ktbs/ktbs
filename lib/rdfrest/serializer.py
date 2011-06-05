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
I provide functionality to select the best serialization syntax in
response to a HTTP query, and serialize an RDF graph accordingly.

I also provide an extension mechanism for adding syntaxes.
"""

from bisect import insort
from rdflib import Graph, Literal, RDF, RDFS, URIRef
from .namespaces import RDFREST

_BY_PRIORITY = []
_BY_EXTENSION = {}
_BY_MIMETYPE = {}
_NAMESPACES = [
    ("rdf", unicode(RDF)),
    ("rdfs", unicode(RDFS)),
    ("rdfrest", RDFREST),
    ]

def register_namespace(prefix, uri):
    """
    Add a standard namespace prefix.
    """
    _NAMESPACES.append((prefix, uri))

def register(mimetype, extension, priority=50, callble=None):
    """
    Register a serializer. Can also be used as a decorator (see below).

    * mimetype: a mimetype as a str
    * etension: a file extension as a str
    * priority: an integer between 00 and 99 included
    * callble: a generator yielding the serialization

    See `generate_ttl` for the expected interface of ``callble``.

    If the last parameter is omitted, this function acts as a decorator,
    registering the decorated callable.
    """
    def decorator(decorated):
        "register the decorated function as a serializer"
        insort(_BY_PRIORITY, (-priority, mimetype))
        _BY_EXTENSION[extension] = (mimetype, decorated)
        _BY_MIMETYPE[mimetype] = (extension, decorated)
        return decorated

    if callble is None:
        return decorator
    else:
        decorator(callble)

def serialize(graph, request, extension=None):
    """
    Serialize graph according to the HTTP request.

    Return a tuple containing a generator, the content type and the extension,
    or None,None,None if no acceptable serializer can be found.

    Note that the extension, if provided, overrides the HTTP Accept header.
    """
    uri = request.resource_uri
    nsp = list(_NAMESPACES)

    if extension is not None:
        pair = _BY_EXTENSION.get(extension)
        if pair is None:
            return None, None, None
        else:
            mimetype, callble = pair
            return callble(nsp, graph, uri), mimetype, extension
    else:
        ordered_mimetypes = [ pair[1] for pair in _BY_PRIORITY ]
        best_mimetype = request.accept.best_match(ordered_mimetypes)
        if best_mimetype is None:
            return None, None, None
        else:
            extension, callble = _BY_MIMETYPE[best_mimetype]
            return callble(nsp, graph, uri), best_mimetype, extension

def serialize_version_list(uri, request):
    """
    Generate a list of available version for the given URI; return an
    iterable of str and a mimetype.

    We assume that the URI resoves to an RDF graph. This is used to
    generate the body of a 406 Not Acceptable error. The best mimetype
    should be guessed in env.
    """
    #pylint: disable=R0201,W0613

    # TODO MINOR implement proper "406 Not Acceptable" message
    return ["Not Acceptable"], "text/html"

@register("text/html", "html", 01)
def generate_htmlized_turtle(namespaces, graph, uri):
    """
    I serialize graph in a HTMLized simple turtle form.

    NB: this generator is associated with the lowest possible priority,
    so that it can be overriden by other serializers.
    """
    #pylint: disable=R0914
    #    too many local variables

    ret = (u"<html>\n"
    "<head>\n"
    "<title>%(uri)s</title>\n"
    """<style text="text/css">
    a { text-decoration: none; }
    .prefixes { font-size: 50%%; float: right; }
    .prefix { display: none; }
    .subj { margin-top: 2ex; }
    .pred { margin-left: 2em ; }
    .obj  { margin-left: .5em ; display: inline; }
    </style>"""
    "</head>\n"
    "<body>\n"
    ) % locals()

    ret += "<h1># "
    crumbs = uri.split("/")
    crumbs[:3] = [ "/".join(crumbs[:3]) ]
    for i in xrange(len(crumbs)-1):
        link = "/".join(crumbs[:i+1]) + "/"
        ret += u'<a href="%s">%s</a>' % (link, crumbs[i] + "/",)
    ret += u'<a href="%s">%s</a></h1>\n' % (uri, crumbs[-1])

    ret += "<div>#\n"
    for ext in _BY_EXTENSION:
        ret += u'<a href="%s.%s">%s</a>\n' % (uri, ext, ext)
    ret += "</div>\n"

    ret += '<div class="prefixes">\n'
    ret += u"<div>@base &lt;%s&gt; .</div>\n" % uri
    for prefix, nsuri in namespaces:
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
                   % _htmlize_node(namespaces, subj, uri)
            old_subj = subj
            old_pred = None
        if pred != old_pred:
            if old_pred is not None:
                ret += ";</div></div>\n"
            ret += u'\t<div class="pred">%s\n' \
                   % _htmlize_node(namespaces, pred, uri)
            old_pred = pred
        else:
            ret += ",</div>\n"
        ret += u'\t\t<div class="obj">%s\n' \
               % _htmlize_node(namespaces, obj, uri)
    ret += ".</div></div></div>\n"
    ret += "</body>\n</html>\n"
    yield ret.encode("utf-8")

@register("text/turtle", "ttl", 60)
@register("text/n3",     "n3",  40)
def generate_ttl(namespaces, graph, uri):
    """
    I serialize graph in turtle.
    """
    return _generate_with_rdflib("turtle", namespaces, graph, uri)

@register("text/nt", "nt", 40)
def generate_nt(namespaces, graph, uri):
    """
    I serialize graph in N-Triple.
    """
    return _generate_with_rdflib("nt", namespaces, graph, uri)

@register("application/rdf+xml", "rdf", 40)
def generate_rdf(namespaces, graph, uri):
    """
    I serialize graph in turtle.
    """
    return _generate_with_rdflib("pretty-xml", namespaces, graph, uri)

def _generate_with_rdflib(rdf_format, namespaces, graph, uri):
    """
    I implement the generic behaviour for using rdflib serializers.
    """
    # copy in another graph to prevent polluting the original graph namespaces
    # TODO MINOR is there no better way of doing that??
    ser = Graph()
    ser_add = ser.add
    for triple in graph:
        ser_add(triple)
    for prefix, nsuri in namespaces:
        ser.bind(prefix, nsuri)
    yield ser.serialize(None, rdf_format, uri)

def _htmlize_node(namespaces, node, base):
    """
    Generate simple HTML output for the given node.

    Parameters:
      uri: a Node, unicode or ascii str
      base: a unicode or ascii str

    Return:
      a unicode
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
    for prefix, nsuri in namespaces:
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
