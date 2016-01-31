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
assert sys.version_info[0] == 2 and sys.version_info[1] >= 5

import logging
LOG = logging.getLogger(__name__)

if sys.version_info[1] < 6:

    # next builtin

    def next(iterable, default=None):
        "Emulating python2.6 buitin next"
        try:
            return iterable.next()
        except StopIteration:
            return default

    __builtins__["next"] = next


    # Popen.terminate method
    if sys.platform == "w32":
        from win32process import TerminateProcess #pylint: disable=F0401

        def terminate(self):
            "Emulating python2.6 terminate method"
            #pylint: disable=W0212
            #    access to a protected member
            TerminateProcess(self._handle, 1)
    else:
        from os import kill
        from signal import SIGTERM

        def terminate(self):
            "Emulating python2.6 terminate method"
            kill(self.pid, SIGTERM)

    from subprocess import Popen
    Popen.terminate = terminate.__get__(None, Popen) #pylint: disable=E1101


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
