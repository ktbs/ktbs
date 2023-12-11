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
from unittest import skip
from pytest import raises as assert_raises

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
        assert relation_type.uri == generated_uri
        if self.target is self.model:
            assert relation_type.origins == []
        else:
            assert relation_type.origins == [self.target]
        assert relation_type.destinations == []
        assert relation_type.supertypes == []
        assert relation_type.subtypes == []
        assert self.target.relation_types == [relation_type]
        assert self.model.relation_types == [relation_type]

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#RelTypeWithID")

    def test_create_relation_type_with_label(self):
        relation_type = \
            self.target.create_relation_type(label="Test relation type")
        assert self.target.relation_types == [relation_type]
        assert self.model.relation_types == [relation_type]

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
        assert relation_type.uri == generated_uri
        assert self.target.relation_types == [relation_type]
        assert self.model.relation_types == [relation_type]

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#RelTypeWithIDAndLabel")

    def test_create_relation_type_with_one_supertype(self):
        supertype = self.target.create_relation_type(id="#SuperRelType")
        relation_type = self.target.create_relation_type(
                                     id="#RelTypeWithOneSupertype",
                                     supertypes=[supertype.uri],
                                     label="Relation type with one super type")
        assert set(self.target.relation_types) == \
            set([relation_type, supertype])
        assert set(self.model.relation_types) == \
            set([relation_type, supertype])
        assert relation_type.supertypes == [supertype]
        assert supertype.subtypes == [relation_type]

    def test_create_relation_type_with_two_supertypes(self):
        supertype1 = self.target.create_relation_type(id="#SuperRelType1")
        supertype2 = self.target.create_relation_type(id="#SuperRelType2")
        relation_type = self.target.create_relation_type(
                                     id="#RelTypeWithTwoSupertypes",
                                     supertypes=[supertype1.uri,
                                                 supertype2.uri],
                                     label="Relation type with two super types")
        assert set(self.target.relation_types) == \
                         set([relation_type, supertype1, supertype2])
        assert set(self.model.relation_types) == \
                         set([relation_type, supertype1, supertype2])
        assert set(relation_type.supertypes) == \
                         set([supertype1, supertype2])
        assert supertype1.subtypes == [relation_type]
        assert supertype2.subtypes == [relation_type]

    def test_create_relation_type_with_destination(self):
        dest = self.model.create_obsel_type("#ObselTypeWithId")
        reltype = self.target.create_relation_type(id="#RelTypeWithDestination",
                                                   destinations=[dest.uri])
        assert reltype.destinations == [dest]
        assert dest.inverse_relation_types == [reltype]

    ######## add attribute types ########

    def test_create_attribute_type_no_id_no_label(self):
        with assert_raises(ValueError):
            attribute_type = self.target.create_attribute_type()

    def test_create_attribute_type_with_id(self):
        attribute_type = self.target.create_attribute_type(id="#AttTypeWithID")
        generated_uri = URIRef(KTBS_ROOT + "BaseTest/ModelTest#AttTypeWithID")
        assert attribute_type.uri == generated_uri
        if self.target is self.model:
            assert attribute_type.obsel_types == []
        else:
            assert attribute_type.obsel_types == [self.target]
        assert attribute_type.data_types == []
        assert self.target.attribute_types == [attribute_type]
        assert self.model.attribute_types == [attribute_type]

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#AttTypeWithID")

    def test_create_attribute_type_with_label(self):
        attribute_type = \
            self.target.create_attribute_type(label="Test attribute type")
        assert self.target.attribute_types == [attribute_type]
        assert self.model.attribute_types == [attribute_type]

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
        assert attribute_type.uri == generated_uri
        assert self.target.attribute_types == [attribute_type]
        assert self.model.attribute_types == [attribute_type]

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#AttTypeWithIDAndLabel")

    def test_create_attribute_type_with_datatype(self):
        atttype = self.target.create_attribute_type(id="#AttTypeWithDatatype",
                                                    data_types=[XSD.integer])
        assert atttype.data_types == [XSD.integer]

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
        assert self.target.supertypes == []
        supertype1 = self.create_supertype(id="#SuperType1")
        self.target.add_supertype(supertype1)
        assert self.target.supertypes == [supertype1]
        supertype2 = self.create_supertype(id="#SuperType2")
        self.target.add_supertype(supertype2)
        assert set(self.target.supertypes), set([supertype1 == supertype2])
        self.target.remove_supertype(supertype1)
        assert self.target.supertypes == [supertype2]
        self.target.remove_supertype(supertype2)
        assert self.target.supertypes == []

    def test_handle_inherited_obsel_types(self):
        supertype1 = self.create_supertype(id="#SuperType1")
        supertype2 = self.create_supertype(id="#SuperType2",
                                           supertypes=[supertype1])
        self.target.add_supertype(supertype2)
        assert self.target.supertypes == [supertype2]
        assert set(self.target.list_supertypes(True)) == \
            set([self.target, supertype1, supertype2])


