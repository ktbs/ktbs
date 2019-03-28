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

"""
I ensure compatibility with older versions of python and other dependencies.

I am automatically loaded when importing `rdfrest`:mod:.
"""
#pylint: disable=W0622
#    redefining built-in #pylint: disable=W0622

import sys
assert sys.version_info[0] == 3

import logging
LOG = logging.getLogger(__name__)


def monkeypatch_prepare_query():
    """
    ensures that rdflib.plugins.sparql.processor is uptodate, else monkeypatch it.
    """
    # pylint: disable=invalid-name
    import rdflib.plugins.sparql.processor as sparql_processor
    _TEST_PREPARED_QUERY = sparql_processor.prepareQuery("ASK { ?s ?p ?o }")
    if not hasattr(_TEST_PREPARED_QUERY, "_original_args"):
        # monkey-patch 'prepare'
        original_prepareQuery = sparql_processor.prepareQuery
        def monkeypatched_prepareQuery(queryString, initNS=None, base=None):
            """
            A monkey-patched version of the original prepareQuery,
            adding an attribute '_original_args' to the result.
            """
            if initNS is None:
                initNS = {}
            ret = original_prepareQuery(queryString, initNS, base)
            ret._original_args = (queryString, initNS, base)
            return ret
        sparql_processor.prepareQuery = monkeypatched_prepareQuery
        LOG.info("monkey-patched rdflib.plugins.sparql.processor.prepareQuery")
monkeypatch_prepare_query()
del monkeypatch_prepare_query

def monkeypatch_union():
    """
    In rdflib 4.2.2, the SPARQL implementation prevents UNION from returning duplicates.
    This is extremely costly, and not required by the spec.
    This patch simplifies the handling of SPARQL UNION and makes it compliant *and* faster.
    """
    import rdflib
    if rdflib.__version__ != "4.2.2":
        return

    from rdflib.plugins.sparql import evaluate

    def patchedEvalUnion(ctx, union):
        for x in evaluate.evalPart(ctx, union.p1):
            yield x
        for x in evaluate.evalPart(ctx, union.p2):
            yield x
    evaluate.evalUnion = patchedEvalUnion

monkeypatch_union()
del monkeypatch_union
