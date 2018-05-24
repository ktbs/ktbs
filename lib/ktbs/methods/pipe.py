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
Implementation of the filter builtin methods.
"""
import logging

from rdflib import Literal

from rdfrest.cores.factory import factory
from rdfrest.util import Diagnosis
from .interface import IMethod
from ..engine.builtin_method import get_builtin_method_impl, register_builtin_method_impl
from ..engine.resource import METADATA
from ..namespace import KTBS

LOG = logging.getLogger(__name__)

_FUSION_IMPL = get_builtin_method_impl(KTBS.fusion)

class _PipeMethod(IMethod):
    """I implement the pipe builtin method.
    """
    uri = KTBS.pipe

    def compute_trace_description(self, computed_trace):
        """I implement :meth:`.interface.IMethod.compute_trace_description`.
        """
        diag = Diagnosis("pipe.compute_trace_description")

        src, params =  self._prepare_source_and_params(computed_trace, diag)
        _FUSION_IMPL._init_cstate(computed_trace, diag)
        if src is None:
            return diag

        method_params = params['method_params']
        methods = params['methods']

        source = computed_trace.source_traces[0]
        prev = source
        base = computed_trace.base
        id_template = '_%s_{}'.format(computed_trace.id)

        # create or update intermediate traces
        for i, method in enumerate(methods):
            int_trace_id = id_template % i
            int_trace = base.get(int_trace_id)
            if int_trace is None:
                int_trace = base.create_computed_trace(
                    int_trace_id, method, method_params[i], [prev])
            else:
                with int_trace.edit(_trust=True) as editable:
                    int_trace_uri = int_trace.uri
                    # we do not use the high-level API here,
                    # because it would force the state to refresh
                    # even if no actual changes are done
                    editable.set((int_trace_uri, KTBS.hasMethod, method.uri))
                    editable.remove((int_trace_uri, KTBS.hasParameter, None))
                    for item in method_params[i].items():
                        editable.add((int_trace_uri, KTBS.hasParameter,
                                      Literal('{}={}'.format(*item))))
            prev = int_trace
        effective_source = prev
        computed_trace.metadata.set((computed_trace.uri,
                                     METADATA.effective_source,
                                     effective_source.uri))

        # inherit trace description from effecive_source
        model_uri = effective_source.model_uri
        origin = effective_source.state.value(effective_source.uri, KTBS.hasOrigin)
        with computed_trace.edit(_trust=True) as editable:
            editable.set((computed_trace.uri, KTBS.hasModel, model_uri))
            editable.set((computed_trace.uri, KTBS.hasOrigin, origin))

        # remove spurious intermediate traces
        i = len(methods)
        to_del = []
        while True:
            int_trace_id = id_template % i
            int_trace = base.get(int_trace_id)
            if int_trace is not None:
                to_del.append(int_trace)
            else:
                break
            i += 1
        for int_trace in to_del[::-1]:
            int_trace.delete()

    def compute_obsels(self, computed_trace, from_scratch=False):
        """I implement :meth:`.interface.IMethod.compute_obsels`.
        """
        diag = Diagnosis("pipe.compute_trace_description")
        eff_src_uri = computed_trace.metadata.value(computed_trace.uri,
                                                    METADATA.effective_source)
        effective_source = computed_trace.factory(eff_src_uri)
        if effective_source is None:
            msg = "Effective source can not be found <%s>" % eff_src_uri
            LOG.error(msg)
            diag.append(msg)
            return diag
        else:
            return _FUSION_IMPL.compute_obsels(computed_trace, from_scratch,
                                               [effective_source], diag)

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
            msg = "Method ktbs:pipe expects exactly one source"
            LOG.error(msg)
            diag.append(msg)
            critical = True

        if "methods" not in params:
            msg = "Method ktbs:pipe requires parameter methods"
            LOG.error(msg)
            diag.append(msg)
            critical = True
        
        method_uris = [ i for i in params['methods'].split(' ') if i != '' ]
        if len(method_uris) < 1:
            msg = "Method ktbs:pipe must have at least one method"
            LOG.error(msg)
            diag.append(msg)
            critical = True
        methods = []
        for uri in method_uris:
            m = factory(uri)
            if len(method_uris) < 1:
                msg = "Sub-method <{}> is not accessible".format(uri)
                LOG.error(msg)
                diag.append(msg)
                critical = True
            methods.append(m)
        method_params = [ {} for i in methods ]
        ret_params = {
            'methods_uris': method_uris,
            'methods': methods,
            'method_params': method_params,
        }

        if len(params) > 1:
            diag.append("WARN: Method ktbs:pipe does not support "
                        "additional parameters yet")
            # TODO implement a way to dispatch parameters to submethods

        if critical:
            return None, None
        else:
            return sources[0], ret_params

register_builtin_method_impl(_PipeMethod())
