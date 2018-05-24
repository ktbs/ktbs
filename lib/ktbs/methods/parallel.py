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
from ..engine.builtin_method import get_builtin_method_impl, \
    register_builtin_method_impl
from ..engine.resource import METADATA
from ..namespace import KTBS

LOG = logging.getLogger(__name__)

_FUSION_IMPL = get_builtin_method_impl(KTBS.fusion)


class _ParallelMethod(IMethod):
    """I implement the parallel builtin method.
    """
    uri = KTBS.parallel

    def compute_trace_description(self, computed_trace):
        """I implement :meth:`.interface.IMethod.compute_trace_description`.
        """
        diag = Diagnosis("parallel.compute_trace_description")
        params = computed_trace.parameters_as_dict
        critical = False

        if len(computed_trace.source_traces) != 1:
            msg = "Method ktbs:parallel expects exactly one source"
            LOG.error(msg)
            diag.append(msg)
            critical = True

        critical, fusion_params = \
            _FUSION_IMPL._get_fusion_parameters(params, diag, critical)
        if "methods" not in params:
            msg = "Method ktbs:parallel requires parameter methods"
            LOG.error(msg)
            diag.append(msg)
            critical = True
        else:
            method_uris = [i for i in params.pop('methods').split(' ') if i != '']
            if len(method_uris) < 1:
                msg = "Method ktbs:parellel must have at least one method"
                LOG.error(msg)
                diag.append(msg)
                critical = True
            methods = []
            method_params = []
            for uri in method_uris:
                m = factory(uri)
                if len(method_uris) < 1:
                    msg = "Sub-method <{}> is not accessible".format(uri)
                    LOG.warning(msg)
                    diag.append("WARN: "+msg)
                else:
                    methods.append(m)
                    method_params.append({})
            parallel_params = {
                'methods_uris': method_uris,
                'methods': methods,
                'method_params': method_params,
            }
            if len(params) > 1:
                diag.append("Method ktbs:parallel does not support "
                            "additional parameters yet")
                # TODO implement a way to dispatch parameters to submethods

            if not critical:
                sources = self._prepare_intermediate_traces(computed_trace,
                                                            parallel_params)
                _FUSION_IMPL._do_compute_trace_description(computed_trace, sources,
                                                           fusion_params, diag)
        _FUSION_IMPL._init_cstate(computed_trace, diag)


    def compute_obsels(self, computed_trace, from_scratch=False):
        """I implement :meth:`.interface.IMethod.compute_obsels`.
        """
        diag = Diagnosis("paralel.compute_trace_description")
        eff_src_uris = computed_trace.metadata.objects(computed_trace.uri,
                                                       METADATA.effective_source)
        effective_sources = []
        for uri in eff_src_uris:
            eff_src = computed_trace.factory(uri)
            if eff_src is None:
                msg = "Effective source can not be found <%s>" % eff_src_uri
                LOG.warning(msg)
                diag.append("WARN: "+msg)
            else:
                effective_sources.append(eff_src)
        return _FUSION_IMPL.compute_obsels(computed_trace, from_scratch,
                                           effective_sources, diag)

    @staticmethod
    def _prepare_intermediate_traces(computed_trace, params):
        method_params = params['method_params']
        methods = params['methods']
        source = computed_trace.source_traces[0]
        base = computed_trace.base
        id_template = '_%s_{}'.format(computed_trace.id)

        # create or update intermediate traces
        effective_sources = []
        for i, method in enumerate(methods):
            int_trace_id = id_template % i
            int_trace = base.get(int_trace_id)
            if int_trace is None:
                int_trace = base.create_computed_trace(
                    int_trace_id, method, method_params[i], [source])
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
            effective_sources.append(int_trace)

        computed_trace.metadata.remove((computed_trace.uri,
                                        METADATA.effective_source,
                                        None))
        for eff_src in effective_sources:
            computed_trace.metadata.add((computed_trace.uri,
                                         METADATA.effective_source,
                                         eff_src.uri))

        # remove spurious intermediate tracess
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

        return effective_sources


register_builtin_method_impl(_ParallelMethod())
