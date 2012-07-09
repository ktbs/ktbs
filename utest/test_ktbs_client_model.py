#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/silex/2009/ktbs>
#    Copyright (C) 2012 Françoise Conil <fconil@liris.cnrs.fr> / SILEX
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
from nose.tools import raises

from os.path import abspath, dirname, join
from subprocess import Popen, PIPE

from rdflib import URIRef, XSD

from ktbs.namespaces import KTBS

from ktbs.client.root import KtbsRoot

KTBS_ROOT = "http://localhost:8001/"

class TestKtbsClientModelGetGeneralInformation(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelTest", label="Test model")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_get_model_uri(self):
        reference_uri = URIRef(KTBS_ROOT + "BaseTest/ModelTest")
        assert self.model.get_uri() == reference_uri

    @skip("Resource.get_sync_status() is not yet implemented")
    def test_get_sync_status(test):
        assert self.model.get_sync_status() == "ok"

    def test_get_readonly(self):
        assert self.model.get_readonly() == False

    def test_get_model_label(self):
        assert self.model.get_label() == "Test model"

    def test_get_base(self):
        base = self.model.get_base()
        assert base.get_uri() == self.base.get_uri()

    def test_get_unit(self):
        assert self.model.get_unit() == "ms"

    def test_list_parents(self):
        lpm = self.model.list_parents()
        assert len(lpm) == 0

    def test_list_obsel_types(self):
        lot = self.model.list_obsel_types()
        assert len(lot) == 0

    def test_list_attribute_types(self):
        lat = self.model.list_attribute_types()
        assert len(lat) == 0

    def test_list_relation_types(self):
        lot = self.model.list_relation_types()
        assert len(lot) == 0

class TestKtbsClientModelSetInformation(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelTest", label="Test model")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_set_model_label(self):
        self.model.set_label("New model label")
        assert self.model.get_label() == "New model label"

    @skip("Resource.reset_label() is not yet implemented")
    def test_reset_model_label(self):
        self.model.set_label("New model label")
        self.model.reset_label()
        assert self.model.get_label() == "Test model"

    @skip("ModelMixin.set_unit() does not work : 403 Forbidden")
    def test_set_unit(self):
        unit = "s"
        self.model.set_unit(unit)
        assert self.model.get_unit() == unit

class TestKtbsClientModelAddParents(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.base_model = cls.base.create_model(id="BaseModel", label="Base model")
        cls.model = cls.base.create_model(id="ModelWithID", label="Test model")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_add_parents(self):
        self.model.add_parent(self.base_model.get_uri())
        lpm = self.model.list_parents()
        assert len(lpm) == 1

class TestKtbsClientModelRemoveParents(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.base_model = cls.base.create_model(id="BaseModel", label="Base model")
        cls.model = cls.base.create_model(id="ModelWithID", label="Test model")
        cls.model.add_parent(cls.base_model.get_uri())

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_remove_parents(self):
        self.model.remove_parent(self.base_model.get_uri())
        lpm = self.model.list_parents()
        assert len(lpm) == 0

class TestKtbsClientModelAddObselTypes(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelWithID", label="Test model")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    @raises(ValueError)
    def test_create_obsel_type_no_id_no_label(self):
        obsel_type = self.model.create_obsel_type()

    def test_create_obsel_type_with_id(self):
        obsel_type = self.model.create_obsel_type(id="#ObselTypeWithID")
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelWithID#ObselTypeWithID")
        assert obsel_type.get_uri() == generated_uri

    def test_create_obsel_type_with_label(self):
        obsel_type = self.model.create_obsel_type(label="Test obsel type")
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelWithID#test-obsel-type")
        assert obsel_type.get_uri() == generated_uri

    def test_create_obsel_type_with_id_and_label(self):
        obsel_type = self.model.create_obsel_type(id="#ObselTypeWithIDAndLabel", 
                                                  label="Test obsel type")
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelWithID#ObselTypeWithIDAndLabel")
        assert obsel_type.get_uri() == generated_uri

class TestKtbsClientModelObselTypeWithSuperType(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelWithID", label="Test model")
        cls.super_obsel_type_1 = cls.model.create_obsel_type(
                                          id="#ObselSuperType1",
                                          label="Obsel Super Type 1")
        cls.super_obsel_type_2 = cls.model.create_obsel_type(
                                          id="#ObselSuperType2",
                                          label="Obsel Super Type 2")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_create_obsel_type_with_one_super_type(self):
        super_types = (self.super_obsel_type_1.get_uri(),)
        obsel_type = self.model.create_obsel_type(
                                     id="#ObselTypeWithOneSupertype", 
                                     supertypes=super_types,
                                     label="Obsel type with one super type")
        assert len(obsel_type.list_supertypes()) == 1

    def test_create_obsel_type_with_one_super_type(self):
        super_types = (self.super_obsel_type_1.get_uri(),
                       self.super_obsel_type_2.get_uri())
        obsel_type = self.model.create_obsel_type(
                                     id="#ObselTypeWithTwoSupertypes", 
                                     supertypes=super_types,
                                     label="Obsel type with two super types")
        assert len(obsel_type.list_supertypes()) == 2

class TestKtbsClientModelRelationTypeWithSuperType(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelWithID", label="Test model")
        cls.obsel_type_1 = cls.model.create_obsel_type(id="#ObselType1", 
                                                       label="Obsel Type 1")
        cls.obsel_type_2 = cls.model.create_obsel_type(id="#ObselType2", 
                                                       label="Obsel Type 2")
        cls.super_relation_type_1 = cls.model.create_relation_type(
                                          id="#RelationSuperType1",
                                          origin=cls.obsel_type_1.get_uri(),
                                          destination=cls.obsel_type_2.get_uri(),
                                          label="Relation Super Type 1")
        cls.super_relation_type_2 = cls.model.create_relation_type(
                                          id="#RelationSuperType2",
                                          origin=cls.obsel_type_1.get_uri(),
                                          destination=cls.obsel_type_2.get_uri(),
                                          label="Relation Super Type 2")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_create_relation_type_with_one_super_type(self):
        super_types = (self.super_relation_type_1.get_uri(),)
        relation_type = self.model.create_relation_type(
                                     id="#RelationTypeWithOneSupertype", 
                                     origin=self.obsel_type_1.get_uri(),
                                     destination=self.obsel_type_2.get_uri(),
                                     supertypes=super_types,
                                     label="Relation type with one super type")
        assert len(relation_type.list_supertypes()) == 1

    def test_create_relation_type_with_one_super_type(self):
        super_types = (self.super_relation_type_1.get_uri(),
                       self.super_relation_type_2.get_uri())
        relation_type = self.model.create_relation_type(
                                     id="#RelationTypeWithTwoSupertypes", 
                                     origin=self.obsel_type_1.get_uri(),
                                     destination=self.obsel_type_2.get_uri(),
                                     supertypes=super_types,
                                     label="Relation type with two super types")
        assert len(relation_type.list_supertypes()) == 2

class TestKtbsClientModelAddAttibuteAndRelationTypes(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelWithID", label="Test model")
        cls.obsel_type_1 = cls.model.create_obsel_type(id="#ObselType1", 
                                                       label="Obsel Type 1")
        cls.obsel_type_2 = cls.model.create_obsel_type(id="#ObselType2", 
                                                       label="Obsel Type 2")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    @raises(ValueError)
    def test_create_attribute_type_no_id_no_label(self):
        attribute_type = self.model.create_attribute_type(
                                         obsel_type=self.obsel_type_1.get_uri())

    def test_create_attribute_type_with_id(self):
        attribute_type = self.model.create_attribute_type(
                                         id="#AttibuteTypeWithID",
                                         obsel_type=self.obsel_type_1.get_uri())
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelWithID#AttibuteTypeWithID")
        assert attribute_type.get_uri() == generated_uri

    def test_create_attribute_type_with_label(self):
        attribute_type = self.model.create_attribute_type(
                                         obsel_type=self.obsel_type_1.get_uri(),
                                         label="Test attribute type")
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelWithID#test-attribute-type")
        assert attribute_type.get_uri() == generated_uri

    def test_create_attribute_type_no_obsel_type(self):
        attribute_type = self.model.create_attribute_type(
                                         id="#AttibuteTypeWithNoObselType")
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelWithID#AttibuteTypeWithNoObselType")
        assert attribute_type.get_uri() == generated_uri

    def test_create_attribute_type_datatype_int(self):
        attribute_type = self.model.create_attribute_type(
                                         id="#AttibuteTypeDataTypeInt",
                                         obsel_type=self.obsel_type_1.get_uri(),
                                         data_type=XSD.integer) 
        assert attribute_type.get_data_type() == XSD.integer

    def test_create_attribute_type_value_is_list(self):
        attribute_type = self.model.create_attribute_type(
                                         id="#AttibuteTypeValueIsList",
                                         obsel_type=self.obsel_type_1.get_uri(),
                                         value_is_list=True)

    @raises(ValueError)
    def test_create_relation_type_no_id_no_label(self):
        relation_type = self.model.create_relation_type(
                                        origin=self.obsel_type_1.get_uri(),
                                        destination=self.obsel_type_2.get_uri())

    def test_create_relation_type_with_id(self):
        relation_type = self.model.create_relation_type(
                                        id="#RelationTypeWithID",
                                        origin=self.obsel_type_1.get_uri(),
                                        destination=self.obsel_type_2.get_uri())
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelWithID#RelationTypeWithID")
        assert relation_type.get_uri() == generated_uri

    def test_create_relation_type_with_label(self):
        relation_type = self.model.create_relation_type(
                                        origin=self.obsel_type_1.get_uri(),
                                        destination=self.obsel_type_2.get_uri(),
                                        label="Test relation type")
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelWithID#test-relation-type")
        assert relation_type.get_uri() == generated_uri

    def test_create_relation_type_no_origin_nor_destination(self):
        relation_type = self.model.create_relation_type(
                                        id="#RelationNoOriginNorDestination")
        generated_uri = URIRef(KTBS_ROOT + 
                          "BaseTest/ModelWithID#RelationNoOriginNorDestination")
        assert relation_type.get_uri() == generated_uri

    def test_create_relation_type_without_origin(self):
        relation_type = self.model.create_relation_type(
                                        id="#RelationTypeWithoutOrigin",
                                        destination=self.obsel_type_2.get_uri())
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelWithID#RelationTypeWithoutOrigin")
        assert relation_type.get_uri() == generated_uri

    def test_create_relation_type_without_destination(self):
        relation_type = self.model.create_relation_type(
                                        id="#RelationTypeWithoutDestination",
                                        origin=self.obsel_type_1.get_uri())
        generated_uri = URIRef(KTBS_ROOT + 
                               "BaseTest/ModelWithID#RelationTypeWithoutDestination")
        assert relation_type.get_uri() == generated_uri

class TestKtbsClientModelGetElementInformation(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelTest", label="Test model")
        cls.obsel_type_1 = cls.model.create_obsel_type(id="#ObselType1", 
                                                       label="Obsel Type 1")
        cls.obsel_type_2 = cls.model.create_obsel_type(id="#ObselType2", 
                                                       label="Obsel Type 2")
        cls.int_attribute_type = cls.model.create_attribute_type(
                                         id="#AttibuteTypeDataTypeInt",
                                         obsel_type=cls.obsel_type_1.get_uri(),
                                         data_type=XSD.integer) 
        cls.relation_type = cls.model.create_relation_type(
                                        id="#RelationTypeWithID",
                                        origin=cls.obsel_type_1.get_uri(),
                                        destination=cls.obsel_type_2.get_uri())

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_list_obsel_types(self):
        lot = self.model.list_obsel_types()
        assert len(lot) == 2

    def test_list_attribute_types(self):
        lat = self.model.list_attribute_types()
        assert len(lat) == 1

    def test_list_relation_types(self):
        lrt = self.model.list_relation_types()
        assert len(lrt) == 1

    def test_get_obsel_type(self):
        obsel_type = self.model.get("#ObselType1")
        assert obsel_type.get_uri() == self.obsel_type_1.get_uri()

    def test_get_attribute_type(self):
        attribute_type = self.model.get("#AttibuteTypeDataTypeInt")
        assert attribute_type.get_uri() == self.int_attribute_type.get_uri()

    def test_get_relation_type(self):
        relation_type = self.model.get("#RelationTypeWithID")
        assert relation_type.get_uri() == self.relation_type.get_uri()

class TestKtbsClientModelRemove(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelTest", label="Test model")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    @skip("Resource.remove() does not work : 405 Not Allowed")
    def test_remove_model(self):
        model_uri = self.model.get_uri()
        self.model.remove()
        assert self.base.get(model_uri) == None

class TestKtbsClientModelObselTypeRemove(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelTest", label="Test model")
        cls.obsel_type = cls.model.create_obsel_type(id="#ObselTypeWithID",
                                                     label="Test obsel type")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    @skip("ObselType.remove() is not yet implemented")
    def test_remove_obsel_type(self):
        self.obsel_type.remove()

class TestKtbsClientModelAttributeTypeRemove(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelTest", label="Test model")
        cls.obsel_type = cls.model.create_obsel_type(id="#ObselTypeWithID",
                                                     label="Test obsel type")
        cls.int_attribute_type = cls.model.create_attribute_type(
                                         id="#AttibuteTypeDataTypeInt",
                                         obsel_type=cls.obsel_type.get_uri(),
                                         data_type=XSD.integer) 

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    @skip("AttributeType.remove() is not yet implemented")
    def test_remove_attribute_type(self):
        self.int_attribute_type.remove()

class TestKtbsClientModelRelationTypeRemove(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelTest", label="Test model")
        cls.obsel_type_1 = cls.model.create_obsel_type(id="#ObselType1", 
                                                       label="Obsel Type 1")
        cls.obsel_type_2 = cls.model.create_obsel_type(id="#ObselType2", 
                                                       label="Obsel Type 2")
        cls.relation_type = cls.model.create_relation_type(
                                        id="#RelationTypeWithID",
                                        origin=cls.obsel_type_1.get_uri(),
                                        destination=cls.obsel_type_2.get_uri())

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    @skip("RelationType.remove() is not yet implemented")
    def test_remove_obsel_type(self):
        self.relation_type.remove()