class TestKtbsTraceModel(RelAndAttTypeMixin, KtbsTestCase):

    def setup_method(self):
        KtbsTestCase.setup_method(self)
        self.base = self.my_ktbs.create_base(id="BaseTest/", label="Test base")
        self.model = self.base.create_model(id="ModelTest", label="Test model")
        self.target = self.model

    ######## get information ########

    def test_get_model_uri(self):
        reference_uri = URIRef(KTBS_ROOT + "BaseTest/ModelTest")
        assert self.model.uri == reference_uri

    @skip("Resource.sync_status is not yet implemented")
    def test_get_sync_status(test):
        assert self.model.sync_status == "ok"

    def test_get_readonly(self):
        assert self.model.readonly == False

    def test_get_model_label(self):
        assert self.model.label == "Test model"

    def test_get_base(self):
        base = self.model.base
        assert base == self.base

    def test_get_unit(self):
        assert self.model.unit == KTBS.millisecond

    def test_list_parents(self):
        assert self.model.parents == []

    def test_list_obsel_types(self):
        assert self.model.obsel_types == []

    def test_list_attribute_types(self):
        assert self.model.attribute_types == []

    def test_list_relation_types(self):
        assert self.model.relation_types == []

    ######## set information ########

    def test_set_model_label(self):
        self.model.set_label("New model label")
        assert self.model.label == "New model label"

    def test_reset_model_label(self):
        self.model.set_label("New model label")
        self.model.reset_label()
        assert self.model.label == "ModelTest"

    def test_set_unit(self):
        self.model.set_unit(KTBS.second)
        assert self.model.unit == KTBS.second

    def test_add_del_parents(self):
        assert self.model.parents == []
        parent_model = self.base.create_model()
        self.model.add_parent(parent_model.uri)
        assert self.model.parents == [parent_model]
        self.model.remove_parent(parent_model.uri)
        assert self.model.parents == []

    ######## add obsel types ########

    def test_create_obsel_type_no_id_no_label(self):
        with assert_raises(ValueError):
            obsel_type = self.model.create_obsel_type()

    def test_create_obsel_type_with_id(self):
        obsel_type = self.model.create_obsel_type(id="#ObselTypeWithID")
        generated_uri = URIRef(KTBS_ROOT +
                               "BaseTest/ModelTest#ObselTypeWithID")
        assert obsel_type.uri == generated_uri
        assert self.model.obsel_types == [obsel_type]

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#ObselTypeWithID")

    def test_create_obsel_type_with_label(self):
        obsel_type = self.model.create_obsel_type(label="Test obsel type")
        assert self.model.obsel_types == [obsel_type]

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id=obsel_type.uri)

    def test_create_obsel_type_with_id_and_label(self):
        obsel_type = self.model.create_obsel_type(id="#ObselTypeWithIDAndLabel",
                                                  label="Test obsel type")
        generated_uri = URIRef(KTBS_ROOT +
                               "BaseTest/ModelTest#ObselTypeWithIDAndLabel")
        assert obsel_type.uri == generated_uri
        assert self.model.obsel_types == [obsel_type]

        # check duplicate URI
        with assert_raises(InvalidDataError):
            self.base.create_model(id="#ObselTypeWithIDAndLabel")

    def test_create_obsel_type_with_one_supertype(self):
        supertype = self.model.create_obsel_type(id="#SuperObselType")
        obsel_type = self.model.create_obsel_type(
                                     id="#ObselTypeWithOneSupertype",
                                     supertypes=[supertype.uri],
                                     label="Obsel type with one super type")
        assert obsel_type.supertypes == [supertype]
        assert set(self.model.obsel_types), set([obsel_type == supertype])

    def test_create_obsel_type_with_two_supertypes(self):
        supertype1 = self.model.create_obsel_type(id="#SuperObselType1")
        supertype2 = self.model.create_obsel_type(id="#SuperObselType2")
        obsel_type = self.model.create_obsel_type(
                                     id="#ObselTypeWithTwoSupertypes",
                                     supertypes=[supertype1.uri,
                                                 supertype2.uri],
                                     label="Obsel type with two super types")
        assert set(obsel_type.supertypes), set([supertype1 == supertype2])
        assert set(self.model.obsel_types) == \
            set([obsel_type, supertype1, supertype2])

    ######## add relation types ########

    # mostly inherited from RelAndAttTypeMixin

    def test_create_relation_type_with_origin(self):
        orig = self.model.create_obsel_type("#ObselTypeWithId")
        relation_type = self.model.create_relation_type(id="#RelTypeWithOrigin",
                                                        origins=[orig.uri])
        assert orig.relation_types == [relation_type]

    def test_create_relation_type_with_everything(self):
        orig = self.model.create_obsel_type("#ObselTypeWithId1")
        dest = self.model.create_obsel_type("#ObselTypeWithId2")
        relation_type = self.model.create_relation_type(id="#RelTypeWithOrigin",
                                                        origins=[orig.uri],
                                                        destinations=[dest.uri])
        assert orig.relation_types == [relation_type]
        assert dest.inverse_relation_types == [relation_type]

    ######## add attribute types ########

    # mostly inherited from RelAndAttTypeMixin

    def test_create_attribute_type_with_obsel_type(self):
        orig = self.model.create_obsel_type("#ObselTypeWithId")
        attribute_type = \
            self.model.create_attribute_type(id="#AttTypeWithObselType",
                                             obsel_types=[orig.uri])
        assert orig.attribute_types == [attribute_type]

    def test_create_attribute_type_with_everything(self):
        orig = self.model.create_obsel_type("#ObselTypeWithId1")
        dest = self.model.create_obsel_type("#ObselTypeWithId2")
        attribute_type = \
            self.model.create_attribute_type(id="#AttTypeWithObsel_Type",
                                             obsel_types=[orig.uri],
                                             data_types=[XSD.integer])
        assert orig.attribute_types == [attribute_type]

    ######## remove ########

    def test_remove_model(self):
        model_uri = self.model.get_uri()
        self.model.remove()
        assert self.base.models == []
        assert self.base.get(model_uri) == None

    def test_remove_obsel_type(self):
        obsel_type = self.model.create_obsel_type(id="#ObselTypeTest")
        obsel_type_uri = obsel_type.uri
        assert self.model.get(obsel_type_uri) == obsel_type

        obsel_type.remove()
        assert self.model.get(obsel_type_uri) == None
        assert self.model.obsel_types == []

    def test_remove_relation_type(self):
        relation_type = self.model.create_relation_type(id="#RelationTypeTest")
        relation_type_uri = relation_type.uri
        assert self.model.get(relation_type_uri) == relation_type

        relation_type.remove()
        assert self.model.get(relation_type_uri) == None
        assert self.model.relation_types == []

    def test_remove_attribute_type(self):
        attribute_type = \
            self.model.create_attribute_type(id="#AttributeTypeTest")
        attribute_type_uri = attribute_type.uri
        assert self.model.get(attribute_type_uri) == attribute_type

        attribute_type.remove()
        assert self.model.get(attribute_type_uri) == None
        assert self.model.attribute_types == []


