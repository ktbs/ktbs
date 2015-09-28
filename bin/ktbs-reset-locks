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
    This could be useful after a kTBS crash. This MUST NOT be used on a running kTBS.""")

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
    """Get the store type and configuration from the repository argument.

    :param str repository: repository type and configuration in the form `:type:configuration`.
    """
    if repository[0] != ':':
        repository = ':Sleepycat:' + repository
    _, store_type, store_config = repository.split(':', 2)

    return store_type, store_config


def get_locked_resources(graph):
    """Generator of all the possibly locked resources of a store.
    Possible locked resources are KtbsRoot and kTBS bases.

    :param ConjunctiveGraph graph: graph that stores the kTBS resources.
    """
    # Add KtbsRoot
    for root in graph.subjects(predicate=RDF.type, object=KTBS.KtbsRoot):
        yield root

    # Add bases
    for base in graph.objects(predicate=KTBS.hasBase):
        yield base


def reset(resource_uri):
    """Reset a resource at the semaphore level, i.e. set its value to 1.

    :param resource_uri: URI of the resource to reset.
    :return: True if the resource has been reset, False otherwise.
    """
    semaphore_name = get_semaphore_name(resource_uri)
    reset_resource = False

    try:
        semaphore = posix_ipc.Semaphore(semaphore_name)

        if semaphore.value == 0:
            semaphore.release()
            logging.info("The resource <{res}> has been unlocked.".format(res=resource_uri))
            reset_resource = True

        elif semaphore.value > 1:
            old_semaphore_value = semaphore.value
            while semaphore.value > 1:
                semaphore.acquire()
            reset_resource = True
            logging.info("The lock for <{res}> has been reset to 1 (was {old_value})."
                         .format(res=resource_uri, old_value=old_semaphore_value))

        elif semaphore.value == 1:
            logging.info("The resource <{res}> doesn't appear to be locked (semaphore found).".format(res=resource_uri))

        semaphore.close()

    except posix_ipc.ExistentialError:
        message = "The resource <{res}> doesn't appear to be locked (semaphore not found).".format(res=resource_uri)
        logging.info(message)

    return reset_resource


def main(repository, log_level):
    """Entry point for the script."""
    store_type, store_config = get_store_info(repository)
    if store_type == 'IOMemory':
        raise ValueError('Cannot use IOMemory as repository. Try rebooting to get rid of the locks.')

    # Set logging level
    logging.basicConfig(level=log_level.upper())

    # Make a graph of everything that is in the RDF store
    graph = ConjunctiveGraph(store_type)
    graph.open(store_config, create=False)

    # Do the reset of the resources
    did_reset = False  # tell if we already did a successful reset or not
    for resource in get_locked_resources(graph):
        if reset(resource) and not did_reset:
            did_reset = True

    if not did_reset:
        logging.warning('No lock to reset, did not do anything.')


if __name__ == '__main__':
    args = get_args()
    main(args.repository[0], args.log_level[0])
