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
#    GNU Lesser General Public License for more .
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with KTBS.  If not, see <http://www.gnu.org/licenses/>.

from pprint import pformat
from unittest import skip

from rdflib.compare import graph_diff

from rdfrest.cores.factory import unregister_service
from ktbs.api.base import BaseMixin
from ktbs.api.method import MethodMixin
from ktbs.api.obsel import ObselMixin
from ktbs.api.trace import ComputedTraceMixin, StoredTraceMixin
from ktbs.api.trace_model import TraceModelMixin
from ktbs.engine.service import make_ktbs
from ktbs.engine import trace_stats
from ktbs.plugins import stats_per_type
from ktbs.serpar.jsonld_parser import *
from ktbs.serpar.jsonld_serializers import *
from ktbs import __version__ as ktbs_version
from ktbs import __commitno__ as ktbs_commit
from .test_ktbs_engine import KtbsTestCase

_BUILTIN_METHODS = [
    'external', 'filter', 'fsa', 'fusion', 'sparql', 'isparql', 'hrules',
    'parallel', 'pipe', 'sparql',
]


def unordered_json(json):
    """I transform a json object by replacing all lists by sets,
    as the order of lists is usually not relevant in JSON-LD.

    Note that this function may lose informations as in *some* lists,
    the order *might* be significant (depending on the @context).
    """
    if isinstance(json, dict):
        return frozenset((
                (key, unordered_json(val)) for key, val in json.items()
            ))
    elif isinstance(json, list):
        return frozenset(( unordered_json(i) for i in json ))
    else:
        return json

def assert_jsonld_equiv(val1, val2):
    assert unordered_json(val1) == unordered_json(val2), (
        "\n%s\n\nIS NOT JSON-LD EQUIVALENT TO\n\n%s"
        % (pformat(val1), pformat(val2)))

def assert_roundtrip(json_content, resource, parameters=None):
    graph = parse_json(json_content, resource.uri)
    _, spurious, missing = graph_diff(graph, resource.get_state(parameters))
    assert not(spurious or missing), graph_diff_msg(spurious, missing)

def graph_diff_msg(spurious, missing):
    ret = "Json does not encode the right graph"
    if spurious:
        ret += "\nSPURIOUS:\n" + spurious.serialize(format="turtle", encoding='utf-8').decode('utf-8')
    if missing:
        ret += "\nMISSING:\n" + missing.serialize(format="turtle", encoding='utf-8').decode('utf-8')
    return ret


class TestJsonRoot(KtbsTestCase):

    def test_bare_root(self):
        json_content = b"".join(
            serialize_json_root(self.my_ktbs.state, self.my_ktbs))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/',
            '@type': 'KtbsRoot',
            'hasBuiltinMethod': _BUILTIN_METHODS,
            'version': '%s%s' % (ktbs_version, ktbs_commit),
        })
        assert_roundtrip(json_content, self.my_ktbs)

    def test_customized_root(self):
        self.my_ktbs.label = "My customized ktbs root"
        with self.my_ktbs.edit() as g:
            g.add((self.my_ktbs.uri,
                   URIRef("http://example.org/ns/strprop"),
                   Literal("Hello world")
                   ))
            g.add((self.my_ktbs.uri,
                   URIRef("http://example.org/ns/numberprop"),
                   Literal(42)
                   ))
            g.add((self.my_ktbs.uri,
                   URIRef("http://example.org/ns/boolprop"),
                   Literal(True)
                   ))
            g.add((self.my_ktbs.uri,
                   URIRef("http://example.org/ns/uriprop"),
                   URIRef("http://example.org/foo")
                   ))
            g.add((URIRef("http://example.org/foo"),
                   URIRef("http://example.org/ns/revprop"),
                   self.my_ktbs.uri,
                   ))
            g.add((self.my_ktbs.uri,
                   RDF.type,
                   URIRef("http://example.org/ns/other-type"),
                   ))

        json_content = b"".join(
            serialize_json_root(self.my_ktbs.state, self.my_ktbs))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            'hasBuiltinMethod': _BUILTIN_METHODS,
            '@id': 'http://localhost:12345/',
            '@type': 'KtbsRoot',
            'additionalType': [ 'http://example.org/ns/other-type' ],
            'label': 'My customized ktbs root',
            'version': '%s%s' % (ktbs_version, ktbs_commit),
            'http://example.org/ns/strprop': 'Hello world',
            'http://example.org/ns/numberprop': 42,
            'http://example.org/ns/boolprop': True,
            'http://example.org/ns/uriprop':
                { "@id": 'http://example.org/foo' },
            '@reverse': {
                'http://example.org/ns/revprop': {
                    "@id": 'http://example.org/foo',
                }
            }
        })
        assert_roundtrip(json_content, self.my_ktbs)

    def test_populated_root(self):
        self.my_ktbs.create_base("b1/")
        self.my_ktbs.create_base("b2/")
        self.my_ktbs.create_base("b3/")
        json_content = b"".join(
            serialize_json_root(self.my_ktbs.state, self.my_ktbs))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            'hasBuiltinMethod': _BUILTIN_METHODS,
            '@id': 'http://localhost:12345/',
            '@type': 'KtbsRoot',
            'hasBase': [ 'b1/', 'b2/', 'b3/', ],
            'version': '%s%s' % (ktbs_version, ktbs_commit),
        })
        assert_roundtrip(json_content, self.my_ktbs)


