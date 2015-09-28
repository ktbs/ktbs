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
Implementation of the external builtin methods.
"""
import logging
from os import getenv
from rdflib import Literal, Graph, URIRef
from rdfrest.util import Diagnosis
from rdfrest.exceptions import ParseError
from subprocess import Popen, PIPE

from .interface import IMethod
from .utils import replace_obsels
from ..engine.builtin_method import register_builtin_method_impl
from ..namespace import KTBS

LOG = logging.getLogger(__name__)

class _ExternalMethod(IMethod):
    """I implement the external builtin method.
    """
    uri = KTBS.external

    def compute_trace_description(self, computed_trace):
        """I implement :meth:`.interface.IMethod.compute_trace_description`.
        """
        diag = Diagnosis("external.compute_trace_description")

        srcs, params =  self._prepare_sources_and_params(computed_trace, diag)
        if srcs is not None:

            assert params is not None
            model = params.get("model")
            if model is not None:
                model = URIRef(model)
            else:
                models = set( src.model_uri for src in srcs )
                if len(models) != 1:
                    diag.append("Can not infer model from sources and no "
                                "target model is explicitly specified")
                else:
                    model = models.pop()

            origin = params.get("origin")
            if origin is None:
                origins = set( src.origin for src in srcs )
                if len(origins) != 1:
                    diag.append("Can not infer origin from sources and no "
                                "target origin is explicitly specified")
                else:
                    origin = origins.pop()
            origin = Literal(origin)

            with computed_trace.edit(_trust=True) as editable:
                editable.add((computed_trace.uri, KTBS.hasModel, model))
                editable.add((computed_trace.uri, KTBS.hasOrigin, origin))

        return diag

    def compute_obsels(self, computed_trace, from_scratch=False):
        """I implement :meth:`.interface.IMethod.compute_obsels`.
        """
        diag = Diagnosis("external.compute_obsels")

        sources = computed_trace.source_traces
        parameters = computed_trace.parameters_as_dict
        parameters["__destination__"] = computed_trace.uri
        parameters["__sources__"] = " ".join( s.uri for s in sources )

        rdfformat = parameters.get("format", "n3")

        command_line = parameters["command-line"] % parameters
        if parameters.get("feed-to-stdin"):
            stdin = PIPE
            stdin_data = (sources[0].obsel_collection
                          .get_state({"refresh":"no"})
                          .serialize(format=rdfformat, encoding="utf-8"))
        else:
            stdin = None
            stdin_data = None

        popen_env = {
            "PATH": getenv("PATH", ""),
            "PYTHONPATH": getenv("PYTHONPATH", ""),
            }
        LOG.info("Running: %s" % command_line)
        child = Popen(command_line, shell=True, stdin=stdin, stdout=PIPE,
                      close_fds=True, env=popen_env)
        rdfdata, _ = child.communicate(stdin_data)
        if child.returncode != 0:
            diag.append("command-line ended with error: %s" % child.returncode)
        raw_graph = Graph()
        try:
            raw_graph.parse(data=rdfdata, publicID=computed_trace.uri,
                            format=rdfformat)
        except Exception, exc:
            diag.append(str(exc))
        replace_obsels(computed_trace, raw_graph)

        return diag

    @staticmethod
    def _prepare_sources_and_params(computed_trace, diag):
        """I check and prepare the data required by the method.

        I return the sources of the computed trace, and a dict of
        useful parameters converted to the expected datatype. If this can not
        be done, I return ``(None, None)``.

        I also populate `diag` with error/warning messages.
        """
        sources = computed_trace.source_traces
        params = computed_trace.parameters_as_dict
        critical = False

        if "command-line" not in params:
            diag.append("Method ktbs:external requires parameter command-line")
            critical = True
        cmdline = params.get("command-line", "")

        for key, val in params.items():
            datatype = _PARAMETERS_TYPE.get(key)
            if datatype is None:
                if ("%%(%s)s" % key) not in cmdline:
                    diag.append("WARN: Parameter %s is not used by "
                                "ktbs:external nor by the command line"
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

        nsrc = len(sources)
        minsrc = params.get("min-sources")
        if minsrc and  nsrc < minsrc:
            diag.append("Too few sources (%s, min is %s)" % (nsrc, minsrc))
            critical = True
        maxsrc = params.get("max-sources")
        if maxsrc and  nsrc > maxsrc:
            diag.append("Too many sources (%s, max is %s)" % (nsrc, maxsrc))
            critical = True

        if critical:
            return None, None
        else:
            return sources, params


_PARAMETERS_TYPE = {
    "origin": Literal,
    "model": URIRef,
    "command-line": str,
    "min-sources": int,
    "max-sources": int,
    "feed-to-stdin": bool, # for the moment assume 1st source
    "format": str,
}


register_builtin_method_impl(_ExternalMethod())
