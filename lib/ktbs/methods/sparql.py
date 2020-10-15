#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    KTBS is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    KTBS is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with KTBS.  If not, see <http://www.gnu.org/licenses/>.

"""
Implementation of the sparql builtin methods.
"""
import traceback

from pyparsing import ParseException
from rdfrest.exceptions import ParseError
from rdfrest.util import Diagnosis
from rdflib import BNode, Literal, URIRef
from rdflib.graph import ConjunctiveGraph
import rdflib.plugins.sparql.algebra

from rdfrest.util.prefix_conjunctive_view import PrefixConjunctiveView
from .interface import IMethod
from .utils import replace_obsels
from ..namespace import KTBS
from ..engine.builtin_method import register_builtin_method_impl

import logging

LOG = logging.getLogger(__name__)

class _SparqlMethod(IMethod):
    """I implement the sparql builtin method.
    """
    uri = KTBS.sparql

    def compute_trace_description(self, computed_trace):
        """I implement :meth:`.interface.IMethod.compute_trace_description`.
        """
        diag = Diagnosis("sparql.compute_trace_description")

        src, params =  self._prepare_source_and_params(computed_trace, diag)
        if src is not None:
            if params.get('scope') == 'store':
                config = computed_trace.service.config
                if not config.has_section('sparql') \
                or not config.has_option('sparql', 'allow-scope-ktbs') \
                or not config.getboolean('sparql', 'allow-scope-ktbs'):
                    diag.append("Scope 'ktbs' must be explicitly allowed in config, "
                                "as it raises privacy issued.")
            assert params is not None
            model = params.get("model")
            if model is None:
                model = src.model_uri
            else:
                model = URIRef(model)
            origin = Literal(params.get("origin")  or  src.origin)
            with computed_trace.edit(_trust=True) as editable:
                editable.add((computed_trace.uri, KTBS.hasModel, model))
                editable.add((computed_trace.uri, KTBS.hasOrigin, origin))

        return diag

    def compute_obsels(self, computed_trace, from_scratch=False):
        """I implement :meth:`.interface.IMethod.compute_obsels`.
        """
        diag = Diagnosis("sparql.compute_obsels")

        source = computed_trace.source_traces[0]
        parameters = computed_trace.parameters_as_dict
        parameters["__destination__"] = computed_trace.uri
        parameters["__source__"] = source.uri

        scope = parameters.get('scope', 'trace')
        try:
            if scope == 'store':
                data = ConjunctiveGraph(source.service.store)
            elif scope == 'base':
                data = PrefixConjunctiveView(source.base.uri,
                                             source.service.store)
            else:
                # scope == 'trace'
                data = source.obsel_collection.get_state({"refresh":"no"})
            sparql = parameters["sparql"] % parameters
            result = data.query(sparql, base=source.obsel_collection.uri).graph
            replace_obsels(computed_trace, result, ("inherit" in parameters))
        except Exception as exc:
            LOG.warning(traceback.format_exc())
            diag.append(str(exc))

        return diag

    @staticmethod
    def _prepare_source_and_params(computed_trace, diag):
        """I check and prepare the data required by the method.

        I return the unique source of the computed trace, and a dict of
        useful parameters converted to the expected datatype. If this can not
        be done, I return ``(None, None)``.

        I also populate `diag` with error/warning messages.
        """
        sources = computed_trace.source_traces
        params = computed_trace.parameters_as_dict
        critical = False

        if len(sources) != 1:
            diag.append("Method ktbs:sparql expects exactly one source")
            critical = True

        if "sparql" not in params:
            diag.append("Method ktbs:sparql requires parameter sparql")
            critical = True
        sparql = params.get("sparql", "")

        for key, val in params.items():
            datatype = _PARAMETERS_TYPE.get(key)
            if datatype is None:
                if ("%%(%s)s" % key) not in sparql:
                    diag.append("WARN: Parameter %s is not used by "
                                "ktbs:sparql nor by the SPARQL query"
                                % key)
            else:
                try:
                    params[key] = datatype(val)
                except ValueError:
                    LOG.info(traceback.format_exc())
                    diag.append("Parameter %s has illegal value: %s"
                                % (key, val))
                    critical = True
                except ParseError:
                    LOG.info(traceback.format_exc())
                    diag.append("Parameter %s has illegal value: %s"
                                % (key, val))
                    critical = True

        if critical:
            return None, None
        else:
            return sources[0], params

def _scope_datatype(value):
    if value in {'trace', 'base', 'store'}:
        return value
    raise ValueError(value)

_PARAMETERS_TYPE = {
    "origin": Literal,
    "model": URIRef,
    "sparql": str,
    "inherit": str,
    "scope": _scope_datatype,
}

# monkeypatch to fix issue #381 in rdflib.plugins.sparql
from rdflib.plugins.sparql import parser as sparql_parser
original_expandTriples = sparql_parser.expandTriples
def clean_terms(terms):
    for i, t in enumerate(terms):
        if t == ';':
            if i == len(terms)-1 or terms[i+1] == ';' or terms[i+1] == '.':
                continue # spurious ';'
        yield t
def my_expandTriples(terms):
    terms = list(clean_terms(terms))
    return original_expandTriples(terms)
sparql_parser.expandTriples = my_expandTriples
sparql_parser.TriplesSameSubject.setParseAction(my_expandTriples)
sparql_parser.TriplesSameSubjectPath.setParseAction(my_expandTriples)
    
# this is in wait of a proper fix for https://github.com/RDFLib/rdflib/issues/381

register_builtin_method_impl(_SparqlMethod())
