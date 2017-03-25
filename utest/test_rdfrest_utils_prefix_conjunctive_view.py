# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Françoise Conil <francoise.conil@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RDF-REST is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with RDF-REST.  If not, see <http://www.gnu.org/licenses/>.
from pytest import mark, raises as assert_raises

from rdfrest.util.prefix_conjunctive_view import PrefixConjunctiveView

import os
import pyodbc
from rdflib import BNode, Graph, Namespace
from unittest import skip

EX = Namespace('http://localhost:1234/')

class TestDefaultStore(object):

    def get_store(self):
        return Graph().store

    def setup(self):
        self.s = self.get_store()
        self.g1 = Graph(self.s, EX['g1/'])
        self.g2 = Graph(self.s, EX['g1/g2'])
        self.ga = Graph(self.s, EX['pab/ga'])
        self.gb = Graph(self.s, EX['pab/gb'])

        self.g1.add((EX.x1, EX.p, EX.x2))
        self.g2.add((EX.x2, EX.p, EX.x3))
        self.g2.add((EX.x3, EX.p, EX.x4))
        self.ga.add((EX.xa, EX.p, EX.xb))
        self.gb.add((EX.xb, EX.p, EX.xc))

        self.p12 = PrefixConjunctiveView(EX['g1/'], self.s, BNode('p12'))
        self.pab = PrefixConjunctiveView(EX['pab/'], self.s, BNode('pab'))

    def teardown(self):
        self.g1.remove((None, None, None))
        self.g2.remove((None, None, None))
        self.ga.remove((None, None, None))
        self.gb.remove((None, None, None))



    @mark.parametrize("datasetname, triple, expected", [
                ('p12', None, {EX['g1/'], EX['g1/g2']}),
                ('pab', None, {EX['pab/ga'], EX['pab/gb']}),

                ('p12', (EX.x1, EX.p, EX.x2), {EX['g1/']}),
                ('p12', (EX.x2, EX.p, EX.x3), {EX['g1/g2']}),
                ('p12', (EX.xa, EX.p, EX.xb), set()),
                ('p12', (EX.xb, EX.p, EX.xc), set()),

                ('pab', (EX.x1, EX.p, EX.x2), set()),
                ('pab', (EX.x2, EX.p, EX.x3), set()),
                ('pab', (EX.xa, EX.p, EX.xb), {EX['pab/ga']}),
                ('pab', (EX.xb, EX.p, EX.xc), {EX['pab/gb']}),
    ])
    def test_contexts(self, datasetname, triple, expected):
        dataset = getattr(self, datasetname)
        assert set( g.identifier for g in dataset.contexts(triple) ) == \
               expected

    @mark.parametrize("datasetname, length", [
                ('p12', 3),
                ('pab', 2),
    ])
    def test_len(self, datasetname, length):
        dataset = getattr(self, datasetname)
        assert len(dataset) == length

    @mark.parametrize("datasetname, triple_or_quad, expected", [
                ('p12', (EX.x1, EX.p, EX.x2), True),
                ('p12', (EX.x2, EX.p, EX.x3), True),
                ('p12', (EX.x3, EX.p, EX.x4), True),
                ('p12', (EX.xa, EX.p, EX.xb), False),
                ('p12', (EX.xb, EX.p, EX.xc), False),
                ('p12', (EX.x0, EX.p, EX.xc), False),

                ('pab', (EX.x1, EX.p, EX.x2), False),
                ('pab', (EX.x2, EX.p, EX.x3), False),
                ('pab', (EX.x3, EX.p, EX.x4), False),
                ('pab', (EX.xa, EX.p, EX.xb), True),
                ('pab', (EX.xb, EX.p, EX.xc), True),
                ('pab', (EX.x0, EX.p, EX.xc), False),

                ('p12', (EX.x1, EX.p, EX.x2, EX['g1/']), True),
                ('p12', (EX.x1, EX.p, EX.x2, EX['g1/g2']), False),
                ('p12', (EX.x1, EX.p, EX.x2, EX['pab/ga']), False),
                ('p12', (EX.x2, EX.p, EX.x3, EX['g1/']), False),
                ('p12', (EX.x2, EX.p, EX.x3, EX['g1/g2']), True),
                ('p12', (EX.x3, EX.p, EX.x4, EX['g1/']), False),
                ('p12', (EX.x3, EX.p, EX.x4, EX['g1/g2']), True),
                ('p12', (EX.xa, EX.p, EX.xb, EX['pab/ga']), False),
                ('p12', (EX.xa, EX.p, EX.xb, EX['pab/gb']), False),
                ('p12', (EX.xb, EX.p, EX.xc, EX['pab/ga']), False),
                ('p12', (EX.xb, EX.p, EX.xc, EX['pab/gb']), False),

                ('pab', (EX.x1, EX.p, EX.x2, EX['g1/']), False),
                ('pab', (EX.x1, EX.p, EX.x2, EX['g1/g2']), False),
                ('pab', (EX.x2, EX.p, EX.x3, EX['g1/']), False),
                ('pab', (EX.x2, EX.p, EX.x3, EX['g1/g2']), False),
                ('pab', (EX.x3, EX.p, EX.x4, EX['g1/']), False),
                ('pab', (EX.x3, EX.p, EX.x4, EX['g1/g2']), False),
                ('pab', (EX.xa, EX.p, EX.xb, EX['pab/ga']), True),
                ('pab', (EX.xa, EX.p, EX.xb, EX['pab/gb']), False),
                ('pab', (EX.xb, EX.p, EX.xc, EX['pab/ga']), False),
                ('pab', (EX.xb, EX.p, EX.xc, EX['pab/gb']), True),
                ('pab', (EX.xb, EX.p, EX.xc, EX['g1/']), False),
    ])
    def test_contains(self, datasetname, triple_or_quad, expected):
        dataset = getattr(self, datasetname)
        assert (triple_or_quad in dataset) == expected, triple_or_quad

    @mark.parametrize("datasetname, triple_or_quad, expected", [
                ('p12', (EX.x1, EX.p, EX.x2), {(EX.x1, EX.p, EX.x2)}),
                ('p12', (EX.x2, EX.p, EX.x3), {(EX.x2, EX.p, EX.x3)}),
                ('p12', (EX.x3, EX.p, EX.x4), {(EX.x3, EX.p, EX.x4)}),
                ('p12', (EX.xa, EX.p, EX.xb), set()),
                ('p12', (EX.xb, EX.p, EX.xc), set()),
                ('p12', (EX.x0, EX.p, EX.xc), set()),

                ('pab', (EX.x1, EX.p, EX.x2), set()),
                ('pab', (EX.x2, EX.p, EX.x3), set()),
                ('pab', (EX.x3, EX.p, EX.x4), set()),
                ('pab', (EX.xa, EX.p, EX.xb), {(EX.xa, EX.p, EX.xb)}),
                ('pab', (EX.xb, EX.p, EX.xc), {(EX.xb, EX.p, EX.xc)}),
                ('pab', (EX.x0, EX.p, EX.xc), set()),

                ('p12', (EX.x1, EX.p, EX.x2, EX['g1/']), {(EX.x1, EX.p, EX.x2)}),
                ('p12', (EX.x1, EX.p, EX.x2, EX['g1/g2']), set()),
                ('p12', (EX.x2, EX.p, EX.x3, EX['g1/']), set()),
                ('p12', (EX.x2, EX.p, EX.x3, EX['g1/g2']), {(EX.x2, EX.p, EX.x3)}),
                ('p12', (EX.x3, EX.p, EX.x4, EX['g1/']), set()),
                ('p12', (EX.x3, EX.p, EX.x4, EX['g1/g2']), {(EX.x3, EX.p, EX.x4)}),
                ('p12', (EX.xa, EX.p, EX.xb, EX['pab/ga']), set()),
                ('p12', (EX.xa, EX.p, EX.xb, EX['pab/gb']), set()),
                ('p12', (EX.xb, EX.p, EX.xc, EX['pab/ga']), set()),
                ('p12', (EX.xb, EX.p, EX.xc, EX['pab/gb']), set()),

                ('pab', (EX.x1, EX.p, EX.x2, EX['g1/']), set()),
                ('pab', (EX.x1, EX.p, EX.x2, EX['g1/g2']), set()),
                ('pab', (EX.x2, EX.p, EX.x3, EX['g1/']), set()),
                ('pab', (EX.x2, EX.p, EX.x3, EX['g1/g2']), set()),
                ('pab', (EX.x3, EX.p, EX.x4, EX['g1/']), set()),
                ('pab', (EX.x3, EX.p, EX.x4, EX['g1/g2']), set()),
                ('pab', (EX.xa, EX.p, EX.xb, EX['pab/ga']), {(EX.xa, EX.p, EX.xb)}),
                ('pab', (EX.xa, EX.p, EX.xb, EX['pab/gb']), set()),
                ('pab', (EX.xb, EX.p, EX.xc, EX['pab/ga']), set()),
                ('pab', (EX.xb, EX.p, EX.xc, EX['pab/gb']), {(EX.xb, EX.p, EX.xc)}),

                ('p12', (EX.x1, None, None), {(EX.x1, EX.p, EX.x2)}),
                ('p12', (EX.x2, None, None), {(EX.x2, EX.p, EX.x3)}),
                ('p12', (EX.x3, None, None), {(EX.x3, EX.p, EX.x4)}),
                ('p12', (EX.xa, None, None), set()),
                ('p12', (EX.xb, None, None), set()),
                ('p12', (EX.x0, None, None), set()),

                ('pab', (EX.x1, None, None), set()),
                ('pab', (EX.x2, None, None), set()),
                ('pab', (EX.x3, None, None), set()),
                ('pab', (EX.xa, None, None), {(EX.xa, EX.p, EX.xb)}),
                ('pab', (EX.xb, None, None), {(EX.xb, EX.p, EX.xc)}),
                ('pab', (EX.x0, None, None), set()),

                ('p12', (EX.x1, None, None, EX['g1/']), {(EX.x1, EX.p, EX.x2)}),
                ('p12', (EX.x1, None, None, EX['g1/g2']), set()),
                ('p12', (EX.x2, None, None, EX['g1/']), set()),
                ('p12', (EX.x2, None, None, EX['g1/g2']), {(EX.x2, EX.p, EX.x3)}),
                ('p12', (EX.x3, None, None, EX['g1/']), set()),
                ('p12', (EX.x3, None, None, EX['g1/g2']), {(EX.x3, EX.p, EX.x4)}),
                ('p12', (EX.xa, None, None, EX['pab/ga']), set()),
                ('p12', (EX.xa, None, None, EX['pab/gb']), set()),
                ('p12', (EX.xb, None, None, EX['pab/ga']), set()),
                ('p12', (EX.xb, None, None, EX['pab/gb']), set()),

                ('pab', (EX.x1, None, None, EX['g1/']), set()),
                ('pab', (EX.x1, None, None, EX['g1/g2']), set()),
                ('pab', (EX.x2, None, None, EX['g1/']), set()),
                ('pab', (EX.x2, None, None, EX['g1/g2']), set()),
                ('pab', (EX.x3, None, None, EX['g1/']), set()),
                ('pab', (EX.x3, None, None, EX['g1/g2']), set()),
                ('pab', (EX.xa, None, None, EX['pab/ga']), {(EX.xa, EX.p, EX.xb)}),
                ('pab', (EX.xa, None, None, EX['pab/gb']), set()),
                ('pab', (EX.xb, None, None, EX['pab/ga']), set()),
                ('pab', (EX.xb, None, None, EX['pab/gb']), {(EX.xb, EX.p, EX.xc)}),

                ('p12', (None, None, None), {(EX.x1, EX.p, EX.x2),
                                             (EX.x2, EX.p, EX.x3),
                                             (EX.x3, EX.p, EX.x4),
                }),
                ('pab', (None, None, None), {(EX.xa, EX.p, EX.xb),
                                             (EX.xb, EX.p, EX.xc),
                }),

                ('p12', (None, None, None, EX['g1/']), {
                    (EX.x1, EX.p, EX.x2),
                }),
                ('p12', (None, None, None, EX['g1/g2']), {
                    (EX.x2, EX.p, EX.x3),
                    (EX.x3, EX.p, EX.x4),
                }),
                ('p12', (None, None, None, EX['pab/ga']), set()),

                ('pab', (None, None, None, EX['pab/ga']), {
                    (EX.xa, EX.p, EX.xb),
                }),
                ('pab', (None, None, None, EX['pab/gb']), {
                    (EX.xb, EX.p, EX.xc),
                }),
                ('pab', (None, None, None, EX['g1/']), set()),
    ])
    def test_triples(self, datasetname, triple_or_quad, expected):
        dataset = getattr(self, datasetname)
        assert set(dataset.triples(triple_or_quad)) == set(expected)

    PP = EX.p/EX.p

    @mark.parametrize("datasetname, triple_or_quad, expected", [
                ('p12', (None, PP, None), {(EX.x1, PP, EX.x3),
                                           (EX.x2, PP, EX.x4),
                }),
                ('pab', (None, PP, None), {(EX.xa, PP, EX.xc),
                }),

                ('p12', (None, PP, None, EX['g1/']), set()),
                ('p12', (None, PP, None, EX['g1/g2']), {(EX.x2, PP, EX.x4)}),
                ('p12', (None, PP, None, EX['pab/ga']), set()),

                ('pab', (None, PP, None, EX['pab/ga']), set()),
                ('pab', (None, PP, None, EX['pab/gb']), set()),
                ('pab', (None, PP, None, EX['g1/g2']), set()),
    ])
    def test_triples_with_path(self, datasetname, triple_or_quad, expected):
        dataset = getattr(self, datasetname)
        assert set(dataset.triples(triple_or_quad)) == set(expected)


    @mark.skip('not implemented yet')
    @mark.parametrize("datasetname, triple, contextname, expected", [
                ('p12', ([EX.x1,EX.x2], EX.p, None), None, {
                    (EX.x1, EX.p, EX.x2),
                    (EX.x2, EX.p, EX.x3),
                }),
                ('p12', ([EX.x1,EX.x2], EX.p, None), 'g1', {
                    (EX.x1, EX.p, EX.x2),
                }),
                ('p12', ([EX.x1,EX.x2], EX.p, None), 'g2', {
                    (EX.x2, EX.p, EX.x3),
                }),
    ])
    def test_triples_choices(self, datasetname, triple, contextname, expected):
        dataset = getattr(self, datasetname)
        context = contextname and getattr(self, contextname) or None
        assert set(dataset.triples_choices(triple, context)) == set(expected)

    @mark.parametrize("datasetname, triple_or_quad, expected", [
                ('p12', (EX.x1, EX.p, EX.x2), {(EX.x1, EX.p, EX.x2, EX['g1/'])}),
                ('p12', (EX.x2, EX.p, EX.x3), {(EX.x2, EX.p, EX.x3, EX['g1/g2'])}),
                ('p12', (EX.x3, EX.p, EX.x4), {(EX.x3, EX.p, EX.x4, EX['g1/g2'])}),
                ('p12', (EX.xa, EX.p, EX.xb), set()),
                ('p12', (EX.xb, EX.p, EX.xc), set()),
                ('p12', (EX.x0, EX.p, EX.xc), set()),

                ('pab', (EX.x1, EX.p, EX.x2), set()),
                ('pab', (EX.x2, EX.p, EX.x3), set()),
                ('pab', (EX.x3, EX.p, EX.x4), set()),
                ('pab', (EX.xa, EX.p, EX.xb), {(EX.xa, EX.p, EX.xb, EX['pab/ga'])}),
                ('pab', (EX.xb, EX.p, EX.xc), {(EX.xb, EX.p, EX.xc, EX['pab/gb'])}),
                ('pab', (EX.x0, EX.p, EX.xc), set()),

                ('p12', (EX.x1, EX.p, EX.x2, EX['g1/']), {(EX.x1, EX.p, EX.x2, EX['g1/'])}),
                ('p12', (EX.x1, EX.p, EX.x2, EX['g1/g2']), set()),
                ('p12', (EX.x2, EX.p, EX.x3, EX['g1/']), set()),
                ('p12', (EX.x2, EX.p, EX.x3, EX['g1/g2']), {(EX.x2, EX.p, EX.x3, EX['g1/g2'])}),
                ('p12', (EX.x3, EX.p, EX.x4, EX['g1/']), set()),
                ('p12', (EX.x3, EX.p, EX.x4, EX['g1/g2']), {(EX.x3, EX.p, EX.x4, EX['g1/g2'])}),
                ('p12', (EX.xa, EX.p, EX.xb, EX['pab/ga']), set()),
                ('p12', (EX.xa, EX.p, EX.xb, EX['pab/gb']), set()),
                ('p12', (EX.xb, EX.p, EX.xc, EX['pab/ga']), set()),
                ('p12', (EX.xb, EX.p, EX.xc, EX['pab/gb']), set()),

                ('pab', (EX.x1, EX.p, EX.x2, EX['g1/']), set()),
                ('pab', (EX.x1, EX.p, EX.x2, EX['g1/g2']), set()),
                ('pab', (EX.x2, EX.p, EX.x3, EX['g1/']), set()),
                ('pab', (EX.x2, EX.p, EX.x3, EX['g1/g2']), set()),
                ('pab', (EX.x3, EX.p, EX.x4, EX['g1/']), set()),
                ('pab', (EX.x3, EX.p, EX.x4, EX['g1/g2']), set()),
                ('pab', (EX.xa, EX.p, EX.xb, EX['pab/ga']), {(EX.xa, EX.p, EX.xb, EX['pab/ga'])}),
                ('pab', (EX.xa, EX.p, EX.xb, EX['pab/gb']), set()),
                ('pab', (EX.xb, EX.p, EX.xc, EX['pab/ga']), set()),
                ('pab', (EX.xb, EX.p, EX.xc, EX['pab/gb']), {(EX.xb, EX.p, EX.xc, EX['pab/gb'])}),

                ('p12', (EX.x1, None, None), {(EX.x1, EX.p, EX.x2, EX['g1/'])}),
                ('p12', (EX.x2, None, None), {(EX.x2, EX.p, EX.x3, EX['g1/g2'])}),
                ('p12', (EX.x3, None, None), {(EX.x3, EX.p, EX.x4, EX['g1/g2'])}),
                ('p12', (EX.xa, None, None), set()),
                ('p12', (EX.xb, None, None), set()),
                ('p12', (EX.x0, None, None), set()),

                ('pab', (EX.x1, None, None), set()),
                ('pab', (EX.x2, None, None), set()),
                ('pab', (EX.x3, None, None), set()),
                ('pab', (EX.xa, None, None), {(EX.xa, EX.p, EX.xb, EX['pab/ga'])}),
                ('pab', (EX.xb, None, None), {(EX.xb, EX.p, EX.xc, EX['pab/gb'])}),
                ('pab', (EX.x0, None, None), set()),

                ('p12', (EX.x1, None, None, EX['g1/']), {(EX.x1, EX.p, EX.x2, EX['g1/'])}),
                ('p12', (EX.x1, None, None, EX['g1/g2']), set()),
                ('p12', (EX.x2, None, None, EX['g1/']), set()),
                ('p12', (EX.x2, None, None, EX['g1/g2']), {(EX.x2, EX.p, EX.x3, EX['g1/g2'])}),
                ('p12', (EX.x3, None, None, EX['g1/']), set()),
                ('p12', (EX.x3, None, None, EX['g1/g2']), {(EX.x3, EX.p, EX.x4, EX['g1/g2'])}),
                ('p12', (EX.xa, None, None, EX['pab/ga']), set()),
                ('p12', (EX.xa, None, None, EX['pab/gb']), set()),
                ('p12', (EX.xb, None, None, EX['pab/ga']), set()),
                ('p12', (EX.xb, None, None, EX['pab/gb']), set()),

                ('pab', (EX.x1, None, None, EX['g1/']), set()),
                ('pab', (EX.x1, None, None, EX['g1/g2']), set()),
                ('pab', (EX.x2, None, None, EX['g1/']), set()),
                ('pab', (EX.x2, None, None, EX['g1/g2']), set()),
                ('pab', (EX.x3, None, None, EX['g1/']), set()),
                ('pab', (EX.x3, None, None, EX['g1/g2']), set()),
                ('pab', (EX.xa, None, None, EX['pab/ga']), {(EX.xa, EX.p, EX.xb, EX['pab/ga'])}),
                ('pab', (EX.xa, None, None, EX['pab/gb']), set()),
                ('pab', (EX.xb, None, None, EX['pab/ga']), set()),
                ('pab', (EX.xb, None, None, EX['pab/gb']), {(EX.xb, EX.p, EX.xc, EX['pab/gb'])}),

                ('p12', (None, None, None), {(EX.x1, EX.p, EX.x2, EX['g1/']),
                                             (EX.x2, EX.p, EX.x3, EX['g1/g2']),
                                             (EX.x3, EX.p, EX.x4, EX['g1/g2']),
                }),
                ('pab', (None, None, None), {(EX.xa, EX.p, EX.xb, EX['pab/ga']),
                                             (EX.xb, EX.p, EX.xc, EX['pab/gb']),
                }),

                ('p12', (None, None, None, EX['g1/']), {
                    (EX.x1, EX.p, EX.x2, EX['g1/']),
                }),
                ('p12', (None, None, None, EX['g1/g2']), {
                    (EX.x2, EX.p, EX.x3, EX['g1/g2']),
                    (EX.x3, EX.p, EX.x4, EX['g1/g2']),
                }),
                ('p12', (None, None, None, EX['pab/ga']), {
                }),

                ('pab', (None, None, None, EX['pab/ga']), {
                    (EX.xa, EX.p, EX.xb, EX['pab/ga']),
                }),
                ('pab', (None, None, None, EX['pab/gb']), {
                    (EX.xb, EX.p, EX.xc, EX['pab/gb']),
                }),
                ('pab', (None, None, None, EX['g1/']), {
                }),
    ])
    def test_quads(self, datasetname, triple_or_quad, expected):
        dataset = getattr(self, datasetname)
        quads = set( (s, p, o, ctx.identifier)
                     for s, p, o, ctx
                     in dataset.quads(triple_or_quad)
        )
        assert quads == set(expected)

    @mark.parametrize("datasetname, sparql, expected", [
                ('p12', 'select ?s { ?s ?p ?o } order by ?s', [(EX.x1,),
                                                               (EX.x2,),
                                                               (EX.x3,),
                ]),
                ('pab', 'select ?s { ?s ?p ?o } order by ?s', [(EX.xa,),
                                                               (EX.xb,),
                ]),
                ('p12', 'select ?g ?s { graph ?g {?s ?p ?o} } order by ?s', [
                    (EX['g1/'],   EX.x1,),
                    (EX['g1/g2'], EX.x2,),
                    (EX['g1/g2'], EX.x3,),
                ]),
                ('pab', 'select ?g ?s { graph ?g {?s ?p ?o} } order by ?s', [
                    (EX['pab/ga'], EX.xa,),
                    (EX['pab/gb'], EX.xb,),
                ]),
    ])
    def test_sparql_select(self, datasetname, sparql, expected):
        dataset = getattr(self, datasetname)
        result = dataset.query(sparql)
        if isinstance(expected, list):
            assert list(result) == expected
        else:
            assert set(result) == expected

    @mark.parametrize("datasetname, sparql, expected", [
                ('p12', 'construct { ?s ?p ?s } where { ?s ?p ?o }', {
                    (EX.x1, EX.p, EX.x1),
                    (EX.x2, EX.p, EX.x2),
                    (EX.x3, EX.p, EX.x3),
                }),
                ('pab', 'construct { ?s ?p ?s } where { ?s ?p ?o }', {
                    (EX.xa, EX.p, EX.xa),
                    (EX.xb, EX.p, EX.xb),
                }),
                ('p12', 'construct { ?g ?p ?s } where { graph ?g {?s ?p ?o} }', {
                    (EX['g1/'],   EX.p, EX.x1,),
                    (EX['g1/g2'], EX.p, EX.x2,),
                    (EX['g1/g2'], EX.p, EX.x3,),
                }),
                ('pab', 'construct { ?g ?p ?s } where { graph ?g {?s ?p ?o} }', {
                    (EX['pab/ga'], EX.p, EX.xa,),
                    (EX['pab/gb'], EX.p, EX.xb,),
                }),
    ])
    def test_sparql_construct(self, datasetname, sparql, expected):
        dataset = getattr(self, datasetname)
        result = dataset.query(sparql)
        if isinstance(expected, list):
            assert list(result) == expected
        else:
            assert set(result) == expected

    @mark.parametrize("datasetname", ['p12', 'pab'])
    @mark.parametrize("sparql", [
                    'select * from <> { ?s ?p ?o }',
                    'select * from named <> { ?s ?p ?o }',
                    'select * from <> from named <> { ?s ?p ?o }',
    ])
    def test_sparql_with_from(self, datasetname, sparql):
        dataset = getattr(self, datasetname)
        with assert_raises(ValueError):
            dataset.query(sparql)

virtuoso_store = os.environ.get('RDFREST_VIRTUOSO_STORED')
if virtuoso_store:
    try:
        from virtuoso.vstore import Virtuoso
        _ = Virtuoso(virtuoso_store)

        class TestVirtuoso(TestDefaultStore):

            def get_store(self):
                return Virtuoso(virtuoso_store)

    except (ImportError, pyodbc.Error) as ex:

        @skip('Virtuoso store not available')
        def TestVirtuoso():
            pass
else:
    @skip('No Virtuoso store configured for testing')
    def TestVirtuoso():
        pass