class TestJsonBase(KtbsTestCase):

    def setup(self):
        super(TestJsonBase, self).setup()
        self.base = self.my_ktbs.create_base("b1/")

    def teardown(self):
        super(TestJsonBase, self).teardown()
        self.base = None

    def test_bare_base(self):
        json_content = b"".join(
            serialize_json_base(self.base.state, self.base))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/',
            '@type': 'Base',
            'inRoot': '../',
        })
        assert_roundtrip(json_content, self.base)

    def test_customized_base(self):
        self.base.label = "My customized base"
        with self.base.edit() as g:
            g.add((self.base.uri,
                   URIRef("http://example.org/ns/strprop"),
                   Literal("Hello world")
                   ))
        json_content = b"".join(
            serialize_json_base(self.base.state, self.base))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/',
            '@type': 'Base',
            'inRoot': '../',
            'label': 'My customized base',
            'http://example.org/ns/strprop': 'Hello world',
        })
        assert_roundtrip(json_content, self.base)

    def test_populated_base(self):
        self.base.create_method("method", KTBS.sparql)
        self.base.create_model("model")
        self.base.create_stored_trace("t1/", "model", "alonglongtimeago")
        json_content = b"".join(
            serialize_json_base(self.base.state, self.base))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/',
            '@type': 'Base',
            'inRoot': '../',
            'contains': [
                { '@id': 'method', '@type': 'Method' },
                { '@id': 'model', '@type': 'TraceModel' },
                { '@id': 't1/', '@type': 'StoredTrace' },
            ],
        })
        assert_roundtrip(json_content, self.base)

    def test_enriched_base(self):
        self.base.create_method("method", KTBS.sparql, label="the method")
        self.base.create_model("model", label="the model")
        self.base.create_stored_trace("t1/", "model", "alonglongtimeago", label="the trace")
        self.base.create_computed_trace("t2/", KTBS.filter, sources=['t1/'])

        params = lambda: {'prop':'comment,hasModel,hasMethod,hasSource,label,obselCount',}
        json_content = b"".join(
            serialize_json_base(self.base.get_state(params()), self.base))
        json = loads(json_content)
        obselCount = 0
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/',
            '@type': 'Base',
            'inRoot': '../',
            'contains': [
                { '@id': 'method', '@type': 'Method', 'label':"the method" },
                { '@id': 'model', '@type': 'TraceModel', 'label':"the model" },
                { '@id': 't1/', '@type': 'StoredTrace', 'label':"the trace",
                  'hasModel':"model", 'obselCount':obselCount },
                { '@id': 't2/', '@type': 'ComputedTrace', 'hasModel':"model",
                  'hasMethod': 'filter',
                  'hasSource':["t1/"], 'obselCount':obselCount },
            ],
        })
        assert_roundtrip(json_content, self.base, params())

    def test_post_base(self):
        """
        Test posting a base with minimal JSON (no @context, no inRoot...)
        """
        base_id = "b2/"
        graph = parse_json(dumps(
        {
            "@type": "Base",
            "@id": base_id,
        }), self.my_ktbs.uri)
        ret = self.my_ktbs.post_graph(graph)
        assert len(ret) == 1
        assert ret[0] == self.my_ktbs.uri + base_id
        newbase = self.my_ktbs.factory(ret[0], [KTBS.Base])
        assert isinstance(newbase, BaseMixin)
        assert newbase.state.value(self.my_ktbs.uri, KTBS.hasBase) == ret[0]
        assert newbase.state.value(self.my_ktbs.uri, KTBS.contains) is None

    def test_post_subbase(self):
        """
        Test posting a base with minimal JSON (no @context, no inRoot...)
        """

        b1 = self.my_ktbs.get_base('b1/')
        base_id = "b2/"
        graph = parse_json(dumps(
        {
            "@type": "Base",
            "@id": base_id,
        }), b1.uri)
        ret = b1.post_graph(graph)
        assert len(ret) == 1
        assert ret[0] == b1.uri + base_id
        newbase = self.my_ktbs.factory(ret[0], [KTBS.Base])
        assert isinstance(newbase, BaseMixin)
        assert newbase.state.value(b1.uri, KTBS.contains) == ret[0]
        assert newbase.state.value(b1.uri, KTBS.hasBase) is None

