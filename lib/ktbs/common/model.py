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
from rdflib import RDF

from ktbs.common.base import InBaseMixin
from ktbs.common.resource import ResourceMixin
from ktbs.common.utils import coerce_to_uri, extend_api
from ktbs.namespaces import KTBS

@extend_api
class ModelMixin(InBaseMixin):
    """
    I provide the pythonic interface to a trace model.
    """

    def get(self, uri):
        """
        Return the pythonic instance corresponding to the given uri, or None.

        `uri` can be relative to this Model's URI.

        NB: None if the uri is not found *but also* if it does not identify
        a Model element (ObselType, AttributeType or RelationType).
        """
        uri = coerce_to_uri(uri, self.uri)
        for rdf_type in self.graph.objects(uri, _RDF_TYPE):
            if rdf_type in (_ATTR_TYPE, _OBSEL_TYPE, _REL_TYPE):
                return self.make_resource(uri, rdf_type)
        return None

    def iter_inherited(self):
        """
        I iter over all the models inherited by this model.

        NB: if make_resource fails to instanciate some models, the URI will be
        yielded instead, but this should not happen.
        """
        make_resource = self.make_resource
        for uri in self.graph.objects(self.uri, _INHERITS):
            yield make_resource(uri) or uri

    def iter_own_attribute_types(self):
        """
        I iter over all the attribute types described in this trace model.
        """
        make_resource = self.make_resource
        for uri in self.graph.subjects(_RDF_TYPE, _ATTR_TYPE):
            yield make_resource(uri)

    def iter_own_obsel_types(self):
        """
        I iter over all the obsel types described in this trace model.
        """
        make_resource = self.make_resource
        for uri in self.graph.subjects(_RDF_TYPE, _OBSEL_TYPE):
            yield make_resource(uri)

    def iter_own_relation_types(self):
        """
        I iter over all the relation types described in this trace model.
        """
        make_resource = self.make_resource
        for uri in self.graph.subjects(_RDF_TYPE, _REL_TYPE):
            yield make_resource(uri)

    def iter_all_attribute_types(self):
        """
        I iter over all the attribute types inherited by this trace model.
        """
        ret = set(self.iter_own_attribute_types())
        for inherited in self.iter_inherited():
            set.add(inherited.iter_all_attribute_types())
        return iter(ret)

    def iter_all_obsel_types(self):
        """
        I iter over all the obsel types inherited by this trace model.
        """
        ret = set(self.iter_own_obsel_types())
        for inherited in self.iter_inherited():
            set.add(inherited.iter_all_attribute_types())
        return iter(ret)

    def iter_all_relation_types(self):
        """
        I iter over all the attribute types inherited by this trace model.
        """
        ret = set(self.iter_own_relation_types())
        for inherited in self.iter_inherited():
            set.add(inherited.iter_all_attribute_types())
        return iter(ret)


