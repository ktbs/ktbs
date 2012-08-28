#!/usr/bin/env python
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
Nose unit-testing for the kTBS model client API.
"""
from unittest import TestCase, skip
from nose.tools import eq_, assert_raises

from rdflib import URIRef, XSD

from rdfrest.exceptions import InvalidDataError

from ktbs.namespace import KTBS

from .test_ktbs_engine import KtbsTestCase

KTBS_ROOT = "http://localhost:12345/"

class RelAndAttTypeMixin:
    # common methods for testing TraceModel and ObselType;
    # I rely on self.target being either the model or the obsel type,
    # and self.model being the model

    ######## add relation types ########

    def test_create_relation_type_no_id_no_label(self):
        with assert_raises(ValueError):
            relation_type = self.target.create_relation_type()

    def test_create_relation_type_with_id(self):
        relation_type = self.target.create_relation_type(id="#RelTypeWithID")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/ModelTest#RelTypeWithID")
        eq_(relation_type.uri, generated_uri)
        if self.target is self.model:
            eq_(relation_type.origin, None)
        else:
            eq_(relation_type.origin, self.target)
        eq_(relation_type.destination, None)
        eq_(relation_type.supertypes, [])
        eq_(relation_type.subtypes, [])
        eq_(self.target.relation_types, [relation_type])
        eq_(self.model.relation_types, [relation_type])

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#RelTypeWithID")

    def test_create_relation_type_with_label(self):
        relation_type = \
            self.target.create_relation_type(label="Test relation type")
        eq_(self.target.relation_types, [relation_type])
        eq_(self.model.relation_types, [relation_type])

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id=relation_type.uri)

    def test_create_relation_type_with_id_and_label(self):
        relation_type = \
            self.target.create_relation_type(id="#RelTypeWithIDAndLabel", 
                                            label="Test relation type")
        generated_uri = \
            URIRef(KTBS_ROOT + 
                               "BaseTest/ModelTest#RelTypeWithIDAndLabel")
        eq_(relation_type.uri, generated_uri)
        eq_(self.target.relation_types, [relation_type])
        eq_(self.model.relation_types, [relation_type])

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#RelTypeWithIDAndLabel")

    def test_create_relation_type_with_one_supertype(self):
        supertype = self.target.create_relation_type(id="#SuperRelType")
        relation_type = self.target.create_relation_type(
                                     id="#RelTypeWithOneSupertype", 
                                     supertypes=[supertype.uri],
                                     label="Relation type with one super type")
        eq_(set(self.target.relation_types),
            set([relation_type, supertype]))
        eq_(set(self.model.relation_types),
            set([relation_type, supertype]))
        eq_(relation_type.supertypes, [supertype])
        eq_(supertype.subtypes, [relation_type])

    def test_create_relation_type_with_two_supertypes(self):
        supertype1 = self.target.create_relation_type(id="#SuperRelType1")
        supertype2 = self.target.create_relation_type(id="#SuperRelType2")
        relation_type = self.target.create_relation_type(
                                     id="#RelTypeWithTwoSupertypes", 
                                     supertypes=[supertype1.uri,
                                                 supertype2.uri],
                                     label="Relation type with two super types")
        eq_(set(self.target.relation_types),
            set([relation_type, supertype1, supertype2]))
        eq_(set(self.model.relation_types),
            set([relation_type, supertype1, supertype2]))
        eq_(set(relation_type.supertypes),
            set([supertype1, supertype2]))
        eq_(supertype1.subtypes, [relation_type])
        eq_(supertype2.subtypes, [relation_type])

    def test_create_relation_type_with_destination(self):
        dest = self.model.create_obsel_type("#ObselTypeWithId")
        reltype = self.target.create_relation_type(id="#RelTypeWithDestination",
                                                   destination=dest.uri)
        eq_(reltype.destination, dest)
        eq_(dest.inverse_relation_types, [reltype])

    ######## add attribute types ########

    def test_create_attribute_type_no_id_no_label(self):
        with assert_raises(ValueError):
            attribute_type = self.target.create_attribute_type()

    def test_create_attribute_type_with_id(self):
        attribute_type = self.target.create_attribute_type(id="#AttTypeWithID")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/ModelTest#AttTypeWithID")
        eq_(attribute_type.uri, generated_uri)
        if self.target is self.model:
            eq_(attribute_type.obsel_type, None)
        else:
            eq_(attribute_type.obsel_type, self.target)
        eq_(attribute_type.data_type, None)
        eq_(self.target.attribute_types, [attribute_type])
        eq_(self.model.attribute_types, [attribute_type])

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#AttTypeWithID")

    def test_create_attribute_type_with_label(self):
        attribute_type = \
            self.target.create_attribute_type(label="Test attribute type")
        eq_(self.target.attribute_types, [attribute_type])
        eq_(self.model.attribute_types, [attribute_type])

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id=attribute_type.uri)

    def test_create_attribute_type_with_id_and_label(self):
        attribute_type = \
            self.target.create_attribute_type(id="#AttTypeWithIDAndLabel", 
                                            label="Test attribute type")
        generated_uri = \
            URIRef(KTBS_ROOT + 
                               "BaseTest/ModelTest#AttTypeWithIDAndLabel")
        eq_(attribute_type.uri, generated_uri)
        eq_(self.target.attribute_types, [attribute_type])
        eq_(self.model.attribute_types, [attribute_type])

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#AttTypeWithIDAndLabel")

    def test_create_attribute_type_with_datatype(self):
        atttype = self.target.create_attribute_type(id="#AttTypeWithDatatype",
                                                    data_type=XSD.integer)
        eq_(atttype.data_type, XSD.integer)

    @skip("list datatypes not supported yet")
    def test_create_attribute_type_with_list_value(self):
        atttype = self.target.create_attribute_type(id="#AttTypeWithDatatype",
                                                    data_type=XSD.integer)
        # TODO test relevant properties of attypes

class SuperTypeMixin:
    # common methods for testing ObselType and RelationType;
    # I rely on self.target being either obsel- or relation-type,
    # and self.create_supertype being the model method for creating other types

    def test_handle_super_obsel_types(self):
        eq_(self.target.supertypes, [])
        supertype1 = self.create_supertype(id="#SuperType1")
        self.target.add_supertype(supertype1)
        eq_(self.target.supertypes, [supertype1])
        supertype2 = self.create_supertype(id="#SuperType2")
        self.target.add_supertype(supertype2)
        eq_(set(self.target.supertypes), set([supertype1, supertype2]))
        self.target.remove_supertype(supertype1)
        eq_(self.target.supertypes, [supertype2])
        self.target.remove_supertype(supertype2)
        eq_(self.target.supertypes, [])

    def test_handle_inherited_obsel_types(self):
        supertype1 = self.create_supertype(id="#SuperType1")
        supertype2 = self.create_supertype(id="#SuperType2",
                                                  supertypes=[supertype1])
        self.target.add_supertype(supertype2)
        eq_(self.target.supertypes, [supertype2])
        eq_(set(self.target.list_supertypes(True)),
            set([self.target, supertype1, supertype2]))


class TestKtbsTraceModel(RelAndAttTypeMixin, KtbsTestCase):

    def setUp(self):
        KtbsTestCase.setUp(self)
        self.base = self.my_ktbs.create_base(id="BaseTest/", label="Test base")
        self.model = self.base.create_model(id="ModelTest", label="Test model")
        self.target = self.model

    ######## get information ########

    def test_get_model_uri(self):
        reference_uri = URIRef(KTBS_ROOT + "BaseTest/ModelTest")
        eq_(self.model.uri, reference_uri)

    @skip("Resource.sync_status is not yet implemented")
    def test_get_sync_status(test):
        eq_(self.model.sync_status, "ok")

    def test_get_readonly(self):
        eq_(self.model.readonly, False)

    def test_get_model_label(self):
        eq_(self.model.label, "Test model")

    def test_get_base(self):
        base = self.model.base
        eq_(base, self.base)

    def test_get_unit(self):
        eq_(self.model.unit, KTBS.millisecond)

    def test_list_parents(self):
        eq_(self.model.parents, [])

    def test_list_obsel_types(self):
        eq_(self.model.obsel_types, [])

    def test_list_attribute_types(self):
        eq_(self.model.attribute_types, [])

    def test_list_relation_types(self):
        eq_(self.model.relation_types, [])

    ######## set information ########

    def test_set_model_label(self):
        self.model.set_label("New model label")
        eq_(self.model.label, "New model label")

    def test_reset_model_label(self):
        self.model.set_label("New model label")
        self.model.reset_label()
        eq_(self.model.label, "ModelTest")

    def test_set_unit(self):
        self.model.set_unit(KTBS.second)
        eq_(self.model.unit, KTBS.second)

    def test_add_del_parents(self):
        eq_(self.model.parents, [])
        parent_model = self.base.create_model()
        self.model.add_parent(parent_model.uri)
        eq_(self.model.parents, [parent_model])
        self.model.remove_parent(parent_model.uri)
        eq_(self.model.parents, [])

    ######## add obsel types ########

    def test_create_obsel_type_no_id_no_label(self):
        with assert_raises(ValueError):
            obsel_type = self.model.create_obsel_type()

    def test_create_obsel_type_with_id(self):
        obsel_type = self.model.create_obsel_type(id="#ObselTypeWithID")
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelTest#ObselTypeWithID")
        eq_(obsel_type.uri, generated_uri)
        eq_(self.model.obsel_types, [obsel_type])

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#ObselTypeWithID")

    def test_create_obsel_type_with_label(self):
        obsel_type = self.model.create_obsel_type(label="Test obsel type")
        eq_(self.model.obsel_types, [obsel_type])

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id=obsel_type.uri)

    def test_create_obsel_type_with_id_and_label(self):
        obsel_type = self.model.create_obsel_type(id="#ObselTypeWithIDAndLabel", 
                                                  label="Test obsel type")
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelTest#ObselTypeWithIDAndLabel")
        eq_(obsel_type.uri, generated_uri)
        eq_(self.model.obsel_types, [obsel_type])

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#ObselTypeWithIDAndLabel")

    def test_create_obsel_type_with_one_supertype(self):
        supertype = self.model.create_obsel_type(id="#SuperObselType")
        obsel_type = self.model.create_obsel_type(
                                     id="#ObselTypeWithOneSupertype", 
                                     supertypes=[supertype.uri],
                                     label="Obsel type with one super type")
        eq_(obsel_type.supertypes, [supertype])
        eq_(set(self.model.obsel_types), set([obsel_type, supertype]))

    def test_create_obsel_type_with_two_supertypes(self):
        supertype1 = self.model.create_obsel_type(id="#SuperObselType1")
        supertype2 = self.model.create_obsel_type(id="#SuperObselType2")
        obsel_type = self.model.create_obsel_type(
                                     id="#ObselTypeWithTwoSupertypes", 
                                     supertypes=[supertype1.uri,
                                                 supertype2.uri],
                                     label="Obsel type with two super types")
        eq_(set(obsel_type.supertypes), set([supertype1, supertype2]))
        eq_(set(self.model.obsel_types),
            set([obsel_type, supertype1, supertype2]))

    ######## add relation types ########

    # mostly inherited from RelAndAttTypeMixin

    def test_create_relation_type_with_origin(self):
        orig = self.model.create_obsel_type("#ObselTypeWithId")
        relation_type = self.model.create_relation_type(id="#RelTypeWithOrigin",
                                                        origin=orig.uri)
        eq_(orig.relation_types, [relation_type])

    def test_create_relation_type_with_everything(self):
        orig = self.model.create_obsel_type("#ObselTypeWithId1")
        dest = self.model.create_obsel_type("#ObselTypeWithId2")
        relation_type = self.model.create_relation_type(id="#RelTypeWithOrigin",
                                                        origin=orig.uri,
                                                        destination=dest.uri)
        eq_(orig.relation_types, [relation_type])
        eq_(dest.inverse_relation_types, [relation_type])

    ######## add attribute types ########

    # mostly inherited from RelAndAttTypeMixin

    def test_create_attribute_type_with_obsel_type(self):
        orig = self.model.create_obsel_type("#ObselTypeWithId")
        attribute_type = \
            self.model.create_attribute_type(id="#AttTypeWithObselType",
                                             obsel_type=orig.uri)
        eq_(orig.attribute_types, [attribute_type])

    def test_create_attribute_type_with_everything(self):
        orig = self.model.create_obsel_type("#ObselTypeWithId1")
        dest = self.model.create_obsel_type("#ObselTypeWithId2")
        attribute_type = \
            self.model.create_attribute_type(id="#AttTypeWithObsel_Type",
                                             obsel_type=orig.uri,
                                             data_type=XSD.integer)
        eq_(orig.attribute_types, [attribute_type])

    ######## remove ########
    
    def test_remove_model(self):
        model_uri = self.model.get_uri()
        self.model.remove()
        eq_(self.base.models, [])
        eq_(self.base.get(model_uri), None)

    def test_remove_obsel_type(self):
        obsel_type = self.model.create_obsel_type(id="#ObselTypeTest")
        obsel_type_uri = obsel_type.uri
        eq_(self.model.get(obsel_type_uri), obsel_type)

        obsel_type.remove()
        eq_(self.model.get(obsel_type_uri), None)
        eq_(self.model.obsel_types, [])

    def test_remove_relation_type(self):
        relation_type = self.model.create_relation_type(id="#RelationTypeTest")
        relation_type_uri = relation_type.uri
        eq_(self.model.get(relation_type_uri), relation_type)

        relation_type.remove()
        eq_(self.model.get(relation_type_uri), None)
        eq_(self.model.relation_types, [])

    def test_remove_attribute_type(self):
        attribute_type = \
            self.model.create_attribute_type(id="#AttributeTypeTest")
        attribute_type_uri = attribute_type.uri
        eq_(self.model.get(attribute_type_uri), attribute_type)

        attribute_type.remove()
        eq_(self.model.get(attribute_type_uri), None)
        eq_(self.model.attribute_types, [])


class TestKtbsObselType(RelAndAttTypeMixin, SuperTypeMixin, KtbsTestCase):

    def setUp(self):
        KtbsTestCase.setUp(self)
        self.base = self.my_ktbs.create_base(id="BaseTest/", label="Test base")
        self.model = self.base.create_model(id="ModelTest", label="Test model")
        self.otype = self.model.create_obsel_type(id="#ObselTypeTest")
        self.target = self.otype
        self.create_supertype = self.model.create_obsel_type

    ######## add relation types ########

    # inherited from RelAndAttTypeMixin

    ######## add attribute types ########

    # inherited from RelAndAttTypeMixin

    ######## handle supertypes ########

    # inherited from SuperTypeMixin


class TestKtbsRelationType(SuperTypeMixin, KtbsTestCase):

    def setUp(self):
        KtbsTestCase.setUp(self)
        self.base = self.my_ktbs.create_base(id="BaseTest/", label="Test base")
        self.model = self.base.create_model(id="ModelTest", label="Test model")
        self.otype1 = self.model.create_obsel_type(id="#ObselType1")
        self.otype2 = self.model.create_obsel_type(id="#ObselType2")
        self.rtype = self.model.create_relation_type(id="#RelationTypeTest",
                                                     origin=self.otype1,
                                                     destination=self.otype2,
                                                     )
        self.target = self.rtype
        self.create_supertype = self.model.create_relation_type

    ######## handle supertypes and inheritance ########

    # mostly inherited from RelAndAttTypeMixin

    def test_inherited_origin(self):
        otype1a = self.model.create_obsel_type(id="#ObselType1a",
                                               supertypes=[self.otype1])
        otype2a = self.model.create_obsel_type(id="#ObselType2a",
                                               supertypes=[self.otype2])
        rsubtypea = self.model.create_relation_type(id="#RelationSubtypeA",
                                                   origin=otype1a,
                                                   destination=otype2a,
                                                   supertypes=[self.rtype],
                                                   )
        eq_(rsubtypea.origin, otype1a)
        eq_(rsubtypea.destination, otype2a)
        eq_(rsubtypea.supertypes, [self.rtype])
        eq_(set(rsubtypea.all_origins), set([self.otype1, otype1a]))
        eq_(set(rsubtypea.all_destinations), set([self.otype2, otype2a]))
        eq_(rsubtypea.list_supertypes(True), [rsubtypea, self.rtype])


        otype1b = self.model.create_obsel_type(id="#ObselType1b",
                                               supertypes=[otype1a])
        otype2b = self.model.create_obsel_type(id="#ObselType2b",
                                               supertypes=[otype2a])
        rsubtypeb = self.model.create_relation_type(id="#RelationSubtypeB",
                                                   origin=otype1b,
                                                   destination=otype2b,
                                                   supertypes=[rsubtypea],
                                                   )
        eq_(rsubtypeb.origin, otype1b)
        eq_(rsubtypeb.destination, otype2b)
        eq_(rsubtypeb.supertypes, [rsubtypea])
        eq_(set(rsubtypeb.all_origins), set([self.otype1, otype1a, otype1b]))
        eq_(set(rsubtypeb.all_destinations),
            set([self.otype2, otype2a, otype2b]))
        eq_(rsubtypeb.list_supertypes(True), [rsubtypeb, rsubtypea, self.rtype])