class TestJsonMethod(KtbsTestCase):

    def setup(self):
        super(TestJsonMethod, self).setup()
        self.base = self.my_ktbs.create_base("b1/")
        self.method = self.base.create_method("meth1", KTBS.filter,
                                              { "after": 42 })

    def teardown(self):
        super(TestJsonMethod, self).teardown()
        self.base = None
        self.method = None

    def test_bare_method(self):
        json_content = b"".join(
            serialize_json_method(self.method.state, self.method))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/meth1',
            '@type': 'Method',
            'hasParentMethod': 'filter',
            'parameter': [ 'after=42', ],
            'inBase': './',
        })
        assert_roundtrip(json_content, self.method)

    def test_customized_method(self):
        self.method.label = "My customized method"
        self.method.set_parameter("before", 101)
        with self.method.edit() as g:
            g.add((self.method.uri,
                   URIRef("http://example.org/ns/strprop"),
                   Literal("Hello world")
                   ))
        json_content = b"".join(
            serialize_json_method(self.method.state, self.method))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/meth1',
            '@type': 'Method',
            'hasParentMethod': 'filter',
            'parameter': [ 'after=42', 'before=101', ],
            'inBase': './',
            'label': 'My customized method',
            'http://example.org/ns/strprop': 'Hello world',
        })
        assert_roundtrip(json_content, self.method)

    def test_used_method(self):
        t1 = self.base.create_stored_trace("t1/", "http://example.org/model1")
        self.base.create_computed_trace("tt1/", self.method, sources=[t1])
        self.base.create_computed_trace("tt2/", self.method, sources=[t1])
        json_content = b"".join(
            serialize_json_method(self.method.state, self.method))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/meth1',
            '@type': 'Method',
            'hasParentMethod': 'filter',
            'parameter': [ 'after=42', ],
            'isMethodOf': [ 'tt1/', 'tt2/' ],
            'inBase': './',
        })
        assert_roundtrip(json_content, self.method)

    def test_inherited_method(self):
        self.base.create_method("meth2/", self.method,
                                     { "before": 101 })
        json_content = b"".join(
            serialize_json_method(self.method.state, self.method))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/meth1',
            '@type': 'Method',
            'hasParentMethod': 'filter',
            'parameter': [ 'after=42', ],
            'isParentMethodOf': [ 'meth2/', ],
            'inBase': './',
        })
        assert_roundtrip(json_content, self.method)

    def test_inheriting_method(self):
        m2 = self.base.create_method("meth2/", self.method,
                                     { "before": 101 })
        json_content = b"".join(
            serialize_json_method(m2.state, m2))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/meth2/',
            '@type': 'Method',
            'hasParentMethod': '../meth1',
            'parameter': [ 'before=101', ],
            'inBase': '../',
        })
        assert_roundtrip(json_content, m2)

    def test_post_method(self):
        """
        Test posting a method with minimal JSON (no @context, no inBase...)
        """
        method_id = "meth2/"
        graph = parse_json(dumps(
        {
            "@type": "Method",
            "@id": method_id,
            "hasParentMethod": "meth1",
            "parameter": [ "before=101" ],
        }), self.base.uri)
        ret = self.base.post_graph(graph)
        assert len(ret) == 1
        assert ret[0] == self.base.uri + method_id
        newmethod = self.base.factory(ret[0], [KTBS.Method])
        assert isinstance(newmethod, MethodMixin)

class TestJsonHashModel(KtbsTestCase):

    def setup(self):
        super(TestJsonHashModel, self).setup()
        self.base = self.my_ktbs.create_base("b1/")
        self.model = self.base.create_model("modl1",)

    def teardown(self):
        super(TestJsonHashModel, self).teardown()
        self.base = None
        self.model = None


    def test_bare_model(self):
        json_content = b"".join(
            serialize_json_model(self.model.state, self.model))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@graph': [
                {
                    '@id': 'http://localhost:12345/b1/modl1',
                    '@type': 'TraceModel',
                    'hasUnit': 'millisecond',
                    'inBase': './',
                },
            ]
        })
        assert_roundtrip(json_content, self.model)

    def test_customized_model(self):
        self.model.label = "My customized model"
        self.model.unit = "http://example.org/ns/unit"
        with self.model.edit() as g:
            g.add((self.model.uri,
                   URIRef("http://example.org/ns/strprop"),
                   Literal("Hello world")
            ))
        json_content = b"".join(
            serialize_json_model(self.model.state, self.model))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@graph': [
                {
                    '@id': 'http://localhost:12345/b1/modl1',
                    '@type': 'TraceModel',
                    'hasUnit': 'http://example.org/ns/unit',
                    'inBase': './',
                    'label': 'My customized model',
                    'http://example.org/ns/strprop': 'Hello world',
                },
            ]
        })
        assert_roundtrip(json_content, self.model)

    def test_populated_model(self):
        m2 = self.base.create_model("modl2/")
        self.model.add_parent(m2)
        ot1 = self.model.create_obsel_type("#OT1")
        ot2 = self.model.create_obsel_type("#OT2", [ot1])
        at1 = self.model.create_attribute_type("#at1", [ot1], [XSD.string])
        at2 = self.model.create_attribute_type("#at2", [ot2], [XSD.integer])
        rt1 = self.model.create_relation_type("#rt1", [ot1], [ot1])
        rt2 = self.model.create_relation_type("#rt2", [ot1], [ot2], [rt1])
        ot1.suggested_color = "red"
        ot1.suggested_symbol = "♥"
        at1.suggested_color = "blue"
        at2.suggested_symbol = "#"
        rt1.suggested_color = "green"
        rt2.suggested_symbol = "→"

        json_content = b"".join(
            serialize_json_model(self.model.state, self.model))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@graph': [
                {
                    '@id': 'http://localhost:12345/b1/modl1',
                    '@type': 'TraceModel',
                    'hasUnit': 'millisecond',
                    'inBase': './',
                    'hasParentModel': ["modl2/"],
                },
                {
                    '@id': '#OT1',
                    '@type': 'ObselType',
                    "suggestedColor": "red",
                    "suggestedSymbol": "♥",
                },
                {
                    '@id': '#OT2',
                    '@type': 'ObselType',
                    'hasSuperObselType': [ '#OT1' ],
                },
                {
                    '@id': '#at1',
                    '@type': 'AttributeType',
                    'hasAttributeObselType': ['#OT1',],
                    'hasAttributeDatatype': ['xsd:string',],
                    "suggestedColor": "blue",
                },
                {
                    '@id': '#at2',
                    '@type': 'AttributeType',
                    'hasAttributeObselType': ['#OT2',],
                    'hasAttributeDatatype': ['xsd:integer',],
                    "suggestedSymbol": "#",
                },
                {
                    '@id': '#rt1',
                    '@type': 'RelationType',
                    'hasRelationOrigin': ['#OT1',],
                    'hasRelationDestination': ['#OT1',],
                    "suggestedColor": "green",
                },
                {
                    '@id': '#rt2',
                    '@type': 'RelationType',
                    'hasRelationOrigin': ['#OT1',],
                    'hasRelationDestination': ['#OT2',],
                    'hasSuperRelationType': ['#rt1',],
                    "suggestedSymbol": "→",
                },
            ]
        })
        assert_roundtrip(json_content, self.model)

    def test_post_model(self):
        """
        Test posting a model with minimal JSON (no @context, no inBase...)
        """
        model_id = "modl2/"
        graph = parse_json(dumps(
        {
            "@graph": [
                {
                    "@type": "TraceModel",
                    "@id": model_id
                },
                {
                    "@type": "ObselType",
                    "@id": model_id+"#OT1"
                },
            ]
        }), self.base.uri)
        ret = self.base.post_graph(graph)
        assert len(ret) == 1
        assert ret[0] == self.base.uri + model_id
        newmodel = self.base.factory(ret[0], [KTBS.TraceModel])
        assert isinstance(newmodel, TraceModelMixin)
        assert len(newmodel.obsel_types) == 1


