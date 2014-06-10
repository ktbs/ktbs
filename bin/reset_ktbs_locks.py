import argparse
import posix_ipc
import logging
from rdflib import ConjunctiveGraph, RDF
from ktbs.namespace import KTBS


def get_args():
    """Get arguments from the command line."""
    parser = argparse.ArgumentParser(description="""Reset all the locks of a kTBS.
    This could be useful after a kTBS crash. This shouldn't be used on a running kTBS.""")

    parser.add_argument('repository', nargs=1, type=str,
                        help='the filename/identifier of the RDF database. '
                             'Must be of the form :store_type:configuration_string. '
                             'e.g. :Sleepycat:/path/to/sleepycat.db . '
                             'If :story_type: is missing, then we assume it is :Sleepycat:.'
    )

    return parser.parse_args()


def get_store_info(repository):
    """Get the store type and configuration from the repository argument."""
    if repository[0] != ':':
        repository = ':Sleepycat:' + repository
    _, store_type, store_config = repository.split(':', 2)

    return store_type, store_config


def get_locked_resources(graph):
    """Get all possibly locked resources of a graph.

    That is: all KtbsRoot and all kTBS Bases."""
    resources = []

    # Add KtbsRoot
    for root in graph.subjects(predicate=RDF.type, object=KTBS.KtbsRoot):
        resources.append(root)

    # Add bases
    for _, _, base in graph.triples((None, KTBS.hasBase, None)):
        resources.append(base)

    return resources


def unlock(resource_uri):
    """Unlock a resource at the semaphore level."""
    semaphore_name = str(
        '/' + resource_uri.replace('/', '-'))  # TODO put this transformation into a function and use it

    try:
        semaphore = posix_ipc.Semaphore(semaphore_name)
        if semaphore.value == 0:
            semaphore.release()
            semaphore.close()
            logging.info("The resource <{res}> has been unlocked.".format(res=resource_uri))

    except posix_ipc.ExistentialError:
        message = "The resource <{res}> doesn't appear to be locked (no semaphore found).".format(res=resource_uri)
        logging.warning(message)


if __name__ == '__main__':
    args = get_args()
    store_type, store_config = get_store_info(args.repository[0])

    # Make a graph of everything that is in the RDF store
    big_graph = ConjunctiveGraph(store_type)
    big_graph.open(store_config, create=False)

    locked_resources = get_locked_resources(big_graph)

    for resource in locked_resources:
        unlock(resource)
