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
from pyparsing import ParseException
from rdfrest.exceptions import ParseError
from rdfrest.utils import Diagnosis
from rdflib import Literal, URIRef
import rdflib.plugins.sparql.algebra

from .interface import IMethod
from .utils import replace_obsels
from ..namespace import KTBS
from ..engine.builtin_method import register_builtin_method_impl

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

    def compute_obsels(self, computed_trace):
        """I implement :meth:`.interface.IMethod.compute_obsels`.
        """
        diag = Diagnosis("sparql.compute_obsels")

        source = computed_trace.source_traces[0]
        parameters = computed_trace.parameters_as_dict
        parameters["__destination__"] = computed_trace.uri
        parameters["__source__"] = source.uri

        try:
            sparql = parameters["sparql"] % parameters
            result = source.obsel_collection.get_state({"quick":1}).query(sparql).graph
            replace_obsels(computed_trace, result, ("inherit" in parameters))
        except KeyError, exc:
            diag.append(str(exc))
        except TypeError, exc:
            diag.append(str(exc))
        except ParseException, exc:
            diag.append(str(exc))
        except AttributeError, exc:
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
                    diag.append("Parameter %s has illegal value: %s"
                                % (key, val))
                    critical = True
                except ParseError:
                    diag.append("Parameter %s has illegal value: %s"
                                % (key, val))
                    critical = True

        if critical:
            return None, None
        else:
            return sources[0], params

_PARAMETERS_TYPE = {
    "origin": Literal,
    "model": URIRef,
    "sparql": str,
    "inherit": str,
}

# monkeypatch to fix a bug in rdflib.plugins.sparql
def my_triples(l): 
    l=reduce(lambda x,y: x+y, l)
    #if (len(l) % 3) != 0: 
    #    #import pdb ; pdb.set_trace()
    #    raise Exception('these aint triples')
    return sorted([(l[x],l[x+1],l[x+2]) for x in range(0,len(l)-2,3)])
rdflib.plugins.sparql.algebra.triples = my_triples


register_builtin_method_impl(_SparqlMethod())