class TestKtbsObselType(RelAndAttTypeMixin, SuperTypeMixin, KtbsTestCase):

    def setup_method(self):
        KtbsTestCase.setup_method(self)
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

    def setup_method(self):
        KtbsTestCase.setup_method(self)
        self.base = self.my_ktbs.create_base(id="BaseTest/", label="Test base")
        self.model = self.base.create_model(id="ModelTest", label="Test model")
        self.otype1 = self.model.create_obsel_type(id="#ObselType1")
        self.otype2 = self.model.create_obsel_type(id="#ObselType2")
        self.rtype = self.model.create_relation_type(id="#RelationTypeTest",
                                                     origins=[self.otype1],
                                                     destinations=[self.otype2],
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
                                                   origins=[otype1a],
                                                   destinations=[otype2a],
                                                   supertypes=[self.rtype],
                                                   )
        assert rsubtypea.origins == [otype1a]
        assert rsubtypea.destinations == [otype2a]
        assert rsubtypea.supertypes == [self.rtype]
        assert set(rsubtypea.all_origins), set([self.otype1 == otype1a])
        assert set(rsubtypea.all_destinations), set([self.otype2 == otype2a])
        assert rsubtypea.list_supertypes(True), [rsubtypea == self.rtype]


        otype1b = self.model.create_obsel_type(id="#ObselType1b",
                                               supertypes=[otype1a])
        otype2b = self.model.create_obsel_type(id="#ObselType2b",
                                               supertypes=[otype2a])
        rsubtypeb = self.model.create_relation_type(id="#RelationSubtypeB",
                                                   origins=[otype1b],
                                                   destinations=[otype2b],
                                                   supertypes=[rsubtypea],
                                                   )
        assert rsubtypeb.origins == [otype1b]
        assert rsubtypeb.destinations == [otype2b]
        assert rsubtypeb.supertypes == [rsubtypea]
        assert set(rsubtypeb.all_origins), set([self.otype1, otype1a == otype1b])
        assert set(rsubtypeb.all_destinations) == \
            set([self.otype2, otype2a, otype2b])
        assert rsubtypeb.list_supertypes(True), [rsubtypeb, rsubtypea == self.rtype]
