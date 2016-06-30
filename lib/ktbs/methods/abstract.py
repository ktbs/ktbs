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

"""I define an abstract implementation for mono-source transformation methods.

Method based on this class will always exactly one source.

It handles

TODO: document how to use this
"""
import traceback
from json import dumps as json_dumps, loads as json_loads
import logging

from rdflib import Literal, URIRef

from rdfrest.util import Diagnosis
from .interface import IMethod
from ..engine.resource import METADATA
from ..namespace import KTBS

LOG = logging.getLogger(__name__)

NOT_MON = 0
LOGIC_MON = 1
PSEUDO_MON = 2
STRICT_MON = 3

class AbstractMonosourceMethod(IMethod):
    """An abstract implementation of a mono-source transformation method.
    """
    
    # the following attributes must be overridden by subclasses

    uri = None # a rdflib.URIRef identifying this transformation method

    # the following attributes may be overridden by subclasses

    parameter_types = {} # a dict enumerating all the possible parameters and their expected type
    required_parameters = () # an iterable of parameter names
    target_model = None # override (with URIRef) if you want to force the compute trace's origin
    target_origin = None # override (with URIRef) if you want to force the compute trace's origin

    # the following methods may be overridden by subclasses

    def compute_model(self, computed_trace, params, diag):
        """Compute the model of the computed trace.
        
        The default implementation works as follows:
        * if there is a parameter 'model', it will be returned;
        * else, if the 'target_model' attribute of the method is not None, it will be returned;
        * else, the model of the source trace will be returned.

        TODO document parameters
        """
        model = params.get("model")
        if model is not None:
            return model
        elif self.target_model is not None:
            return self.target_model
        else:
            return computed_trace.source_traces[0].model_uri

    def compute_origin(self, computed_trace, params, diag):
        """Compute the origin of the computed trace.
        
        The default implementation works as follows:
        * if there is a a parameter 'origin', it will be returned;
        * else, if the 'target_origin' attribute of the method is not None, it will be returned;
        * else, the origin of the source trace will be returned.

        TODO document parameters
        """        
        origin = params.get("origin")
        if origin is not None:
            return Literal(origin)
        elif self.target_origin is not None:
            return self.target_origin
        else:
            source = computed_trace.source_traces[0]
            return source.state.value(source.uri, KTBS.hasOrigin)

    def init_state(self, computed_trace, cstate, params, diag):
        """Return the initial structure of the computation state.

        The computation state is a JSON-compatible dict,
        that will hold information across several computation steps.

        TODO document parameters
        """
        pass

    # the following methods must be overridden by subclasses

    def do_compute_obsels(self, computed_trace, cstate, monotonicity, diag):
        """Computes the obsels of the computed trace.

        TODO document parameters
        """
        raise NotImplemented


    # the following methods should not be changed by subclasses,
    # the constitute the common implementation of IMethod by all subclasses

    def compute_trace_description(self, computed_trace):
        """I implement :meth:`.interface.IMethod.compute_trace_description`.
        """
        diag = Diagnosis("compute_trace_description for <{}>".format(self.uri))

        cstate = {
            'errors': None,
            'log_mon_tag': None,
            'pse_mon_tag': None,
            'str_mon_tag': None,
            'custom': {},
        }

        params =  self._prepare_params(computed_trace, diag)
        if len(computed_trace.source_traces) != 1:
            diag.append("Method <{}> expects exactly one source".format(self.uri))
            params = None
        if params is not None:
            model = self.compute_model(computed_trace, params, diag)
            origin = self.compute_origin(computed_trace, params, diag)
            with computed_trace.edit(_trust=True) as editable:
                editable.add((computed_trace.uri, KTBS.hasModel, model))
                editable.add((computed_trace.uri, KTBS.hasOrigin, origin))
            self.init_state(computed_trace, params, cstate['custom'], diag)

        if not diag:
            cstate["errors"] = list(diag)

        computed_trace.metadata.set((computed_trace.uri,
                                     METADATA.computation_state,
                                     Literal(json_dumps(cstate))
                                     ))

        return diag

    def compute_obsels(self, computed_trace, from_scratch=False):
        """I implement :meth:`.interface.IMethod.compute_obsels`.
        """
        diag = Diagnosis("compute_obsels for <{}>".format(self.uri))
        cstate = json_loads(
            computed_trace.metadata.value(computed_trace.uri,
                                          METADATA.computation_state))
        if from_scratch:
                cstate["log_mon_tag"] = None
                cstate["pse_mon_tag"] = None
                cstate["str_mon_tag"] = None
        errors = cstate.get("errors")
        if errors:
            for i in errors:
                diag.append(i)
                return diag

        source_obsels = computed_trace.source_traces[0].obsel_collection
        from logging import getLogger; LOG = getLogger()
        if cstate["str_mon_tag"] == source_obsels.str_mon_tag:
            monotonicity = STRICT_MON
        elif cstate["pse_mon_tag"] == source_obsels.pse_mon_tag:
            monotonicity = PSEUDO_MON
        elif cstate["log_mon_tag"] == source_obsels.log_mon_tag:
            monotonicity = LOGIC_MON
        else:
            monotonicity = NOT_MON

        self.do_compute_obsels(computed_trace, cstate['custom'], monotonicity, diag)

        cstate["log_mon_tag"] = source_obsels.log_mon_tag
        cstate["pse_mon_tag"] = source_obsels.pse_mon_tag
        cstate["str_mon_tag"] = source_obsels.str_mon_tag

        computed_trace.metadata.set((computed_trace.uri,
                                     METADATA.computation_state,
                                     Literal(json_dumps(cstate))
                                     ))
        return diag

    def _prepare_params(self, computed_trace, diag):
        """I check and prepare the parameters passed to the method.

        I return a dict of useful parameters converted to the expected datatype.
        If this can not be done, I return None.

        I also populate `diag` with error/warning messages.
        """
        params = computed_trace.parameters_as_dict
        critical = False

        for key, val in params.items():
            datatype = self.parameter_types.get(key)
            if datatype is None:
                diag.append("WARN: Parameter %s is not used by <%s>"
                            % (key, self.uri))
            else:
                try:
                    params[key] = datatype(val)
                except Exception as e:
                    LOG.info(traceback.format_exc())
                    diag.append("Parameter %s has illegal value: %s.\n"
                                "    Reason: %s"
                                % (key, val, e.message))
                    critical = True

        for key in self.required_parameters:
            if key not in params:
                diag.append("Parameter '%s' is required" % key)
                critical = True

        if critical:
            return None
        else:
            return params
