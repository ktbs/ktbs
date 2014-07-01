# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2014 Françoise Conil <francoise.conil@liris.cnrs.fr> /
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
I provide configuration functions for the kTBS.
"""

from ConfigParser import SafeConfigParser

def get_ktbs_configuration(configfile_path=None):
    """I set kTBS default configuration options and possibly override them
    with the values extracted from a configuration file.

    :param configfile_path: optional path of a configuration file

    :return: Configuration object.
    """
    # When allow_no_value=True is passed, options without values return None
    # The value must be used as flags i.e
    # [rdf_database]
    # repository
    # and not :
    # repository =
    # which will return an empty string whatever 'allow_no_value' value is set
    config = SafeConfigParser()

    # Setting default values
    config.add_section('server')
    config.set('server', 'host-name', 'localhost')
    config.set('server', 'port', '8001')
    config.set('server', 'base-path', '')
    config.set('server', 'ipv4', 'false')
    config.set('server', 'max-bytes', '0')
    config.set('server', 'no-cache', 'false')
    config.set('server', 'flash-allow', 'false')
    config.set('server', 'max-triples', '0')
    config.set('server', 'cors-allow-origin', '')
    config.set('server', 'max-age', '0')
    config.set('server', 'resource-cache', 'false')

    config.add_section('ns_prefix')

    config.add_section('plugins')
    config.set('plugins', 'post_via_get', 'false')

    # TODO : optional plugin specific configuration
    #config.add_section('post_via_get')

    config.add_section('rdf_database')
    config.set('rdf_database', 'repository', '')
    config.set('rdf_database', 'init-repo', 'auto')

    config.add_section('debug')
    config.set('debug', 'log-level', 'info')
    config.set('debug', 'requests', '-1')

    # Loading from config file
    if configfile_path is not None:
        with open(configfile_path) as f:
            config.readfp(f)

    return config