@extend_api
class _ModelElementMixin(ResourceMixin):
    """
    I provide the common pythonic interface to any element of trace models.

    I make the assumption that self.graph is in fact containing the *whole*
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
        tmodel_uri = self.graph.identifier
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

    def iter_all_subtypes(self):
        """
        I iter over all the subtypes of this type (included itself and
        inherited ones).
        """
        return _closure(self, "own_subtypes")

    def iter_all_supertypes(self):
        """
        I iter over all the supertypes of this type (included itself and
        inherited ones).
        """
        return _closure(self, "own_supertypes")

    def iter_own_subtypes(self):
        """
        I iter over the direct subtypes of this type.
        """
        make_resource = self.make_resource
        for uri in self.graph.subjects(self._SUPER_TYPE_PROP):
            yield make_resource(uri)

    def iter_own_supertypes(self):
        """
        I iter over the direct supertypes of this type.
        """
        make_resource = self.make_resource
        for uri in self.graph.objects(self._SUPER_TYPE_PROP):
            yield make_resource(uri)

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
        mine = set(self.iter_all_supertypes())
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
    def get_domain(self):
        """
        I hold the direct domain of this attribute, or None.
        """
        uri = next(self.graph.objects(self.uri, _HAS_ADOMAIN), None)
        if uri is None:
            return None
        else:
            return self.make_resource(uri)

    def get_range(self):
        """
        I hold the direct range of this attribute, or None.

        Returns the type as a URIRef
        """
        return next(self.graph.object(self.uri, _HAS_ARANGE), None)
    #

@extend_api
class ObselTypeMixin(_ModelTypeMixin):
    """
    I provide the pythonic interface to an obsel type.
    """
    #pylint: disable-msg=R0904

    _SUPER_TYPE_PROP = KTBS.hasSuperObselType

    def iter_own_attributes(self):
        """
        I iter over the attributes directly allowed for this type.
        """
        make_resource = self.make_resource
        for uri in self.graph.subjects(_HAS_ADOMAIN, self.uri):
            yield make_resource(uri)

    def iter_own_relations(self):
        """
        I iter over the relations directly allowing this type as domain.
        """
        make_resource = self.make_resource
        for uri in self.graph.subjects(_HAS_RDOMAIN, self.uri):
            yield make_resource(uri)

    def iter_own_inverse_relations(self):
        """
        I iter over the relations directly allowing this type as range.
        """
        make_resource = self.make_resource
        for uri in self.graph.subjects(_HAS_RRANGE, self.uri):
            yield make_resource(uri)

    def iter_all_attributes(self):
        """
        I iter over all the attributes allowed for this type.
        """
        seen = set()
        for typ in self.iter_all_supertypes():
            for attr in typ.attributes:
                if attr not in seen:
                    yield attr
                    seen.add(attr)

    def iter_all_relations(self):
        """
        I iter over all the relations allowing this type as domain.
        """
        seen = set()
        for typ in self.iter_all_supertypes():
            for rel in typ.own_relations:
                if rel not in seen:
                    yield rel
                    seen.add(rel)
                    for rel2 in rel.all_subtypes:
                        if rel2 not in seen:
                            if self.matches(*rel2.all_domains):
                                yield rel2
                                seen.add(rel2)

    def iter_all_inverse_relations(self):
        """
        I iter over all the relations allowing this type as range.
        """
        seen = set()
        for typ in self.iter_all_supertypes():
            for rel in typ.inverse_relations:
                if rel not in seen:
                    yield rel
                    seen.add(rel)
                    for rel2 in rel.all_subtypes:
                        if rel2 not in seen:
                            if self.matches(*rel2.all_ranges):
                                yield rel2
                                seen.add(rel2)

    #

@extend_api
class RelationTypeMixin(_ModelTypeMixin):
    """
    I provide the pythonic interface to a relation type.
    """
    _SUPER_TYPE_PROP = KTBS.hasSuperRelationType

    def get_domain(self):
        """
        I hold the direct domain of this relation, or None.
        """
        uri = next(self.graph.objects(self.uri, _HAS_RDOMAIN), None)
        if uri is None:
            return None
        else:
            return self.make_resource(uri)

    def get_range(self):
        """
        I hold the direct range of this relation, or None.
        """
        uri = next(self.get_object(self.uri, _HAS_RRANGE), None)
        if uri is None:
            return None
        else:
            return self.make_resource(uri)

    def iter_all_domains(self):
        """
        I iter over all the domains (direct or inherited) of this relation.
        """
        seen = set()
        for rtype in self.iter_all_supertypes():
            rdomain = rtype.domain
            if rdomain is not None and rdomain not in seen:
                yield rdomain
                seen.add(rdomain)

    def iter_all_ranges(self):
        """
        I iter over all the ranges (direct or inherited) of this relation.
        """
        seen = set()
        for rtype in self.iter_all_supertypes():
            rrange = rtype.range
            if rrange is not None and rrange not in seen:
                yield rrange
                seen.add(rrange)
    #


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
_HAS_ADOMAIN = KTBS.hasAttributeDomain
_HAS_ARANGE = KTBS.hasAttributeRange
_HAS_RDOMAIN = KTBS.hasRelationDomain
_HAS_RRANGE = KTBS.hasRelationRange
_INHERITS = KTBS.inheritsModel
