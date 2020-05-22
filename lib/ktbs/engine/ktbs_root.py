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
I provide the implementation of ktbs:KtbsRoot .
"""

from rdflib import ConjunctiveGraph, Graph, RDF, RDFS
from rdfrest.exceptions import MethodNotAllowedError

from .resource import KtbsPostableMixin, KtbsResource
from .lock import WithLockMixin
from ..api.ktbs_root import KtbsRootMixin
from ..namespace import KTBS
from ..utils import SKOS


class KtbsRoot(WithLockMixin, KtbsRootMixin, KtbsPostableMixin, KtbsResource):
    """I provide the implementation of ktbs:KtbsRoot .
    """
    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.KtbsRoot

    def check_parameters(self, to_check, parameters, method):
        """I implement :meth:`~rdfrest.cores.local.ILocalCore.check_parameters`

        I also convert parameters values from strings to usable datatypes.
        """
        if parameters is not None:
            to_check_again = None
            if method in ("get_state", "force_state_refresh"):
                for key in to_check:
                    val = parameters[key]
                    if key == 'prop':
                        parameters[key] = val.split(',')
                    else:
                        if to_check_again is None:
                            to_check_again = []
                        to_check_again.append(key)
            else:
                to_check_again = to_check
            if to_check_again:
                super(KtbsRoot, self).check_parameters(to_check_again, parameters,
                                                       method)

    def delete(self, parameters=None, _trust=True):
        """I override :meth:`rdfrest.util.EditableCore.delete`.

        A kTBS root can never be deleted.
        """
        # We do not use check_deletable, because that would raise a
        # CanNotProceedError, which is semantically less correct.
        raise MethodNotAllowedError("Can not delete KtbsRoot")

    def ack_post(self, parameters, created, new_graph):
        """I override :meth:`rdfrest.util.GraphPostableMixin.ack_post`.
        """
        super(KtbsRoot, self).ack_post(parameters, created, new_graph)
        with self.edit(_trust=True) as editable:
            editable.add((self.uri, KTBS.hasBase, created))

    def find_created(self, new_graph):
        """I override :meth:`rdfrest.util.GraphPostableMixin.find_created`.

        I look for the ktbs:hasBase property, pointing to a ktbs:Base.
        """
        query = """PREFIX ktbs: <%s>
                   SELECT DISTINCT ?c
                   WHERE { <%s> ktbs:hasBase ?c . ?c a ktbs:Base . }
        """ % (KTBS, self.uri)
        return self._find_created_default(new_graph, query)

    ######## ICore implementation  ########

    def get_state(self, parameters=None):
        """I override `~rdfrest.cores.ICore.get_state`:meth:

        I support parameter "prop" to enrich the KtbsRoot description with additional information.
        I consider an empty dict as equivalent to no dict.
        """
        state = super(KtbsRoot, self).get_state(parameters)
        if not parameters:
            return state

        enriched_state = Graph()
        enriched_state += state
        whole = ConjunctiveGraph(self.service.store)
        initNs = { '': KTBS, 'rdfs': RDFS, 'skos': SKOS }
        initBindings = { 'base': self.uri }
        for prop in parameters['prop']:
            if prop == 'comment':
                enriched_state.addN(
                    (s, RDFS.comment, o, enriched_state)
                    for s, o, _ in whole.query('''
                        SELECT ?s ?o
                          $root # selected solely to please Virtuoso
                        {
                            GRAPH $root { $root :hasBase ?s }
                            GRAPH ?s    { ?s rdfs:comment ?o }
                        }
                    ''', initNs=initNs, initBindings=initBindings)
                )
            elif prop == 'label':
                enriched_state.addN(
                    (s, p, o, enriched_state)
                    for s, p, o, _ in whole.query('''
                        SELECT ?s ?p ?o
                          $root # selected solely to please Virtuoso
                        {
                            VALUES ?p { rdfs:label skos:prefLabel }
                            GRAPH $root { $root :hasBase ?s }
                            GRAPH ?s    {
                                $root :hasBase ?s.
                                ?s ?p ?o.
                            }
                        }
                    ''', initNs=initNs, initBindings=initBindings)
                )
            else:
                pass # ignoring unrecognized properties
                # should we signal them instead (diagnosis?)

        return enriched_state
