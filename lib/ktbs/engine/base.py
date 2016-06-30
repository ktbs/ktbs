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
I provide the implementation of ktbs:Base .
"""
from rdflib import ConjunctiveGraph, Graph, RDF, RDFS
from contextlib import contextmanager
from posix_ipc import SEMAPHORE_VALUE_SUPPORTED
from rdfrest.exceptions import InvalidParametersError

from .resource import KtbsPostableMixin, KtbsResource
from .lock import WithLockMixin
from ..api.base import BaseMixin, InBaseMixin
from ..namespace import KTBS, KTBS_NS_URI
from ..utils import SKOS


class Base(WithLockMixin, BaseMixin, KtbsPostableMixin, KtbsResource):
    """I provide the implementation of ktbs:Base .
    """

    ######## ICore implementation  ########

    def get_state(self, parameters=None):
        """I override `~rdfrest.cores.ICore.get_state`:meth:

        I support parameter "prop" to enrich the Base description with additional information.
        I consider an empty dict as equivalent to no dict.
        """
        state = super(Base, self).get_state(parameters)
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
                    for s, o in whole.query('''
                        SELECT ?s ?o {
                            GRAPH ?base { ?base :contains ?s }
                            GRAPH ?t    { ?s rdfs:comment ?o }
                        }
                    ''', initNs=initNs, initBindings=initBindings)
                )
            elif prop == 'hasModel':
                enriched_state.addN(
                    (s, KTBS.hasModel, o, enriched_state)
                    for s, o in whole.query('''
                        SELECT ?t ?m {
                            GRAPH ?base { ?base :contains ?t }
                            GRAPH ?t    { ?t :hasModel ?m }
                        }
                    ''', initNs=initNs, initBindings=initBindings)
                )
            elif prop == 'hasSource':
                enriched_state.addN(
                    (s, KTBS.hasSource, o, enriched_state)
                    for s, o in whole.query('''
                        SELECT ?t1 ?t2 {
                            GRAPH ?base { ?base :contains ?t1 }
                            GRAPH ?t1   { ?t1 :hasSource ?t2 }
                        }
                    ''', initNs=initNs, initBindings=initBindings)
                )
            elif prop == 'label':
                enriched_state.addN(
                    (s, p, o, enriched_state)
                    for s, p, o in whole.query('''
                        SELECT ?s ?p ?o {
                            GRAPH ?base { ?base :contains ?s }
                            GRAPH ?s    { ?s ?p ?o }
                            VALUES ?p { rdfs:label skos:prefLabel }
                        }
                    ''', initNs=initNs, initBindings=initBindings)
                )
            elif prop == 'obselCount':
                enriched_state.addN(
                    (s, KTBS.hasObselCount, o, enriched_state)
                    for s, o in whole.query('''
                            SELECT ?t (COUNT(?obs) as ?c) {
                                GRAPH ?base { ?base :contains ?t. ?t a ?tt }
                                OPTIONAL { ?obs :hasTrace ?t }
                                VALUES ?tt { :StoredTrace :ComputedTrace }
                            } GROUP BY ?t
                        ''', initNs=initNs, initBindings=initBindings)
                )
            else:
                pass # ignoring unrecognized properties
                # should we signal them instead (diagnosis?)

        return enriched_state



    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.Base

    RDF_CREATABLE_IN = [ KTBS.hasBase, KTBS.contains, ]

    ######## ILocalCore (and mixins) implementation  ########

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
                super(Base, self).check_parameters(to_check_again, parameters,
                                                   method)

    def ack_delete(self, parameters):
        """I override :meth:`rdfrest.util.EditableCore.ack_delete`.
        """
        super(Base, self).ack_delete(parameters)
        parent = self.get_parent()
        with parent.edit(_trust=True) as editable:
            editable.remove((parent.uri, KTBS.hasBase, self.uri))
            editable.remove((parent.uri, KTBS.contains, self.uri))
            editable.remove((self.uri, RDF.type, self.RDF_MAIN_TYPE))

    def ack_post(self, parameters, created, new_graph):
        """I override :meth:`rdfrest.util.GraphPostableMixin.ack_post`.
        """
        super(Base, self).ack_post(parameters, created, new_graph)
        with self.edit(_trust=True) as editable:
            editable.add((self.uri, KTBS.contains, created))
            for typ in new_graph.objects(created, RDF.type):
                if typ.startswith(KTBS_NS_URI):
                    assert typ in (KTBS.Base, KTBS.TraceModel, KTBS.Method,
                                   KTBS.StoredTrace, KTBS.ComputedTrace,
                                   KTBS.DataGraph,)
                    editable.add((created, RDF.type, typ))
                    break
            else: # no valid rdf:type was found; should not happen
                assert 0, "No valid rdf:type was found for posted resource"

    def check_deletable(self, parameters):
        """I override :meth:`rdfrest.util.EditableCore.check_deletable`.

        Only an empty base can be deleted.
        """
        diag = super(Base, self).check_deletable(parameters)
        if self.state.value(self.uri, KTBS.contains):
            diag.append("Can not delete non-empty Base")
        return diag

    def find_created(self, new_graph):
        """I override :meth:`rdfrest.util.GraphPostableMixin.find_created`.

        I look for the ktbs:contains property, pointing to something a base
        can contain.
        """
        query = """PREFIX ktbs: <%s>
                   SELECT DISTINCT ?c
                   WHERE { <%s> ktbs:contains ?c .
                           { ?c a ktbs:Base} UNION
                           { ?c a ktbs:TraceModel } UNION
                           { ?c a ktbs:Method } UNION
                           { ?c a ktbs:StoredTrace } UNION
                           { ?c a ktbs:ComputedTrace } UNION
                           { ?c a ktbs:DataGraph }
                         }
        """ % (KTBS, self.uri)
        return self._find_created_default(new_graph, query)

    @classmethod
    def create_lock(cls, uri):
        """ I override `WithLockMixin.create_lock`.

        As base creation is protected by the KtbsRoot lock,
        we are sure that this method can not be called concurrently.
        So rather than taking the existing semaphore as is
        and hoping it is correctly set,
        we force it to 1.

        That way, if a previous kTBS didn't clean up its semaphores,
        it won't block a new instance.
        """
        semaphore = super(Base, cls).create_lock(uri)
        if SEMAPHORE_VALUE_SUPPORTED:
            if semaphore.value == 0:
                semaphore.release()
            else:
                while semaphore.value > 1:
                    semaphore.acquire()
        return semaphore



class InBase(InBaseMixin, KtbsResource):
    """I provide common implementation of all elements contained in a base.
    """
    ######## ILocalCore (and mixins) implementation  ########

    RDF_CREATABLE_IN = [ KTBS.contains, ]

    def ack_delete(self, parameters):
        """I override :meth:`rdfrest.util.DeletableMixin.ack_delete`.
        """
        super(InBase, self).ack_delete(parameters)
        base = self.get_base()
        with base.edit(_trust=True) as editable:
            editable.remove((base.uri, KTBS.contains, self.uri))
            editable.remove((self.uri, RDF.type, self.RDF_MAIN_TYPE))

    def delete(self, parameters=None, _trust=False):
        """I override :meth:`rdfrest.cores.local.EditableCore.delete`.
        """
        base = self.get_base()
        with base.lock(self):
            super(InBase, self).delete(parameters, _trust)

    @contextmanager
    def edit(self, parameters=None, clear=False, _trust=False):
        """I override :meth:`rdfrest.cores.local.EditableCore.edit`.
        """
        base = self.get_base()
        with base.lock(self), super(InBase, self).edit(parameters, clear, _trust) as editable:
            yield editable