class TestJsonSlashModel(KtbsTestCase):

    def setup(self):
        super(TestJsonSlashModel, self).setup()
        self.base = self.my_ktbs.create_base("b1/")
        self.model = self.base.create_model("modl1/",)

    def teardown(self):
        super(TestJsonSlashModel, self).teardown()
        self.base = None
        self.model = None


    def test_bare_model(self):
        json_content = b"".join(
            serialize_json_model(self.model.state, self.model))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@graph': [
                {
                    '@id': 'http://localhost:12345/b1/modl1/',
                    '@type': 'TraceModel',
                    'hasUnit': 'millisecond',
                    'inBase': '../',
                },
            ]
        })
        assert_roundtrip(json_content, self.model)

    def test_customized_model(self):
        self.model.label = "My customized model"
        self.model.unit = "http://example.org/ns/unit"
        with self.model.edit() as g:
            g.add((self.model.uri,
                   URIRef("http://example.org/ns/strprop"),
                   Literal("Hello world")
            ))
        json_content = b"".join(
            serialize_json_model(self.model.state, self.model))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@graph': [
                {
                    '@id': 'http://localhost:12345/b1/modl1/',
                    '@type': 'TraceModel',
                    'hasUnit': 'http://example.org/ns/unit',
                    'inBase': '../',
                    'label': 'My customized model',
                    'http://example.org/ns/strprop': 'Hello world',
                },
            ]
        })
        assert_roundtrip(json_content, self.model)

    def test_slashhash_populated_model(self):
        m2 = self.base.create_model("modl2")
        self.model.add_parent(m2)
        ot1 = self.model.create_obsel_type("#OT1")
        ot2 = self.model.create_obsel_type("#OT2", [ot1])
        at1 = self.model.create_attribute_type("#at1", [ot1], [XSD.string])
        at2 = self.model.create_attribute_type("#at2", [ot2], [XSD.integer])
        rt1 = self.model.create_relation_type("#rt1", [ot1], [ot1])
        rt2 = self.model.create_relation_type("#rt2", [ot1], [ot2], [rt1])

        json_content = b"".join(
            serialize_json_model(self.model.state, self.model))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@graph': [
                {
                    '@id': 'http://localhost:12345/b1/modl1/',
                    '@type': 'TraceModel',
                    'hasUnit': 'millisecond',
                    'inBase': '../',
                    'hasParentModel': ["../modl2"],
                },
                {
                    '@id': '#OT1',
                    '@type': 'ObselType',
                },
                {
                    '@id': '#OT2',
                    '@type': 'ObselType',
                    'hasSuperObselType': [ '#OT1' ],
                },
                {
                    '@id': '#at1',
                    '@type': 'AttributeType',
                    'hasAttributeObselType': ['#OT1',],
                    'hasAttributeDatatype': ['xsd:string',],
                },
                {
                    '@id': '#at2',
                    '@type': 'AttributeType',
                    'hasAttributeObselType': ['#OT2',],
                    'hasAttributeDatatype': ['xsd:integer',],
                },
                {
                    '@id': '#rt1',
                    '@type': 'RelationType',
                    'hasRelationOrigin': ['#OT1',],
                    'hasRelationDestination': ['#OT1',],
                },
                {
                    '@id': '#rt2',
                    '@type': 'RelationType',
                    'hasRelationOrigin': ['#OT1',],
                    'hasRelationDestination': ['#OT2',],
                    'hasSuperRelationType': ['#rt1',],
                },
            ]
        })
        assert_roundtrip(json_content, self.model)

    # unskip the following test once kTBS supports "slash-only" URIs in models
    @skip("not supported yet")
    def test_mixed_populated_model(self):
        m2 = self.base.create_model("modl2")
        self.model.add_parent(m2)
        ot1 = self.model.create_obsel_type("OT1")
        ot2 = self.model.create_obsel_type("#OT2", [ot1])
        at1 = self.model.create_attribute_type("at1", [ot1], [XSD.string])
        at2 = self.model.create_attribute_type("at2", [ot2], [XSD.integer])
        rt1 = self.model.create_relation_type("rt1", [ot1], [ot1])
        rt2 = self.model.create_relation_type("rt2", [ot1], [ot2], [rt1])

        json_content = b"".join(
            serialize_json_model(self.model.state, self.model))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@graph': [
                {
                    '@id': 'http://localhost:12345/b1/modl1/',
                    '@type': 'TraceModel',
                    'hasUnit': 'millisecond',
                    'inBase': '../',
                    'hasParentModel': ["../modl2"],
                },
                {
                    '@id': 'OT1',
                    '@type': 'ObselType',
                },
                {
                    '@id': '#OT2',
                    '@type': 'ObselType',
                    'hasSuperObselType': [ 'OT1' ],
                },
                {
                    '@id': 'at1',
                    '@type': 'AttributeType',
                    'hasAttributeObselType': 'OT1',
                    'hasAttributeDatatype': 'xsd:string',
                },
                {
                    '@id': '#at2',
                    '@type': 'AttributeType',
                    'hasAttributeObselType': '#OT2',
                    'hasAttributeDatatype': 'xsd:integer',
                },
                {
                    '@id': 'rt1',
                    '@type': 'RelationType',
                    'hasRelationOrigin': 'OT1',
                    'hasRelationDestination': 'OT1',
                },
                {
                    '@id': '#rt2',
                    '@type': 'RelationType',
                    'hasRelationOrigin': 'OT1',
                    'hasRelationDestination': '#OT2',
                    'hasSuperRelationType': ['rt1',],
                },
            ]
        })
        assert_roundtrip(json_content, self.model)


