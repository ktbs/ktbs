# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
I provide the pythonic interface of ktbs:TraceModel .
"""
from rdflib import Literal, RDF

from rdfrest.cores.factory import factory as universal_factory
from rdfrest.util import coerce_to_uri, parent_uri
from .base import InBaseMixin
from rdfrest.wrappers import register_wrapper
from .resource import KtbsResourceMixin
from ..namespace import KTBS, KTBS_NS_URI
from ..utils import extend_api, mint_uri_from_label, SKOS


@register_wrapper(KTBS.TraceModel)
@extend_api
class TraceModelMixin(InBaseMixin):
    """
    I provide the pythonic interface to a trace model.
    """
    # NB: most methods are very permissive with their parameters, and put
    # it blindly in the model's graph.
    # The reason is that model elements can refer to elements from other
    # models, on which we have no control, and that can be modified without
    # notifying us. So even if a parameter is valid when set, it could
    # become invalid later without us noticing.
    # So we don't try to guarantee anything.

    ######## Abstract kTBS API ########

    def get_unit(self):
        """Return the temporal unit used by this model.
        """
        return self.state.value(self.uri, KTBS.hasUnit,
                                default=KTBS.millisecond)

    def set_unit(self, unit):
        """Return the temporal unit used by this model.
        """
        unit = coerce_to_uri(unit, KTBS_NS_URI)
        with self.edit(_trust=True) as graph:
            graph.set((self.uri, KTBS.hasUnit, unit))

    def get(self, id):
        """
        Return the pythonic instance corresponding to the given id, or None.

        :param id: a URI;  can be relative to this Model's URI
        :type  id: str

        :rtype: `AttributeTypeMixin`:class, `ObselTypeMixin`:class: or
                `RelationTypeMixin`:class:

        NB: None if the id is not found *but also* if it does not identify
        a Model element (ObselType, AttributeType or RelationType).
        """
        #pylint: disable-msg=W0622
        #  Redefining built-in id
        uri = coerce_to_uri(id, self.uri)
        for rdf_type in self.state.objects(uri, RDF.type):
            if rdf_type in (KTBS.AttributeType,
                            KTBS.ObselType,
                            KTBS.RelationType):
                ret = self.factory(uri, rdf_type)
                assert isinstance(ret, _ModelElementMixin)
                return ret
        return None

    def iter_parents(self, include_indirect=False):
        """
        I iter over all the parent models of this model.
        """
        cache = set()
        for uri in self.state.objects(self.uri, KTBS.hasParentModel):
            model = universal_factory(uri) or uri
            if include_indirect:
                cache.add(model)
            yield model
        if include_indirect:
            for model in list(cache):
                for i in model.iter_parents(include_indirect=True):
                    if i not in cache:
                        cache.add(i)
                        yield i

    def iter_attribute_types(self, include_inherited=True):
        """
        I iter over the attribute types used in this trace model.
        """
        factory = self.factory
        for uri in self.state.subjects(RDF.type, KTBS.AttributeType):
            yield factory(uri)
        if include_inherited:
            for inherited in self.iter_parents(True):
                for atype in inherited.iter_attribute_types(False):
                    yield atype

    def iter_obsel_types(self, include_inherited=True):
        """
        I iter over the obsel types used in this trace model.
        """
        factory = self.factory
        for uri in self.state.subjects(RDF.type, KTBS.ObselType):
            yield factory(uri)
        if include_inherited:
            for inherited in self.iter_parents(True):
                for otype in inherited.iter_obsel_types(False):
                    yield otype

    def iter_relation_types(self, include_inherited=True):
        """
        I iter over the relation types used in this trace model.
        """
        factory = self.factory
        for uri in self.state.subjects(RDF.type, KTBS.RelationType):
            yield factory(uri)
        if include_inherited:
            for inherited in self.iter_parents(True):
                for rtype in inherited.iter_relation_types(False):
                    yield rtype

    def add_parent(self, model):
        """
        I add model as a parent model to this model.
        """
        with self.edit(_trust=True) as graph:
            graph.add((self.uri, KTBS.hasParentModel,
                       coerce_to_uri(model, self.uri)))

    def remove_parent(self, model):
        """
        I remove model as a parent model to this model.
        """
        with self.edit(_trust=True) as graph:
            graph.remove((self.uri, KTBS.hasParentModel,
                          coerce_to_uri(model, self.uri)))

    def create_obsel_type(self, id=None, supertypes=(), label=None):
        """
        I create a new obsel type in this model.

        :param id: see :ref:`ktbs-resource-creation`
        :param supertypes: explain.
        :param label: explain.

        :rtype: `ObselTypeMixin`:class:
        """
        # redefining built-in 'id' #pylint: disable=W0622
        if id is None  and  label is None:
            raise ValueError("id or label must be supplied")
        uri = mint_uri_from_label(label, self, id)
        with self.edit(_trust=True) as graph:
            base_uri = self.uri
            graph_add = graph.add
            graph_add((uri, RDF.type, KTBS.ObselType))
            if label is not None:
                graph_add((uri, SKOS.prefLabel, Literal(label)))
            for i in supertypes:
                graph_add((uri, KTBS.hasSuperObselType,
                           coerce_to_uri(i, base_uri)))
        ret = self.factory(uri, KTBS.ObselType)
        assert isinstance(ret, ObselTypeMixin)
        return ret

    def create_relation_type(self, id=None, origin=None, destination=None,
                                supertypes=(), label=None):
        """
        I create a new relation type in this model.

        :param id: see :ref:`ktbs-resource-creation`
        :param origin: explain.
        :param destination: explain.
        :param supertypes: explain.
        :param label: explain.

        :rtype: `RelationTypeMixin`:class:
        """
        # redefining built-in 'id' #pylint: disable=W0622
        if id is None  and  label is None:
            raise ValueError("id or label must be supplied")
        uri = mint_uri_from_label(label, self, id)
        with self.edit(_trust=True) as graph:
            base_uri = self.uri
            graph_add = graph.add
            graph_add((uri, RDF.type, KTBS.RelationType))
            if label is not None:
                graph_add((uri, SKOS.prefLabel, Literal(label)))
            if origin is not None:
                origin_uri = coerce_to_uri(origin, self.uri)
                graph_add((uri, _HAS_REL_ORIGIN, origin_uri))
            if destination is not None:
                destination_uri = coerce_to_uri(destination, self.uri)
                graph_add((uri, _HAS_REL_DESTINATION, destination_uri))
            for i in supertypes:
                graph_add((uri, KTBS.hasSuperRelationType,
                     coerce_to_uri(i, base_uri)))
        ret = self.factory(uri, KTBS.RelationType)
        assert isinstance(ret, RelationTypeMixin)
        return ret


    def create_attribute_type(self, id=None, obsel_type=None, data_type=None,
                              value_is_list=False, label=None):
        """
        I create a new obsel type in this model.

        :param id: see :ref:`ktbs-resource-creation`
        :param obsel_type: explain.
        :param data_type: explain.
        :param value_is_list: explain.
        :param label: explain.

        :rtype: `AttributeTypeMixin`:class:
        """
        # redefining built-in 'id' #pylint: disable=W0622
        if id is None  and  label is None:
            raise ValueError("id or label must be supplied")
        uri = mint_uri_from_label(label, self, id)
        with self.edit(_trust=True) as graph:
            base_uri = self.uri
            graph_add = graph.add
            graph_add((uri, RDF.type, KTBS.AttributeType))
            if label is not None:
                graph_add((uri, SKOS.prefLabel, Literal(label)))
            if obsel_type is not None:
                obsel_type_uri = coerce_to_uri(obsel_type, base_uri)
                graph_add ((uri, _HAS_ATT_OBSELTYPE, obsel_type_uri))
            if data_type is not None:
                data_type_uri = coerce_to_uri(data_type, base_uri)
                graph_add ((uri, _HAS_ATT_DATATYPE, data_type_uri))
            # TODO SOON make use of value_is_list
            # ... in the meantime, we lure pylint into ignoring it:
            _ = value_is_list
        ret = self.factory(uri, KTBS.AttributeType)
        assert isinstance(ret, AttributeTypeMixin)
        return ret

    ######## Extension to the abstract kTBS API ########

    def add_supertype(self, element=None, element_type=None, super_type=None):
        """
        I add a super type to the element (obsel or relation) type in this 
        model.

        :param element: ObselType or RelationType or their URI.
        :param element_type: Type of the concerned element.
        :param super_type: SuperObselType or SuperRelationType.
        """
        if element is not None:
            uri = coerce_to_uri(element, self.uri)
        else:
            raise ValueError("element must be supplied")

        base_uri = self.uri
        with self.edit(_trust=True) as graph:
            if element_type == KTBS.ObselType:
                graph.add((uri, KTBS.hasSuperObselType,
                           coerce_to_uri(super_type, base_uri)))
            if element_type == KTBS.RelationType:
                graph.add((uri, KTBS.hasSuperRelationType, 
                           coerce_to_uri(super_type, base_uri)))

    def remove_supertype(self, element=None, element_type=None, 
                         super_type=None):
        """
        I remove a super type from the element (obsel or relation) type in 
        this model.

        :param element: ObselType or RelationType or their URI.
        :param element_type: Type of the concerned element.
        :param super_type: SuperObselType or SuperRelationType.
        """
        if element is not None:
            uri = coerce_to_uri(element, self.uri)
        else:
            raise ValueError("element must be supplied")

        base_uri = self.uri
        with self.edit(_trust=True) as graph:
            if element_type == KTBS.ObselType:
                graph.remove((uri, KTBS.hasSuperObselType,
                             coerce_to_uri(super_type, base_uri)))
            if element_type == KTBS.RelationType:
                graph.remove((uri, KTBS.hasSuperRelationType, 
                             coerce_to_uri(super_type, base_uri)))

@extend_api
class _ModelElementMixin(KtbsResourceMixin):
    """
    I provide the common pythonic interface to any element of trace models.

    I make the assumption that self.state is in fact containing the *whole*
    trace model, not just the description of this element, and that its
    identifier is the URI of the trace model. This is consistent with common
    modelling practices, where elements of a model/ontology will usually have
    their URI redirect to the model/ontology itself (directly for # URIs, or
    with 303 for / URIs).
    """
    ######## Abstract kTBS API ########

    def get_model(self):
        """
        Return the trace model defining this element.
        
        :rtype: `TraceModelMixin`:class:
        """
        #tmodel_uri = self.state.identifier
        #ret = self.factory(tmodel_uri, KTBS.TraceModel)
        #return ret

        #Waiting above code to be fixed.
        #We can have .../Model#ElementType
        #or          .../Model/ElementType
        defragmented_uri = self.uri.defrag()
        if len(self.uri) != len(defragmented_uri):
            model_uri = defragmented_uri
        else:
            model_uri = parent_uri(self.uri)
        ret = self.factory(model_uri, KTBS.TraceModel)
        assert isinstance(ret, TraceModelMixin)
        return ret
        
    def remove(self):
        """Edit the containing model to remove this element.
        """
        with self.model.edit(_trust=True) as editable:
            editable.remove((self.uri, None, None))
            editable.remove((None, None, self.uri))

@extend_api
class _ModelTypeMixin(_ModelElementMixin):
    """
    I provide the common pythonic interface to types defined in a trace model.

    Subclasses must override _SUPER_TYPE_PROP
    """
    _RDF_TYPE = None
    _SUPER_TYPE_PROP = None

    ######## Abstract kTBS API ########

    def iter_subtypes(self, include_indirect=False):
        """
        I list the subtypes of this type from the same model.
        If include_indirect is True, all subtype from the same model are
        listed, including indirect supertypes and this type itself
        """
        if include_indirect:
            return _closure(self, "subtypes")
        else:
            return ( universal_factory(uri) 
                     for uri in self.state.subjects(self._SUPER_TYPE_PROP,
                                                     self.uri) )

    def iter_supertypes(self, include_indirect=False):
        """
        I list the supertypes of this type.
        If include_indirect is True, all supertypes are listed,
        including indirect supertypes and this type itself
        """
        if include_indirect:
            return _closure(self, "supertypes")
        else:
            return ( universal_factory(uri, self._RDF_TYPE)
                     for uri in self.state.objects(self.uri, 
                                                    self._SUPER_TYPE_PROP) )

    def add_supertype(self, super_type):
        """
        Add super relation type to the current relation type.
        """
        model = self.get_model()

        model.add_supertype(element=self.uri,
                            element_type= self._RDF_TYPE,
                            super_type=super_type)

    def remove_supertype(self, super_type):
        """
        Remove super relation type to the current relation type.
        """
        model = self.get_model()

        model.remove_supertype(element=self.uri,
                               element_type= self._RDF_TYPE,
                               super_type=super_type)

    ######## Extension to the abstract kTBS API ########

    def matches(self, *others):
        """
        Return True iff this type is a specialization of every element in
        others.

        If others contains only one element, this element can be None, and then
        it will be considered to match.
        """
        if tuple(others) == (None,):
            return True
        others = set(others)
        mine = set(self.iter_supertypes(True))
        if others - mine:
            return False
        else:
            return True

@register_wrapper(KTBS.AttributeType)
@extend_api
class AttributeTypeMixin(_ModelElementMixin):
    """
    I provide the pythonic interface to an attribute type.
    """
    ######## Abstract kTBS API ########

    def get_obsel_type(self):
        """
        I hold the obsel type containing this attribute, or None.

        :rtype: `ObselTypeMixin`:class:
        """
        uri = self.state.value(self.uri, _HAS_ATT_OBSELTYPE)
        if uri is None:
            return None
        else:
            ret = universal_factory(uri)
            assert isinstance(ret, ObselTypeMixin)
            return ret

    def set_obsel_type(self, obsel_type):
        """
        I set the obsel type of this attribute.
        """
        obsel_type_uri = coerce_to_uri(obsel_type)
        with self.edit(_trust=True) as editable:
            editable.set((self.uri, _HAS_ATT_OBSELTYPE, obsel_type_uri))

    def get_data_type(self):
        """
        I hold the data type allowed for this attribute, or None (any).

        Returns the type as a URIRef
        """
        return self.state.value(self.uri, _HAS_ATT_DATATYPE)

    def set_data_type(self, data_type):
        """
        I set the data type of this attribute.
        """
        # TODO LATER check data_type?
        # what kind of datatype do we accept? see ktbs.namespace
        data_type_uri = coerce_to_uri(data_type)
        with self.edit(_trust=True) as editable:
            editable.set((self.uri, _HAS_ATT_DATATYPE, data_type_uri))


@register_wrapper(KTBS.ObselType)
@extend_api
class ObselTypeMixin(_ModelTypeMixin):
    """
    I provide the pythonic interface to an obsel type.
    """

    _RDF_TYPE = KTBS.ObselType
    _SUPER_TYPE_PROP = KTBS.hasSuperObselType

    ######## Abstract kTBS API ########

    def iter_attribute_types(self, include_inherited=True):
        """
        I iter over the attribute types allowed for this type.
        """
        if include_inherited:
            for supertype in self.iter_supertypes(True):
                for atype in supertype.iter_attribute_types(False):
                    yield atype
        else:
            for uri in self.state.subjects(_HAS_ATT_OBSELTYPE, self.uri):
                yield universal_factory(uri)

    def iter_relation_types(self, include_inherited=True):
        """
        I iter over the relation types having this obsel type as origin.
        """
        if include_inherited:
            for supertype in self.iter_supertypes(True):
                for rtype in supertype.iter_relation_types(False):
                    yield rtype
        else:
            for uri in self.state.subjects(_HAS_REL_ORIGIN, self.uri):
                yield universal_factory(uri)

    def iter_inverse_relation_types(self, include_inherited=True):
        """
        I iter over the relation types having this obsel type as destination.
        """
        if include_inherited:
            for supertype in self.iter_supertypes(True):
                for rtype in supertype.iter_inverse_relation_types(False):
                    yield rtype
        else:
            for uri in self.state.subjects(_HAS_REL_DESTINATION, self.uri):
                yield universal_factory(uri)

    def create_attribute_type(self, id=None, data_type=None,
                              value_is_list=False, label=None):
        """
        Call the associated Model method.
        """
        # redefining built-in 'id' #pylint: disable=W0622
        model = self.get_model()
        return model.create_attribute_type(id=id, 
                                           obsel_type=self.uri,
                                           data_type=data_type,
                                           value_is_list=value_is_list,
                                           label=label)

    def create_relation_type(self, id=None, destination=None,
                             supertypes=(), label=None):
        """
        Call the associated Model method.
        """
        # redefining built-in 'id' #pylint: disable=W0622
        model = self.get_model()
        return model.create_relation_type(id=id, 
                                          origin=self.uri, 
                                          destination=destination,
                                          supertypes=supertypes, 
                                          label=label)

@register_wrapper(KTBS.RelationType)
@extend_api
class RelationTypeMixin(_ModelTypeMixin):
    """
    I provide the pythonic interface to a relation type.
    """

    _RDF_TYPE = KTBS.RelationType
    _SUPER_TYPE_PROP = KTBS.hasSuperRelationType

    ######## Abstract kTBS API ########

    def get_origin(self):
        """
        I hold the origin obsel type this relation, or None.

        :rtype: `ObselTypeMixin`:class:
        """
        uri = self.state.value(self.uri, _HAS_REL_ORIGIN)
        if uri is None:
            return None
        else:
            ret = universal_factory(uri)
            assert isinstance(ret, ObselTypeMixin), ret
            return ret

    def get_destination(self):
        """
        I hold the destination obsel type this relation, or None.

        :rtype: `ObselTypeMixin`:class:
        """
        uri = self.state.value(self.uri, _HAS_REL_DESTINATION)
        if uri is None:
            return None
        else:
            ret = universal_factory(uri)
            assert isinstance(ret, ObselTypeMixin), ret
            return ret

    def iter_all_origins(self):
        """
        I iter over all the origins (direct or inherited) of this relation.

        :rtype: iterator of `ObselTypeMixin`:class:
        """
        seen = set()
        for rtype in self.iter_supertypes(True):
            rorigin = rtype.origin
            if rorigin is not None and rorigin not in seen:
                yield rorigin
                seen.add(rorigin)

    def iter_all_destinations(self):
        """
        I iter over all the destinations (direct or inherited) of this
        relation.

        :rtype: iterator of `ObselTypeMixin`:class:
        """
        seen = set()
        for rtype in self.iter_supertypes(True):
            rdestination = rtype.destination
            if rdestination is not None and rdestination not in seen:
                yield rdestination
                seen.add(rdestination)

def _closure(obj, iter_property_name):
    """
    I iter over the closure of the method named by iter_property_name, starting
    at obj.
    """
    seen = set([obj])
    queue = set(seen)
    while queue:
        i = queue.pop()
        yield i
        for j in getattr(i, iter_property_name):
            if not j in seen:
                seen.add(j)
                queue.add(j)

_HAS_ATT_OBSELTYPE = KTBS.hasAttributeDomain # should be renamed at some point?
_HAS_ATT_DATATYPE = KTBS.hasAttributeRange # should be renamed at some point?
_HAS_REL_ORIGIN = KTBS.hasRelationDomain # should be renamed at some point?
_HAS_REL_DESTINATION = KTBS.hasRelationRange # should be renamed at some point?
