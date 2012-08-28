#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
http://kb.mozillazine.org/Places.sqlite
The file "places.sqlite" stores the annotations, bookmarks, favorite icons, 
input history, keywords, and browsing history (a record of visited pages). 

places.sqlite is a file in the profile folder.
Unix/Linux      ~/.mozilla/
Mac OS X        ~/Library/Mozilla/
                ~/Library/Application Support/ 
Windows         "%APPDATA%\Mozilla\"

https://developer.mozilla.org/en/The_Places_database

The places.sqlite includes a number of tables as follows:
  moz_anno_attributes - Annotation Attributes
  moz_annos - Annotations
  moz_bookmarks - Bookmarks
  moz_bookmarks_roots - Bookmark roots i.e. places, menu, toolbar, tags, unfiled
  moz_favicons - Favourite icons - including URL of icon
  moz_historyvisits - A history of the number of times a site has been visited
  moz_inputhistory - A history of URLS typed by the user
  moz_items_annos - Item annotations
  moz_keywords - Keywords
  moz_places - Places/Sites visited - referenced by moz_historyvisits 

--------------------------------------------------------------------------------
http://brizoma.wordpress.com/2010/12/19/firefox-sqlite-and-places-structure/

https://wiki.mozilla.org/Places
https://developer.mozilla.org/en/The_Places_frecency_algorithm
--------------------------------------------------------------------------------
CREATE TABLE moz_places (id INTEGER PRIMARY KEY, 
                         url LONGVARCHAR, 
                         title LONGVARCHAR,
                         rev_host LONGVARCHAR,
                         visit_count INTEGER DEFAULT 0,
                         hidden INTEGER DEFAULT 0 NOT NULL,
                         typed INTEGER DEFAULT 0 NOT NULL,
                         favicon_id INTEGER,
                         frecency INTEGER DEFAULT -1 NOT NULL,
                         last_visit_date INTEGER,
                         guid TEXT);

last_visit_date semble être un timestamp Unix : nbre de second depuis 01/01/1970
                http://www.unixtimestamp.com/index.php
                sauf qu'il comporte 16 digits au lieu de 10 !
                Il semble donc que ce soit le nombre de microsecondes depuis le
                01/01/1970
                http://www.developpez.net/forums/d726298/bases-donnees/autres-
                       sgbd/sqlite/decodage-timestamp-firefox/