class TestJsonTwoModels(KtbsTestCase):

    def setup(self):
        super(TestJsonTwoModels, self).setup()
        self.base = self.my_ktbs.create_base("b1/")
        self.model = self.base.create_model("modl1",)
        self.other_ktbs = make_ktbs("http://example.org/")
        self.other_base = self.other_ktbs.create_base("another/")
        self.other_model = self.other_base.create_model("model",)

    def teardown(self):
        super(TestJsonTwoModels, self).teardown()
        if self.other_ktbs is not None:
            unregister_service(self.other_ktbs.service)
            self.other_ktbs = None
            self.other_base = None
            self.other_model = None

    def test_foreign_populated_model(self):
        otf = self.other_model.create_obsel_type("#OTF").uri
        rtf = self.other_model.create_relation_type("#rtF").uri

        self.model.add_parent(self.other_model)
        ot1 = self.model.create_obsel_type( "#OT1", [otf])
        at1 = self.model.create_attribute_type("#at1", [otf], [XSD.string])
        rt1 = self.model.create_relation_type("#rt1", [ot1], [otf], [rtf])

        json_content = b"".join(
            serialize_json_model(self.model.state, self.model))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@graph': [
                {
                    '@id': 'http://localhost:12345/b1/modl1',
                    '@type': 'TraceModel',
                    'hasUnit': 'millisecond',
                    'inBase': './',
                    'hasParentModel': ["http://example.org/another/model"],
                },
                {
                    '@id': '#OT1',
                    '@type': 'ObselType',
                    'hasSuperObselType':
                        ['http://example.org/another/model#OTF',],
                },
                {
                    '@id': '#at1',
                    '@type': 'AttributeType',
                    'hasAttributeObselType':
                        ['http://example.org/another/model#OTF',],
                    'hasAttributeDatatype': ['xsd:string',],
                },
                {
                    '@id': '#rt1',
                    '@type': 'RelationType',
                    'hasRelationOrigin': ['#OT1',],
                    'hasRelationDestination':
                        ['http://example.org/another/model#OTF',],
                    'hasSuperRelationType':
                        ['http://example.org/another/model#rtF',],
                },
            ]
        })
        assert_roundtrip(json_content, self.model)

class TestJsonStoredTrace(KtbsTestCase):

    def setup(self):
        super(TestJsonStoredTrace, self).setup()
        self.base = self.my_ktbs.create_base("b1/")
        self.model = self.base.create_model("modl",)
        self.t1 = self.base.create_stored_trace("t1/", self.model,
                                                "1970-01-01T00:00:00Z")

    def teardown(self):
        super(TestJsonStoredTrace, self).teardown()
        self.base = None
        self.model = None
        self.t1 = None

    def test_bare_stored_trace(self):
        json_content = b"".join(serialize_json_trace(self.t1.state, self.t1))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/t1/',
            '@type': 'StoredTrace',
            'inBase': '../',
            'hasObselList': '@obsels',
            'hasTraceStatistics': '@stats',
            'hasModel': '../modl',
            'origin': '1970-01-01T00:00:00Z',
        })
        assert_roundtrip(json_content, self.t1)

    def test_customized_stored_trace(self):
        self.t1.label = "My customized stored trace"
        self.t1.origin = "alonglongtimeago"
        self.t1.default_subject = "pa"
        self.t1.model = "http://example.org/model"
        self.t1.trace_begin = 42
        with self.t1.edit() as g:
            g.add((self.t1.uri,
                   URIRef("http://example.org/ns/strprop"),
                   Literal("Hello world")
                   ))
        json_content = b"".join(serialize_json_trace(self.t1.state, self.t1))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/t1/',
            '@type': 'StoredTrace',
            'label': 'My customized stored trace',
            'inBase': '../',
            'hasObselList': '@obsels',
            'hasTraceStatistics': '@stats',
            'hasModel': 'http://example.org/model',
            'origin': 'alonglongtimeago',
            'traceBegin': 42,
            'defaultSubject': 'pa',
            'http://example.org/ns/strprop': 'Hello world',
        })
        assert_roundtrip(json_content, self.t1)

    def test_customized_stored_trace_2(self):
        self.t1.label = "My customized stored trace #2"
        self.t1.trace_begin_dt = '2015-12-09T12:00:00Z'
        self.t1.trace_end_dt = '2015-12-09T13:00:00Z'
        json_content = b"".join(serialize_json_trace(self.t1.state, self.t1))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/t1/',
            '@type': 'StoredTrace',
            'label': 'My customized stored trace #2',
            'inBase': '../',
            'hasObselList': '@obsels',
            'hasTraceStatistics': '@stats',
            'hasModel': '../modl',
            'origin': '1970-01-01T00:00:00Z',
            'traceBegin': 1449662400000,
            'traceBeginDT': '2015-12-09T12:00:00+00:00',
            'traceEnd': 1449666000000,
            'traceEndDT': '2015-12-09T13:00:00+00:00',
        })
        assert_roundtrip(json_content, self.t1)

    def test_transformed_stored_trace(self):
        self.base.create_computed_trace("t2/", KTBS.filter, { "before": 42 },
                                        [self.t1])
        json_content = b"".join(serialize_json_trace(self.t1.state, self.t1))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/t1/',
            '@type': 'StoredTrace',
            'inBase': '../',
            'hasObselList': '@obsels',
            'hasTraceStatistics': '@stats',
            'hasModel': '../modl',
            'origin': '1970-01-01T00:00:00Z',
            'isSourceOf': ['../t2/',],
        })
        assert_roundtrip(json_content, self.t1)

    def test_post_stored_trace(self):
        """
        Test posting a trace with minimal JSON (no @context, no inBase...)
        """
        stored_trace_id = "t2/"
        graph = parse_json(dumps(
        {
            "@type": "StoredTrace",
            "@id": stored_trace_id,
            "hasModel": "modl",
        }), self.base.uri)
        ret = self.base.post_graph(graph)
        assert len(ret) == 1
        assert ret[0] == self.base.uri + stored_trace_id
        newstored_trace = self.base.factory(ret[0], [KTBS.StoredTrace])
        assert isinstance(newstored_trace, StoredTraceMixin)


    def test_uri_default_subject(self):
        self.t1.default_subject = URIRef("http://ex.co/bob")
        json_content = b"".join(serialize_json_trace(self.t1.state, self.t1))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/t1/',
            '@type': 'StoredTrace',
            'inBase': '../',
            'hasObselList': '@obsels',
            'hasTraceStatistics': '@stats',
            'hasModel': '../modl',
            'origin': '1970-01-01T00:00:00Z',
            'hasDefaultSubject': 'http://ex.co/bob'
        })
        assert_roundtrip(json_content, self.t1)


