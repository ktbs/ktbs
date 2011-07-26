#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
I provide the pythonic interface to trace models and their components.
"""
from rdflib import Literal, RDF

from ktbs.common.base import InBaseMixin
from ktbs.common.resource import ResourceMixin
from ktbs.common.utils import extend_api, mint_uri
from ktbs.namespaces import KTBS, SKOS
from rdfrest.utils import coerce_to_uri

@extend_api
class ModelMixin(InBaseMixin):
    """
    I provide the pythonic interface to a trace model.
    """

    def get_unit(self):
        """Return the temporal unit used by this model.
        """
        return self._graph.value(self.uri, _HAS_UNIT, default="ms")

    def set_unit(self, unit):
        """Return the temporal unit used by this model.
        """
        unit = Literal(str(unit))
        with self._edit as graph:
            graph.add((self.uri, _HAS_UNIT, unit))

    def get(self, id):
        """
        Return the pythonic instance corresponding to the given id, or None.

        `id` can be relative to this Model's URI.

        NB: None if the id is not found *but also* if it does not identify
        a Model element (ObselType, AttributeType or RelationType).
        """
        #pylint: disable-msg=W0622
        #  Redefining built-in id
        uri = coerce_to_uri(id, self.uri)
        for rdf_type in self._graph.objects(uri, _RDF_TYPE):
            if rdf_type in (_ATTR_TYPE, _OBSEL_TYPE, _REL_TYPE):
                return self.make_resource(uri, rdf_type)
        return None

    def iter_parents(self, include_indirect=False):
        """
        I iter over all the parent models of this model.
        """
        make_resource = self.make_resource
        cache = set()
        for uri in self._graph.objects(self.uri, _HAS_PARENT_MODEL):
            model = make_resource(uri) or uri
            if include_indirect:
                cache.add(model)
            yield model
        if include_indirect:
            for model in list(cache):
                for i in model.iter_indirect(True):
                    if i not in cache:
                        cache.add(i)
                        yield i

    def iter_attribute_types(self, include_inherited=True):
        """
        I iter over the attribute types used in this trace model.
        """
        make_resource = self.make_resource
        for uri in self._graph.subjects(_RDF_TYPE, _ATTR_TYPE):
            yield make_resource(uri)
        if include_inherited:
            for inherited in self.iter_inherited(True):
                for atype in inherited.iter_attribute_types(False):
                    yield atype

    def iter_obsel_types(self, include_inherited=True):
        """
        I iter over the obsel types used in this trace model.
        """
        make_resource = self.make_resource
        for uri in self._graph.subjects(_RDF_TYPE, _OBSEL_TYPE):
            yield make_resource(uri)
        if include_inherited:
            for inherited in self.iter_inherited(True):
                for otype in inherited.iter_obsel_types(False):
                    yield otype

    def iter_relation_types(self, include_inherited=True):
        """
        I iter over the relation types used in this trace model.
        """
        make_resource = self.make_resource
        for uri in self._graph.subjects(_RDF_TYPE, _REL_TYPE):
            yield make_resource(uri)
        if include_inherited:
            for inherited in self.iter_inherited(True):
                for rtype in inherited.iter_relation_types(False):
                    yield rtype

    def add_parent(self, model):
        """
        I add model as a parent model to this model.
        """
        with self._edit as graph:
            graph.add((self.uri, _HAS_PARENT_MODEL,
                       coerce_to_uri(model, self.uri)))

    def remove_parent(self, model):
        """
        I remove model as a parent model to this model.
        """
        with self._edit as graph:
            graph.remove((self.uri, _HAS_PARENT_MODEL,
                          coerce_to_uri(model, self.uri)))

    def create_obsel_type(self, label, supertypes=(), id=None):
        """
        I create a new obsel type in this model.
        """
        # redefining built-in 'id' #pylint: disable=W0622
        base_uri = self.uri
        with self._edit as graph:
            uri = mint_uri(label, self, id)
            add = graph.add
            add((uri, _RDF_TYPE, _OBSEL_TYPE))
            add((uri, _PREF_LABEL, Literal(label)))
            for i in supertypes:
                add((uri, _HAS_SUPEROTYPE, coerce_to_uri(i, base_uri)))
        return self.make_resource(uri, _OBSEL_TYPE, graph) 


    # TODO implement add_parent, remove_parent, create_*


@extend_api
class _ModelElementMixin(ResourceMixin):
    """
    I provide the common pythonic interface to any element of trace models.

    I make the assumption that self._graph is in fact containing the *whole*
    trace model, not just the description of this element, and that its
    identifier is the URI of the trace model. This is consistent with common
    modelling practices, where elements of a model/ontology will usually have
    their URI redirect to the model/ontology itself (directly for # URIs, or
    with 303 for / URIs).
    """
    @property
    def is_attribute_type(self):
        """
        Return True iff this instance represents an attribute type.
        """
        return isinstance(self, AttributeTypeMixin)

    @property
    def is_obsel_type(self):
        """
        Return True iff this instance represents an obsel type.
        """
        return isinstance(self, ObselTypeMixin)

    @property
    def is_relation_type(self):
        """
        Return True iff this instance represents an relation type.
        """
        return isinstance(self, RelationTypeMixin)

    def get_model(self):
        """
        Return the trace model of this element.
        """
        tmodel_uri = self._graph.identifier
        ret = self.make_resource(tmodel_uri)
        return ret
    #

@extend_api
class _ModelTypeMixin(_ModelElementMixin):
    """
    I provide the common pythonic interface to types defined in a trace model.

    Subclasses must override _SUPER_TYPE_PROP
    """
    _SUPER_TYPE_PROP = None

    def iter_subtypes(self, include_indirect=False):
        """
        I list the subtypes of this type from the same model.
        If include_indirect is True, all subtype from the same model are
        listed, including indirect supertypes and this type itself
        """
        if include_indirect:
            return _closure(self, "subtypes")
        else:
            make_resource = self.make_resource
            return ( make_resource(uri) 
                     for uri in self._graph.subjects(self._SUPER_TYPE_PROP) )

    def iter_supertypes(self, include_indirect=False):
        """
        I list the supertypes of this type.
        If include_indirect is True, all supertypes are listed,
        including indirect supertypes and this type itself
        """
        if include_indirect:
            return _closure(self, "supertypes")
        else:
            make_resource = self.make_resource
            return ( make_resource(uri)
                     for uri in self._graph.objects(self._SUPER_TYPE_PROP) )

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
    #

@extend_api
class AttributeTypeMixin(_ModelElementMixin):
    """
    I provide the pythonic interface to an attribute type.
    """
    def get_obsel_type(self):
        """
        I hold the obsel type containing this attribute, or None.
        """
        uri = self._graph.value(self.uri, _HAS_AOBSELTYPE)
        if uri is None:
            return None
        else:
            return self.make_resource(uri)

    def get_data_type(self):
        """
        I hold the data type allowed for this attribute, or None (any).

        Returns the type as a URIRef
        """
        return self._graph.value(self.uri, _HAS_ADATATYPE)

    # TODO implement set_obsel_type, set_data_type

@extend_api
class ObselTypeMixin(_ModelTypeMixin):
    """
    I provide the pythonic interface to an obsel type.
    """
    #pylint: disable-msg=R0904

    _SUPER_TYPE_PROP = KTBS.hasSuperObselType

    def iter_attribute_types(self, include_inherited=True):
        """
        I iter over the attribute types allowed for this type.
        """
        make_resource = self.make_resource
        for uri in self._graph.subjects(_HAS_AOBSELTYPE, self.uri):
            yield make_resource(uri)
        if include_inherited:
            for supertype in self.iter_supertypes(True):
                for atype in supertype.iter_attribute_types(False):
                    yield atype                

    def iter_relation_types(self, include_inherited=True):
        """
        I iter over the relation types having this obsel type as origin.
        """
        make_resource = self.make_resource
        for uri in self._graph.subjects(_HAS_RORIGIN, self.uri):
            yield make_resource(uri)
        if include_inherited:
            for supertype in self.iter_supertypes(True):
                for rtype in supertype.iter_relation_types(False):
                    yield rtype                            

    def iter_inverse_relation_types(self, include_inherited=True):
        """
        I iter over the relation types having this obsel type as destination.
        """
        make_resource = self.make_resource
        for uri in self._graph.subjects(_HAS_RDESTINATION, self.uri):
            yield make_resource(uri)
        if include_inherited:
            for supertype in self.iter_supertypes(True):
                for rtype in supertype.iter_inverse_relation_types(False):
                    yield rtype

    # TODO implement add_supertype, remove_supertype, create_*

@extend_api
class RelationTypeMixin(_ModelTypeMixin):
    """
    I provide the pythonic interface to a relation type.
    """
    _SUPER_TYPE_PROP = KTBS.hasSuperRelationType

    def get_origin(self):
        """
        I hold the origin obsel type this relation, or None.
        """
        uri = self._graph.value(self.uri, _HAS_RORIGIN)
        if uri is None:
            return None
        else:
            return self.make_resource(uri)

    def get_destination(self):
        """
        I hold the destination obsel type this relation, or None.
        """
        uri = self._graph.objects(self.uri, _HAS_RDESTINATION)
        if uri is None:
            return None
        else:
            return self.make_resource(uri)

    def iter_all_domains(self):
        """
        I iter over all the domains (direct or inherited) of this relation.
        """
        seen = set()
        for rtype in self.iter_supertypes(True):
            rdomain = rtype.domain
            if rdomain is not None and rdomain not in seen:
                yield rdomain
                seen.add(rdomain)

    def iter_all_ranges(self):
        """
        I iter over all the ranges (direct or inherited) of this relation.
        """
        seen = set()
        for rtype in self.iter_supertypes(True):
            rrange = rtype.range
            if rrange is not None and rrange not in seen:
                yield rrange
                seen.add(rrange)

    # TODO implement add_supertype, remove_supertype, set_*, create_*


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


_ATTR_TYPE = KTBS.AttributeType
_RDF_TYPE = RDF.type
_OBSEL_TYPE = KTBS.ObselType
_REL_TYPE = KTBS.RelationType
_HAS_AOBSELTYPE = KTBS.hasAttributeDomain # should be renamed at some point?
_HAS_ADATATYPE = KTBS.hasAttributeRange # should be renamed at some point?
_HAS_RORIGIN = KTBS.hasRelationDomain # should be renamed at some point?
_HAS_RDESTINATION = KTBS.hasRelationRange # should be renamed at some point?
_HAS_SUPEROTYPE = KTBS.hasSuperObselType
_HAS_SUPERRTYPE = KTBS.hasSuperRelationType
_HAS_UNIT = KTBS.hasUnit
_HAS_PARENT_MODEL = KTBS.hasParentModel
_PREF_LABEL = SKOS.prefLabel
