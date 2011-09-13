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

from datetime import datetime

from optparse import OptionParser

from ktbs.client.root import KtbsRoot
from rdfrest.utils import coerce_to_uri


# TODO "http://liris.cnrs.fr/silex/2010/simple-trace-model"
MODEL_URI = "http://localhost:8001/base1/model1/"
# TODO 1970-01-01T00:00:00Z
TRACE_ORIGIN = ""
# @prefix m: <http://liris.cnrs.fr/silex/2010/simple-trace-model#>
PREFIX = "http://localhost:8001/base1/model1#"

class ObselCollector(object):
    """
    A simple collector class that populates the KTBS with collected obsels.
    """

    _parser = None
    _options = None
    _args = None

    def __init__(self):
        """
        Define simple collector parser and its command line options.
        """
        self._parser = OptionParser()

        self._parser.add_option("-t", "--trace-uri", 
                              dest="trace_uri",
                              help="Enter the uri of the trace that will \
                                    contain the collected obsels")

        (self._options, self._args) = self._parser.parse_args()

    def validate_entries(self):
        """
        Check user entries, the trace URI in fact.
        """
        if self._options.trace_uri is not None:
            print "----- %s" % self._options.trace_uri

            # Transform URI string to an rdflib URIRef
            return (coerce_to_uri(self._options.trace_uri))

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

        for b in root.list_bases():
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
                    tbase = root.create_base(label="%s" % base_name) #, id="%s/" % base_name)

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

        for t in base.list_traces():
            if trace_uri.find(t.uri) != -1:
                print "----- The trace %s already exists" % trace_uri
                ttrace = t

                # TODO Check trace model and origin
                tmodel = ttrace.get_model()
                if tmodel is not None:
                    print "----- %s model uri: %s" % (ttrace.label, tmodel.uri)

                print "----- %s origin: %s" % (ttrace.label, ttrace.get_origin())

        if ttrace is None:
            # TODO create trace
            print "----- No matching trace found, creating ..."

        if ttrace is not None:
            print "----- trace.label: ", ttrace.label

        return ttrace

    def add_obsel(self):
        """
        ce programme lit sur son entrée standard et pour chaque ligne lue, 
        crée un obsel ayant les propriétés suivantes

            ktbs:beginDT  le temps courant
            ktbs:endDT    le temps courant
            ktbs:subject  la valeur de la variable d'environnement USER
            m:value       la ligne de texte lue

        en supposant:
            @prefix m: <http://liris.cnrs.fr/silex/2010/simple-trace-model#>

        pour le temps courant
        ../test/test.py:    g.add((t01_uri, KTBS.hasOrigin, Literal(str(datetime.now()))))
        """
        obsel = None

        return obsel

if __name__ == "__main__":
    ocollector = ObselCollector()
    turi =  ocollector.validate_entries() 

    if turi is None:
        sys.exit("No valid URI, programm stopped.")

    tbase = ocollector.get_base(turi)

    if tbase is None:
        sys.exit("No valid base in URI, programm stopped.")

    ttrace = ocollector.get_trace(tbase, turi)

    sys.exit(0)