class TestJsonComputedTrace(KtbsTestCase):

    def setup(self):
        super(TestJsonComputedTrace, self).setup()
        self.base = self.my_ktbs.create_base("b1/")
        self.model = self.base.create_model("modl",)
        self.t1 = self.base.create_stored_trace("t1/", self.model,
                                                "1970-01-01T00:00:00Z")
        self.t2 = self.base.create_computed_trace("t2/",
                                                  KTBS.filter,
                                                  { "after": 42 },
                                                  [self.t1])

    def teardown(self):
        super(TestJsonComputedTrace, self).teardown()
        self.base = None
        self.model = None
        self.t1 = None
        self.t2 = None

    def test_bare_computed_trace(self):
        json_content = b"".join(serialize_json_trace(self.t2.state, self.t2))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/t2/',
            '@type': 'ComputedTrace',
            'inBase': '../',
            'hasMethod': 'filter',
            'hasSource': [ '../t1/', ],
            'parameter': [ 'after=42', ],
            'hasObselList': '@obsels',
            'hasTraceStatistics': '@stats',
            'hasModel': '../modl',
            'origin': '1970-01-01T00:00:00Z',
        })
        assert_roundtrip(json_content, self.t2)

    def test_customized_computed_trace(self):
        self.meth = self.base.create_method("meth", KTBS.filter,
                                            {"before": 101})
        self.t2.method = self.meth
        self.t2.label = "My customized computed trace"
        self.t2.set_parameter("origin", "alonglongtimeago")
        self.t2.set_parameter("model", "http://example.org/model"),
        with self.t2.edit() as g:
            g.add((self.t2.uri,
                   URIRef("http://example.org/ns/strprop"),
                   Literal("Hello world")
                   ))
        json_content = b"".join(serialize_json_trace(self.t2.state, self.t2))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/t2/',
            '@type': 'ComputedTrace',
            'label': 'My customized computed trace',
            'inBase': '../',
            'hasMethod': '../meth',
            'hasSource': [ '../t1/', ],
            'parameter': [
                'after=42',
                'origin=alonglongtimeago',
                'model=http://example.org/model',
            ],
            'hasObselList': '@obsels',
            'hasTraceStatistics': '@stats',
            'hasModel': 'http://example.org/model',
            'origin': 'alonglongtimeago',
            'http://example.org/ns/strprop': 'Hello world',
        })
        assert_roundtrip(json_content, self.t2)

    def test_transformed_computed_trace(self):
        self.t3 = self.base.create_computed_trace("t3/",
                                                  KTBS.fusion,
                                                  {},
                                                  [self.t1, self.t2])
        json_content = b"".join(serialize_json_trace(self.t2.state, self.t2))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context':
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
            '@id': 'http://localhost:12345/b1/t2/',
            '@type': 'ComputedTrace',
            'inBase': '../',
            'hasMethod': 'filter',
            'hasSource': [ '../t1/', ],
            'parameter': [ 'after=42', ],
            'hasObselList': '@obsels',
            'hasTraceStatistics': '@stats',
            'hasModel': '../modl',
            'origin': '1970-01-01T00:00:00Z',
            'isSourceOf': ['../t3/',],
        })
        assert_roundtrip(json_content, self.t2)

    def test_post_computed_trace(self):
        """
        Test posting a trace with minimal JSON (no @context, no inBase...)
        """
        computed_trace_id = "t3/"
        graph = parse_json(dumps(
        {
            "@type": "ComputedTrace",
            "@id": computed_trace_id,
            "hasMethod": "filter",
            "hasSource": "t1/",
        }), self.base.uri)
        ret = self.base.post_graph(graph)
        assert len(ret) == 1
        assert ret[0] == self.base.uri + computed_trace_id
        newcomputed_trace = self.base.factory(ret[0], [KTBS.ComputedTrace])
        assert isinstance(newcomputed_trace, ComputedTraceMixin)


