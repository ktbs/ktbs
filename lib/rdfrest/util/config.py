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
I provide configuration functions for the rdfrest Service.
"""

import sys
import logging
import logging.config
from ConfigParser import SafeConfigParser

from ..serializers import bind_prefix


def get_service_configuration(configfile_handler=None):
    """I set rdfrest Service default configuration options and possibly
    override them with the values extracted from a configuration file.

    :param configfile_handler: optional handler of a configuration file

    :return: Configuration object.
    """
    # When allow_no_value=True is passed, options without values return None
    # The value must be used as flags i.e
    # [rdf_database]
    # repository
    # and not :
    # repository =
    # which will return an empty string whatever 'allow_no_value' value is set
    config = SafeConfigParser(allow_no_value=True)

    # Setting default values
    config.add_section('server')
    config.set('server', 'host-name', 'localhost')
    config.set('server', 'port', '8001')
    config.set('server', 'base-path', '')
    config.set('server', 'force-ipv4', 'false')
    config.set('server', 'max-bytes', '-1')
    config.set('server', 'no-cache', 'false')
    config.set('server', 'flash-allow', 'false')
    config.set('server', 'max-triples', '-1')
    config.set('server', 'cors-allow-origin', '')
    config.set('server', 'resource-cache', 'false')

    config.add_section('ns_prefix')

    # A future specification section "httpd" or "wsgi"
    # may be needed for HttpFrontend
    #config.add_section('httpd')

    config.add_section('plugins')
    config.set('plugins', 'post_via_get', 'false')

    # TODO : optional plugin specific configuration
    #config.add_section('post_via_get')

    config.add_section('rdf_database')
    config.set('rdf_database', 'repository', '')
    config.set('rdf_database', 'force-init', 'false')

    config.add_section('logging')
    config.set('logging', 'loggers', '')
    config.set('logging', 'console-level', 'INFO')
    # No filename implies no logging to file
    config.set('logging', 'filename', '')
    config.set('logging', 'file-level', 'INFO')
    config.set('logging', 'json-configuration-filename', 'logging.json')

    # Loading from config file
    if configfile_handler is not None:
        config.readfp(configfile_handler)

    return config


def build_service_root_uri(service_config):
    """
    :param service_config: SafeConfigParser object containing URI scheme elements
    :return: Ktbs root URI
    """
    if service_config is None:
        return None

    if service_config.has_option('server', 'fixed-root-uri'):
        # In case a fixed URI is passed (unit tests, ...)
        return service_config.get('server', 'fixed-root-uri', 1)
    else:
        root_uri = "http://{hostname}:{port}{basepath}/".format(
            hostname = service_config.get('server', 'host-name', 1),
            port = service_config.getint('server', 'port'),
            basepath = service_config.get('server', 'base-path', 1))

    return root_uri


def apply_logging_config(service_config):
    """
    Configures the logging for rdfrest services.

    :param service_config: SafeConfigParser object containing a 'logging' section
    """
    # No filter configured
    loggingConfig =  {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'simple': {
                    'format': '%(levelname)s %(asctime)s %(name)s %(message)s',
                    'datefmt': '%d/%m/%Y %I:%M:%S %p'
                    },
                'withpid': {
                    'format': '%(levelname)s %(asctime)s %(process)d %(name)s %(message)s'
                    }
                },
            'handlers': {
                'console': {
                    'level': 'INFO',
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple'
                    }
                }
            }

    # Use the maximum handler loglevel for the loggers
    loglevels = []

    if service_config is not None:
        # TODO add controls on some values
        if service_config.has_option('logging', 'loggers'):
            loggers = service_config.get('logging', 'loggers', 1).split()
            if len(loggers) > 0:
                for logger in loggers:
                    if logger == 'root':
                        # Perhaps better to False when root is concerned
                        #loggingConfig['disable_existing_loggers'] = False

                        loggingConfig['root'] = {}
                        loggingConfig['root']['handlers'] = ['console',]
                    else:
                        if not loggingConfig.has_key('loggers'):
                            loggingConfig['loggers'] = {}

                        # default logging level should be warning if not specified
                        loggingConfig['loggers'][logger] = {}
                        loggingConfig['loggers'][logger]['handlers'] = ['console',]
            else:
                # If not logger is set, no logging configuration is done
                return

        if service_config.has_option('logging', 'console-level'):
            loggingConfig['handlers']['console']['level'] = service_config.get('logging', 'console-level', 1)
        loglevels.append(loggingConfig['handlers']['console']['level'])

        if service_config.has_option('logging', 'filename') and \
           len(service_config.get('logging', 'filename', 1)) > 0:
            # Add a 'filelog' handler
            loggingConfig['handlers']['filelog'] = {}
            loggingConfig['handlers']['filelog']['class'] = 'logging.FileHandler'
            loggingConfig['handlers']['filelog']['filename'] = service_config.get('logging', 'filename', 1)
            loggingConfig['handlers']['filelog']['mode'] = 'w'
            # Just to test
            loggingConfig['handlers']['filelog']['formatter'] = 'withpid'

            if service_config.has_option('logging', 'file-level'):
                loggingConfig['handlers']['filelog']['level'] = service_config.get('logging', 'file-level', 1)
                loglevels.append(loggingConfig['handlers']['filelog']['level'])

        if service_config.has_option('logging', 'ktbs-logurl') and \
           len(service_config.get('logging', 'ktbs-logurl', 1)) > 0:
            # Add a 'kTBS log handler'
            loggingConfig['handlers']['ktbslog'] = {}
            loggingConfig['handlers']['ktbslog']['class'] = 'rdfrest.util.ktbsloghandler.kTBSHandler'
            loggingConfig['handlers']['ktbslog']['url'] =  service_config.get('logging', 'ktbs-logurl', 1)
            if service_config.has_option('logging', 'ktbs-level'):
                loggingConfig['handlers']['ktbslog']['level'] = service_config.get('logging', 'ktbs-level', 1)
                loglevels.append(loggingConfig['handlers']['ktbslog']['level'])

    if loggingConfig.has_key('loggers'):
        for logger in loggingConfig['loggers'].keys():
            loggingConfig['loggers'][logger]['level'] = min(loglevels)

            if loggingConfig['handlers'].has_key('filelog'):
                loggingConfig['loggers'][logger]['handlers'].append('filelog')

            if loggingConfig['handlers'].has_key('ktbslog'):
                loggingConfig['loggers'][logger]['handlers'].append('ktbslog')

    if loggingConfig.has_key('root'):
        loggingConfig['root']['level'] = min(loglevels)

        if loggingConfig['handlers'].has_key('filelog'):
            loggingConfig['root']['handlers'].append('filelog')

        if loggingConfig['handlers'].has_key('ktbslog'):
            loggingConfig['root'][logger]['handlers'].append('ktbslog')
    try:
        # Load config
        logging.config.dictConfig(loggingConfig)
    except ValueError as e:
        print "Error in kTBS logging configuration, please read the following error message carefully.\n{0}".format(e.message)


def apply_ns_prefix_config(service_config):
    """
    Loads and applies the namespace configuration.

    :param service_config: SafeConfigParser object containing a 'ns_prefix' section
    """
    for prefix, uri in service_config.items('ns_prefix'):
        if prefix == "_":
            prefix = ""
        bind_prefix(prefix, uri)


def apply_plugins_config(service_config):
    """
    Loads and applies the plugin configuration.

    :param service_config: SafeConfigParser object containing a 'plugins' section
    """
    for plugin_name in service_config.options('plugins'):
        if service_config.getboolean('plugins', plugin_name):
            try:
                plugin = __import__(plugin_name, fromlist="start_plugin")
            except ImportError:
                plugin = __import__("ktbs.plugins." + plugin_name,
                                    fromlist="start_plugin")
            plugin.start_plugin(service_config)


def apply_global_config(service_config, **sections):
    """
    Loads and applies all global configuration settings
    (i.e. settings having an impact beyong the configured Service).

    Some sections can be individually disabled by using keyword.
    For example::

        apply_global_config(cfg, logging=False, plugins=do_plugins)

    will skip the 'logging' section, and conditionally apply the 'plugins'
    section (depending on the do_plugins variable).
    """
    if sections.get("logging", True):
        apply_logging_config(service_config)
    if sections.get("ns_prefix", True):
        apply_ns_prefix_config(service_config)
    if sections.get("plugins", True):
        apply_plugins_config(service_config)
