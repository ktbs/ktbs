#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simple collector program that populates the KTBS with collected obsels.
"""

import sys
from os.path import abspath, dirname, join

source_dir = dirname(dirname(abspath(__file__)))
lib_dir = join(source_dir, "lib")
sys.path.insert(0, lib_dir)

from optparse import OptionParser

from datetime import datetime

from pprint import pprint

from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef

from ktbs.namespaces import KTBS, SKOS
from ktbs.client.root import KtbsRoot
from ktbs.client.base import Base as KtbsBase
from ktbs.common.utils import post_graph
from rdfrest.utils import coerce_to_uri


#MODEL_URI = "http://localhost:8001/base1/model1"
MODEL_URI = "http://liris.cnrs.fr/silex/2011/simple-trace-model"
TRACE_ORIGIN = "1970-01-01T00:00:00Z"
#MODEL_PREFIX = "@prefix m: <http://localhost:8001/base1/model1#"
MODEL_PREFIX = "@prefix m: <http://liris.cnrs.fr/silex/2011/simple-trace-model#>"
OBSEL_TYPE = "SimpleObsel"

class ObselCollector(object):
    """
    A simple collector class that populates the KTBS with collected obsels.
    """

    def __init__(self):
        """
        Define simple collector parser and its command line options.
        To begin, we just ask for a Trace URI which is mandatory.
        """
        self._parser = OptionParser()

        (self._options, self._args) = self._parser.parse_args()

    def validate_entries(self):
        """
        Check user entries, the trace URI in fact.
        """
        if len(self._args) > 0:
            print "----- %s" % self._args[0]

            # Transform URI string to an rdflib URIRef
            return (coerce_to_uri(self._args[0]))

        return None

    def get_base(self, trace_uri):
        """
        Get the KTBS Base object for the trace whose URI has been passed. 
        If it does not exist, create it.
        """

        # Get a KTBS access 
        root = KtbsRoot("http://localhost:8001/")
        print "----- root.label: ", root.label

        tbase = None

        for b in root.bases:
            base_uri = b.uri

            if trace_uri.find(base_uri) != -1:
                print "----- %s is the base of %s" % (base_uri, trace_uri)
                tbase = b
            else:
                print "----- %s base does not match" % base_uri

        if tbase is None:
            print "----- No matching base found, creating ..."

            root_uri = root.uri
            if (trace_uri.find(root_uri) == 0) and (len(trace_uri) > len(root_uri)):
                wrkuri = trace_uri[len(root_uri):]
                if wrkuri.find('/') != -1:
                    # We should have base_name/trace_name/
                    base_name = wrkuri.split('/')[0]
                    tbase = root.create_base(label="%s" % base_name, id="%s/" % base_name)

                    # Add a default model
                    #tbase.create_model(id=MODEL_URI)

        if tbase is not None:
            print "----- base.label: ", tbase.label

        return tbase

    def get_trace(self, base, trace_uri):
        """
        Get the KTBS StoredTrace object for the trace whose URI has been passed.
        If found, check the model and the origin.
        If it does not exist, create it.
        """
        ttrace = None

        for t in base.traces:
            if trace_uri.find(t.uri) != -1:
                print "----- The trace %s already exists" % trace_uri
                ttrace = t

                # TODO Check trace model and origin
                tmodel = ttrace.model
                if tmodel is not None:
                    print "----- %s model uri: %s" % (ttrace.label, tmodel.uri)
                    print "-----", [ot.uri for ot in tmodel.obsel_types]
                else:
                    print "----- %s model is None" % ttrace.label 

                print "----- %s origin: %s" % (ttrace.label, ttrace.origin)

        if ttrace is None:
            # TODO create trace
            print "----- No matching trace found, creating ..."

            base_uri = base.uri
            if (trace_uri.find(base_uri) == 0) and (len(trace_uri) > len(base_uri)):
                wrkuri = trace_uri[len(base_uri):]
                if wrkuri.find('/') != -1:
                    trace_name = wrkuri.split('/')[0]

                    """
                    model_uri = None

                    bmodels = base.list_models()
                    if len(bmodels) > 0:

                        # If there are several models, select the one
                        # that matches MODEL_URI
                        for m in bmodels:
                            if m.uri.find(MODEL_URI) != -1:
                                model_uri = m.uri

                        if model_uri is None:
                            # Take the first model by default
                            model_uri = bmodels[0].uri
                            print "----- No model matches %s, %s selected" % \
                                                         (MODEL_URI, model_uri)

                        ttrace = base.create_stored_trace(model=model_uri,
                                                          origin=TRACE_ORIGIN,
                                                          #label="%s" % 
                                                          #     trace_name,
                                                          id="%s/" % 
                                                          trace_name)

                    if model_uri is None:
                        # TODO Create an empty one ?
                        print "----- No model associated to %s," % base_uri, \
                              "trace not created" 
                    """

                    ttrace = base.create_stored_trace(model=MODEL_URI,
                                                      origin=TRACE_ORIGIN,
                                                      #label="%s" % 
                                                      #     trace_name,
                                                      id="%s/" % 
                                                      trace_name)

        if ttrace is not None:
            print "----- trace.label: ", ttrace.label

        return ttrace

    def add_model(self, base):
        """
        Temporary method, waiting the definitive model to be ready ?
        """
        assert isinstance(base, KtbsBase)
        print "----- No model found for %s, creating ..." % base.label

        tmodel = base.create_model(id="model1")
        if tmodel is not None:
            simpleobseltype = tmodel.create_obsel_type("SimpleObsel")
        return tmodel

    def add_obsel(self, trace, value):
        """
        ce programme lit sur son entrée standard et pour chaque ligne lue, 
        crée un obsel ayant les propriétés suivantes

            ktbs:beginDT  le temps courant
            ktbs:endDT    le temps courant
            ktbs:subject  la valeur de la variable d'environnement USER
            m:value       la ligne de texte lue

        en supposant:
            @prefix m: <http://liris.cnrs.fr/silex/2011/simple-trace-model#>
        """
        """
        tmodel = trace.get_model()
        print "dbg-- add_obsel, model = %s" % tmodel.label
        otypes = tmodel.list_obsel_types()
        print "dbg-- add_obsel, list_obsel_types: %s" % otypes
        if len(otypes) > 0:
            simpleotype = otypes[0]
        """

        obsel = trace.create_obsel(type=OBSEL_TYPE,
                                   begin=Literal(str(datetime.now())),
                                   end=Literal(str(datetime.now())),
                                   subject="me",
                                   label=value)

        return obsel

if __name__ == "__main__":
    ocollector = ObselCollector()

    turi =  ocollector.validate_entries() 

    if turi is None:
        sys.exit("No valid URI, programm stopped.")

    tbase = ocollector.get_base(turi)

    if tbase is None:
        sys.exit("No valid base in URI, programm stopped.")

    #if len(tbase.models) == 0:
    #    ocollector.add_model(tbase)

    ttrace = ocollector.get_trace(tbase, turi)

    if ttrace is None:
        sys.exit("Trace not created, programm stopped.")

    while(True):
        value = raw_input("====> ")
        if (value.find("exit",0,5) != -1) or (value.find("quit",0,5) != -1):
            print "Sortie du programme"
            break
        ocollector.add_obsel(ttrace, value)

    sys.exit(0)