class TestJsonObsels(KtbsTestCase):

    def setup(self):
        super(TestJsonObsels, self).setup()
        self.base = self.my_ktbs.create_base("b1/")
        self.model = self.base.create_model("modl",)
        self.ot1 = ot1 = self.model.create_obsel_type("#OT1")
        self.at1 = self.model.create_attribute_type("#at1", [ot1])
        self.at2 = self.model.create_attribute_type("#at2", [ot1])
        self.rt1 = self.model.create_attribute_type("#rt1", [ot1], [ot1])
        self.t1 = self.base.create_stored_trace("t1/", self.model,
                                                "1970-01-01T00:00:00Z")

    def teardown(self):
        super(TestJsonObsels, self).teardown()
        self.base = None
        self.model = self.ot1 = self.at1 = self.at2 = self.rt1 = None
        self.t1 = None

    def populate(self):
        # create obsel in wrong order, to check that they are serialized in
        # the correct order nonetheless
        ex_foo = URIRef('http://example.org/Foo')
        self.o3 = self.t1.create_obsel("o3", self.ot1, 3000, 4000,
                                       URIRef("#baz", self.t1.uri),
                                       {self.at1: "hello world",
                                        RDF.type: ex_foo,
                                        })
        self.o2 = self.t1.create_obsel("o2", self.ot1, 2000, 3000, "bar",
                                       {self.at2: 42}, [(self.rt1, self.o3)])
        self.o1 = self.t1.create_obsel("o1", self.ot1,
            "1970-01-01T00:00:01Z", "1970-01-01T00:00:02Z", "foo",
            { self.at1: "hello world",
              self.at2: URIRef("http://example.org/resource"),
            },
            None, None,
            [ URIRef("http://example.org/t1/source-obsel"),
              URIRef("http://localhost:12345/b1/t0/o0"),
            ]
        )

    def test_empty_obsels(self):
        json_content = b"".join(serialize_json_trace_obsels(
            self.t1.obsel_collection.state,
            self.t1.obsel_collection))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context': [
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
                { 'm': 'http://localhost:12345/b1/modl#', },
                ],
            '@id': './',
            'hasObselList': {
                '@id': '',
                '@type': 'StoredTraceObsels',
            },
            'obsels': []
        })
        assert_roundtrip(json_content, self.t1.obsel_collection)

    def test_populated_obsels(self):
        self.populate()
        json_content = b"".join(serialize_json_trace_obsels(
            self.t1.obsel_collection.state,
            self.t1.obsel_collection))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context': [
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
                { 'm': 'http://localhost:12345/b1/modl#', },
                ],
            '@id': './',
            'hasObselList': {
                '@id': '',
                '@type': 'StoredTraceObsels',
            },
            'obsels': [
                {
                    '@id': 'o1',
                    '@type': 'm:OT1',
                    'begin': 1000,
                    'end': 2000,
                    'subject': 'foo',
                    'm:at1': 'hello world',
                    'm:at2': { '@id': 'http://example.org/resource' },
                    'hasSourceObsel': ['http://example.org/t1/source-obsel',
                                       '../t0/o0',],
                    'beginDT': '1970-01-01T00:00:01+00:00',
                    'endDT': '1970-01-01T00:00:02+00:00',
                },
                {
                    '@id': 'o2',
                    '@type': 'm:OT1',
                    'begin': 2000,
                    'end': 3000,
                    'subject': 'bar',
                    'm:at2': 42,
                    'm:rt1': { '@id': 'o3', 'hasTrace': './' },
                },
                {
                    '@id': 'o3',
                    '@type': ['m:OT1', 'http://example.org/Foo'],
                    'begin': 3000,
                    'end': 4000,
                    'hasSubject': './#baz',
                    'm:at1': 'hello world',
                    '@reverse': {
                        'm:rt1': { '@id': 'o2', 'hasTrace': './' },
                    },
                },
            ]
        })
        assert_roundtrip(json_content, self.t1.obsel_collection)

    def test_o1(self):
        self.populate()
        json_content = b"".join(serialize_json_obsel(self.o1.state, self.o1))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context': [
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
                { 'm': 'http://localhost:12345/b1/modl#', },
                ],
            '@id': 'http://localhost:12345/b1/t1/o1',
            'hasTrace': './',
            '@type': 'm:OT1',
            'begin': 1000,
            'end': 2000,
            'subject': 'foo',
            'm:at1': 'hello world',
            'm:at2': { '@id': 'http://example.org/resource' },
            'hasSourceObsel': ['http://example.org/t1/source-obsel',
                               '../t0/o0',],
            'beginDT': '1970-01-01T00:00:01+00:00',
            'endDT': '1970-01-01T00:00:02+00:00',
        })
        assert_roundtrip(json_content, self.o1)

    def test_o2(self):
        self.populate()
        json_content = b"".join(serialize_json_obsel(self.o2.state, self.o2))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context': [
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
                { 'm': 'http://localhost:12345/b1/modl#', },
                ],
            '@id': 'http://localhost:12345/b1/t1/o2',
            'hasTrace': './',
            '@type': 'm:OT1',
            'begin': 2000,
            'end': 3000,
            'subject': 'bar',
            'm:at2': 42,
            'm:rt1': { '@id': 'o3', 'hasTrace': './' },
        })
        assert_roundtrip(json_content, self.o2)

    def test_o3(self):
        self.populate()
        json_content = b"".join(serialize_json_obsel(self.o3.state, self.o3))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context': [
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
                { 'm': 'http://localhost:12345/b1/modl#', },
                ],
            '@id': 'http://localhost:12345/b1/t1/o3',
            'hasTrace': './',
            '@type': ['m:OT1', 'http://example.org/Foo'],
            'begin': 3000,
            'end': 4000,
            "hasSubject": "./#baz",
            'm:at1': 'hello world',
            '@reverse': {
                'm:rt1': { '@id': 'o2', 'hasTrace': './' },
            },
        })
        assert_roundtrip(json_content, self.o3)

    def test_post_obsel(self):
        """
        Test posting an obsel with minimal JSON (no @context, no hasTrace...)
        """
        self.t1.default_subject = "foobar"
        graph = parse_json(dumps(
        {
            "@type": "m:OT1",
        }), self.t1.uri)
        ret = self.t1.post_graph(graph)
        assert len(ret) == 1
        newobsel = self.t1.factory(ret[0], [KTBS.Obsel])
        assert isinstance(newobsel, ObselMixin)
        assert newobsel.obsel_type == self.ot1, newobsel.obsel_type

    def test_post_multiple_obsels(self):
        """
        Test posting several obsels at once
        """
        self.t1.default_subject = "foobar"
        graph = parse_json(dumps(
        [{
            "@type": "m:OT1",
            "begin": 4000,
        },
        {
            "@type": "m:OT1",
            "begin": 5000,
        }]), self.t1.uri)

        ret = self.t1.post_graph(graph)
        assert len(ret) == 2
        newobsel1 = self.t1.factory(ret[0], [KTBS.Obsel])
        assert isinstance(newobsel1, ObselMixin)
        assert newobsel1.obsel_type == self.ot1, newobsel1.obsel_type
        newobsel2 = self.t1.factory(ret[1], [KTBS.Obsel])
        assert isinstance(newobsel2, ObselMixin)
        assert newobsel2.obsel_type == self.ot1, newobsel2.obsel_type