--------------------------------------------------------------------------------
http://docs.python.org/library/sqlite3.html
"""

import os
import sys
import sqlite3
import datetime
import math

import time
from processinfo import ProcessInfo

import cProfile

from argparse import ArgumentParser

# Peut-on éviter URIRef ...
from rdflib import URIRef, XSD

try:
    from ktbs.client import get_ktbs
except:
    from os.path import abspath, dirname, join

    source_dir = dirname(dirname(dirname(dirname(abspath(__file__)))))
    lib_dir = join(source_dir, "lib")
    sys.path.insert(0, lib_dir)

    from ktbs.client import get_ktbs

from rdfrest.proxystore import ResourceAccessError

# General
NB_MAX_ITEMS = 10000

# Firefox history file
FIREFOX_HISTORY = "places.sqlite"

# kTBS elements
KTBS_ROOT = "http://localhost:8001/"
TRACE_ORIGIN = "1970-01-01T00:00:00Z"

BH_OBSEL_ID = "#BHObsel"
BH_OBSEL_LABEL = "Brower History Obsel"

class BrowserHistoryCollector(object):
    """
    Creates a kTBS Base for browser history data.
    This code is for Firefox browser.
    """

    def __init__ (self, process_info=None):
        """
        Define simple collector parser and its command line options.
        To begin, we just ask for a kTBS root which is mandatory.
        """
        self._parser = ArgumentParser(description="Fill a stored trace with \
                                                   browser history items as \
                                                   obsels.")

        self._parser.add_argument("-f", "--file", 
                                  nargs="?", 
                                  const=FIREFOX_HISTORY, 
                                  default=FIREFOX_HISTORY,
                                  help="File containings the sqlite data to \
                                        parse. Default is %s" % FIREFOX_HISTORY)

        self._parser.add_argument("-r", "--root", 
                                  nargs="?", 
                                  const=KTBS_ROOT, default=KTBS_ROOT,
                                  help="Enter the uri of the kTBS root. \
                                        Default is %s" % KTBS_ROOT)

        self._parser.add_argument("-o", "--origin", 
                                  nargs="?", 
                                  const=TRACE_ORIGIN, default=TRACE_ORIGIN,
                                  help="Enter the trace origin. Default is \
                                        %s" % TRACE_ORIGIN)

        self._parser.add_argument("-l", "--limit", 
                                  nargs="?", type=int,
                                  const=NB_MAX_ITEMS, default=NB_MAX_ITEMS,
                                  help="Enter the maximun number of items to \
                                        collect. Default is %s" % NB_MAX_ITEMS)

        self._parser.add_argument("-p", "--profile",
                                  action="store_true",
                                  help="Profile current code")

        self._parser.add_argument("-s", "--stats",
                                  action="store_true",
                                  help="Mesure execution time")

        self._parser.add_argument("-v", "--verbose",
                                  action="store_true",
                                  help="Display print messages")

        self._args = self._parser.parse_args()
        self.display("Parsed with argparse: %s" % str(self._args))

        if self._args.stats:
            # To get process information without callback mechanism
            my_PID = os.getpid()
            self.process_info = ProcessInfo(my_PID)

    def display(self, msg):
        """
        Display the messages only in verbose mode.
        """
        if self._args.verbose:
            print msg

    def profiling_asked(self):
        """Has profiling been asked in command line ?
        """
        return self._args.profile

    def create_ktbs_base_for_history(self):
        """
        Creates a kTBS Base for browser history data.
        """
        root = get_ktbs(self._args.root)

        base = root.get_base(id="BrowserHistory/")

        if base is None:
            base = root.create_base(id="BrowserHistory/")

        return base


    def create_ktbs_model_for_history(self, base=None):
        """
        Creates a kTBS Model for browser history data.
        """
        model = base.create_model(id="BHModel")

        #pylint: disable-msg=W0612
        # Unused variable obsel_type
        bh_obsel_type = model.create_obsel_type(id=BH_OBSEL_ID, 
                                                label=BH_OBSEL_LABEL)

        # Browser history obsel attributes
        # id, url, title, rev_host, visit_count, hidden, typed, favicon_id, 
        # frecency, last_visit_date

        nb_visit_attr_type = model.create_attribute_type(
                                                  id="#visit_count",
                                                  obsel_type=bh_obsel_type, 
                                                  data_type=XSD.integer) 

        title_attr_type = model.create_attribute_type(
                                                  id="#title",
                                                  obsel_type=bh_obsel_type, 
                                                  data_type=XSD.string)

        frequency_attr_type = model.create_attribute_type(
                                                  id="#frequency",
                                                  obsel_type=bh_obsel_type, 
                                                  data_type=XSD.integer) 

        return model

    def create_ktbs_trace_for_history(self, base=None, model=None):
        """
        Creates a kTBS Trace for browser history data.
        """
        trace = base.create_stored_trace(id="RawHistory/",
                                         model=model.get_uri(), 
                                         origin=self._args.origin)
                                         
        return trace

    def collect_history_items(self, trace=None):
        """
        Open the browser history database, extract history items and
        populates a kTBS stored trace with it.
        """
        obsels_list = []

        try:
            if self._args.stats:
                start_time = time.time()
                start_cpu = time.clock()

            # http://docs.python.org/library/sqlite3.html#accessing-columns-
            # by-name-instead-of-by-index
            conn = sqlite3.connect(self._args.file, 
                                   detect_types=sqlite3.PARSE_COLNAMES)
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            # If obsels are not inserted in chronological order 
            # We get a "Non-monotonic collection error"
            cursor.execute('SELECT * FROM moz_places WHERE last_visit_date IS NOT NULL ORDER BY last_visit_date')

            # Get Model Information : should we store it ? 
            model = trace.get_model()

            # Get obsel type URI
            bh_obsel_type = model.get(id=BH_OBSEL_ID)

            # Get attributes types uris
            model_attributes = model.list_attribute_types()
            vcnt_attr = model_attributes
            for ma in model_attributes:
                ma_uri = ma.get_uri()
                if ma_uri.endswith('visit_count'):
                    vcnt_attr_uri = ma_uri
                    continue
                if ma_uri.endswith('title'):
                    title_attr_uri = ma_uri
                    continue
                if ma_uri.endswith('frequency'):
                    freq_attr_uri = ma_uri
                    continue

            nb_browser_items = 0 # to be replaced by select count(id) ...
            nb_obsels = 0
            for row in cursor:
                nb_browser_items = nb_browser_items + 1

                if nb_obsels > self._args.limit:
                    break

                last_visit = row['last_visit_date']
                if last_visit is not None:
                    last_visit = datetime.datetime.fromtimestamp(int( \
                                              math.floor(last_visit/1000000)))
                else:
                    # We do not create obsels with no date in kTBS
                    continue

                # Prepare obsel attributes
                attributes = {}
                attributes[vcnt_attr_uri] = row['visit_count']
                attributes[title_attr_uri] = row['title']
                attributes[freq_attr_uri] = row['frecency']
                
                # Insert history items  as obsels
                o = trace.create_obsel(type=bh_obsel_type.get_uri(),
                                       begin=last_visit,
                                       end=last_visit,
                                       attributes={}, #visit_count=row['visit_count'],
                                       subject=row['url'])

                obsels_list.append(o)

                self.display("id: %s, url: %s, visit_count: %s, frecency: %s, \
                              last_visit_date: %s" % (row['id'], row['url'],
                              row['visit_count'], row['frecency'], last_visit))

                nb_obsels = nb_obsels + 1

                # To display Process information
                if self._args.stats and nb_obsels % 100 == 0:
                    values = self.process_info.get_values()
                    print "=====> PROCESS INFO = %s" % str(values)

            cursor.close()

            if self._args.stats:
                end_cpu = time.clock()
                end_time = time.time()
                print "Program execution time %f seconds" % \
                                                (end_time - start_time)
                print "Program CPU execution time %f seconds" % \
                                                (end_cpu - start_cpu)
                print "Created %i obsels on %i items" % (nb_obsels, \
                                                         nb_browser_items)

        except sqlite3.Error, err:
            print "An error occurred:", err.args[0]

        return obsels_list

    def list_stored_obsels(self, trace=None):
        """
        Open the browser history database, extract history items and
        populates a kTBS stored trace with it.
        """
        if self._args.stats:
            start_time = time.time()
            start_cpu = time.clock()

        nb_obsels = 0
        for o in trace.list_obsels():
            self.display("Trace: %s, obsel: %s" % (trace.label, o.label))

            nb_obsels = nb_obsels + 1

            # To display Process information
            if self._args.stats and nb_obsels % 100 == 0:
                values = self.process_info.get_values()
                print "=====> PROCESS INFO = %s" % str(values)

        if self._args.stats:
            end_cpu = time.clock()
            end_time = time.time()
            print "Program execution time %f seconds" % \
                                            (end_time - start_time)
            print "Program CPU execution time %f seconds" % \
                                            (end_cpu - start_cpu)
            print "To display %i obsels." % nb_obsels

        return nb_obsels

    def display_obsel(self, trace=None, obsel_id=None):
        """
        """
        if self._args.stats:
            start_cpu = time.clock()
            start_time = time.time()

        trace.get_obsel(obsel_id)

        if self._args.stats:
            values = self.process_info.get_values()
            print "=====> PROCESS INFO = %s" % str(values)

            end_cpu = time.clock()
            end_time = time.time()
            print "Program execution time %f seconds" % \
                                            (end_time - start_time)
            print "Program CPU execution time %f seconds" % \
                                            (end_cpu - start_cpu)
            print "To display obsel %s." % obsel_id

def collect(collectBH):
    """
    """
    baseBH = collectBH.create_ktbs_base_for_history()
    modelBH = collectBH.create_ktbs_model_for_history(baseBH)
    traceBH = collectBH.create_ktbs_trace_for_history(baseBH, modelBH)
    obselsBH = collectBH.collect_history_items(traceBH)

    #collectBH.list_stored_obsels(traceBH)
    #if len(obselsBH) > 0:
    #    collectBH.display_obsel(traceBH, obselsBH[0].uri)

if __name__ == "__main__":
    collector = BrowserHistoryCollector()
    if collector.profiling_asked():
        profile_dt = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")
        profile_filename = "profile-ktbs-%s.prof" % profile_dt
        cProfile.runctx('collect(collectBH)', 
                        globals(), 
                        {"collectBH": collector},
                        profile_filename)
    else:
        collect(collector)
    sys.exit(0)
