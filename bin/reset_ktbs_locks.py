#!/usr/bin/env python
# -*- coding=utf-8 -*-

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

from os.path import abspath, dirname, join
from sys import path

try:
    SOURCE_DIR = dirname(dirname(abspath(__file__)))
    LIB_DIR = join(SOURCE_DIR, "lib")
    path.append(LIB_DIR)
except NameError:
    # __file__ is not define in py2exe
    pass

import argparse
import posix_ipc
import logging

from rdflib import ConjunctiveGraph, RDF

from ktbs.namespace import KTBS
from ktbs.engine.lock import get_semaphore_name


def get_args():
    """Get arguments from the command line."""
    parser = argparse.ArgumentParser(description="""Reset all the locks of a kTBS.
    This could be useful after a kTBS crash. This shouldn't be used on a running kTBS.""")

    parser.add_argument('repository', nargs=1, type=str,
                        help='the filename/identifier of the RDF database. '
                             'Must be of the form :store_type:configuration_string. '
                             'e.g. :Sleepycat:/path/to/sleepycat.db . '
                             'If :store_type: is missing, then we assume it is :Sleepycat:.')

    parser.add_argument('-l', '--log-level', nargs=1, type=str, default=['info'],
                        choices=('debug', 'info', 'warning', 'error', 'critical'),
                        help='set the log level.')

    return parser.parse_args()


def get_store_info(repository):
    """Get the store type and configuration from the repository argument."""
    if repository[0] != ':':
        repository = ':Sleepycat:' + repository
    _, store_type, store_config = repository.split(':', 2)

    return store_type, store_config


def get_locked_resources(graph):
    """Generator of all the possibly locked resources of a store.

    Possible locked resoruces are KtbsRoot and kTBS bases."""
    # Add KtbsRoot
    for root in graph.subjects(predicate=RDF.type, object=KTBS.KtbsRoot):
        yield root

    # Add bases
    for base in graph.objects(predicate=KTBS.hasBase):
        yield base


def unlock(resource_uri):
    """Unlock a resource at the semaphore level."""
    semaphore_name = get_semaphore_name(resource_uri)

    try:
        semaphore = posix_ipc.Semaphore(semaphore_name)

        if semaphore.value == 0:
            semaphore.release()
            semaphore.close()
            logging.info("The resource <{res}> has been unlocked.".format(res=resource_uri))

        elif semaphore.value == 1:
            logging.info("The resource <{res}> doesn't appear to be locked (semaphore found).".format(res=resource_uri))

    except posix_ipc.ExistentialError:
        message = "The resource <{res}> doesn't appear to be locked (no semaphore found).".format(res=resource_uri)
        logging.info(message)


def main():
    """Entry point for the script."""
    args = get_args()
    store_type, store_config = get_store_info(args.repository[0])

    # Set logging level
    logging.basicConfig(level=args.log_level[0].upper())

    # Make a graph of everything that is in the RDF store
    big_graph = ConjunctiveGraph(store_type)
    big_graph.open(store_config, create=False)

    for resource in get_locked_resources(big_graph):
        unlock(resource)


if __name__ == '__main__':
    main()