class TestJsonStats(KtbsTestCase):


    def setup(self):
        super(TestJsonRoot, self).setup()
        # load stats plugins which are enabled by default in the global config
        trace_stats.add_plugin(stats_per_type.populate_stats)

    def teardown(self):
        super(TestJsonRoot, self).teardown()
        trace_stats.remove_plugin(stats_per_type.populate_stats)

    def setup(self):
        super(TestJsonStats, self).setup()

        # load stats plugins which are enabled by default in the global config
        trace_stats.add_plugin(stats_per_type.populate_stats)

        self.base = self.my_ktbs.create_base("b1/")
        self.model = self.base.create_model("modl",)
        self.ot1 = ot1 = self.model.create_obsel_type("#OT1")
        self.ot2 = ot2 = self.model.create_obsel_type("#OT2")
        self.t1 = self.base.create_stored_trace("t1/", self.model,
                                                "1970-01-01T00:00:00Z")

    def teardown(self):
        super(TestJsonStats, self).teardown()
        self.base = None
        self.model = self.ot1 = self.ot2 = None
        self.t1 = None
        trace_stats.remove_plugin(stats_per_type.populate_stats)

    def populate(self):
        # create obsel in wrong order, as TestJsonObsels
        self.o3 = self.t1.create_obsel("o3", self.ot1, 3000, 4000, None)
        self.o2 = self.t1.create_obsel("o2", self.ot1, 2000, 3000, "bar")
        self.o1 = self.t1.create_obsel("o1", self.ot1,
            "1970-01-01T00:00:01Z", "1970-01-01T00:00:02Z", "foo")
        self.o4 = self.t1.create_obsel("o4", self.ot2, 1000, 2000, "alice")
        self.o5 = self.t1.create_obsel("o5", self.ot2, 4000, 5000, "bob")

    def test_stats_empty_obsels(self):
        json_content = b"".join(serialize_json_trace_stats(
            self.t1.trace_statistics.state,
            self.t1.trace_statistics))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context': [
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
                { 'm': 'http://localhost:12345/b1/modl#',
                  'stats': 'http://tbs-platform.org/2016/trace-stats#',
                  'stats:hasObselType': {
                      '@type': '@id'
                      },
                  },
                ],
            '@id': './',
            'hasTraceStatistics': {
                '@id': '',
                '@type': 'TraceStatistics',
            },
            'stats:obselCount': 0,
        })

        assert_roundtrip(json_content, self.t1.trace_statistics)

    def test_stats_populated_obsels(self):
        self.populate()
        json_content = b"".join(serialize_json_trace_stats(
            self.t1.trace_statistics.state,
            self.t1.trace_statistics))
        json = loads(json_content)
        assert_jsonld_equiv(json, {
            '@context': [
                'http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context',
                { 'm': 'http://localhost:12345/b1/modl#',
                  'stats': 'http://tbs-platform.org/2016/trace-stats#',
                  'stats:hasObselType': {
                      '@type': '@id'
                      },
                  },
                ],
            '@id': './',
            'hasTraceStatistics': {
                '@id': '',
                '@type': 'TraceStatistics',
            },
            'stats:obselCount': 5,
            'stats:minTime': 1000,
            'stats:maxTime': 5000,
            'stats:duration': 4000,
            'stats:obselCountPerType': [{'stats:hasObselType': 'm:OT1',
                                         'stats:nb': 3},
                                        {'stats:hasObselType': 'm:OT2',
                                         'stats:nb': 2}]
        })
        # Does a roundtrip have a sens for trace statistics ?
        assert_roundtrip(json_content, self.t1.trace_statistics)
