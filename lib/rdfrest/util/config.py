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

import json
import logging
import logging.config
from ConfigParser import NoOptionError, SafeConfigParser

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
    config.set('server', 'threads', '2')
    config.set('server', 'base-path', '')
    config.set('server', 'force-ipv4', 'false')
    config.set('server', 'max-bytes', '-1')
    config.set('server', 'flash-allow', 'false')
    config.set('server', 'max-triples', '-1')
    config.set('server', 'cors-allow-origin', '')
    config.set('server', 'reset-connection', 'false')
    config.set('server', 'send-traceback', 'false')

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
        root_uri = service_config.get('server', 'fixed-root-uri', 1)
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
    if service_config is None:
        return

    loggingConfig = make_log_config_dict(service_config)
    if 'root' not in loggingConfig and not loggingConfig.get('loggers'):
        # no logger configured, so nothing to do
        return

    try:
        # Load config
        logging.config.dictConfig(loggingConfig)
    except ValueError as e:
        print "Error in kTBS logging configuration, please read the following error message carefully.\n{0}".format(e.message)


def make_log_config_dict(service_config, date_fmt='%Y-%m-%d %H:%M:%S %Z'):
    if service_config.has_option('logging', 'json-configuration-filename'):
        filename = service_config.get('logging', 'json-configuration-filename', 1)
        with open(filename) as f:
            loggingConfig = json.load(f)
    else:
        loggingConfig =  {
                'version': 1,
                'disable_existing_loggers': False,
                }
    if 'formatters' not in loggingConfig:
        loggingConfig['formatters'] = {}
    if 'simple' not in loggingConfig['formatters']:
        loggingConfig['formatters']['simple'] = {
            'format': '%(levelname)s\t%(asctime)s\t%(name)s\t%(message)s',
            'datefmt': date_fmt,
        }
    if 'handlers' not in loggingConfig:
        loggingConfig['handlers'] = {}
    if 'console' not in loggingConfig['handlers']:
        loggingConfig['handlers']['console'] = {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    if 'loggers' not in loggingConfig:
        loggingConfig['loggers'] = {}

    # Use the minimum handler loglevel for the loggers
    logger_level = min([
        get_log_level(service_config, 'console-level', logging.INFO),
        get_log_level(service_config, 'file-level'),
        get_log_level(service_config, 'ktbs-level'),
    ])
    logger_handlers = ['console',]

    if service_config.has_option('logging', 'loggers'):
        loggers = service_config.get('logging', 'loggers', 1).split()
        if len(loggers) > 0:
            for logger in loggers:
                logger_dict = {
                    'level': logger_level,
                    'handlers': logger_handlers,
                }
                if logger == 'root' and 'root' not in loggingConfig:
                    loggingConfig['root'] = logger_dict
                elif logger not in loggingConfig['loggers']:
                    loggingConfig['loggers'][logger] = logger_dict

    if service_config.has_option('logging', 'console-level'):
        loggingConfig['handlers']['console']['level'] = get_log_level(service_config, 'console-level')

    if service_config.has_option('logging', 'console-format'):
        loggingConfig['handlers']['console']['formatter'] = 'console'
        loggingConfig['formatters']['console'] = {
            'format': service_config.get('logging', 'console-format', 1),
            'datefmt': date_fmt,
        }


    if service_config.has_option('logging', 'filename') and \
       len(service_config.get('logging', 'filename', 1)) > 0:
        # Add a 'filelog' handler
        logger_handlers.append('filelog')
        loggingConfig['handlers']['filelog'] = {
            'class': 'logging.FileHandler',
            'filename': service_config.get('logging', 'filename', 1),
            'mode': 'w',
            'formatter': 'simple',
        }
        if service_config.has_option('logging', 'file-level'):
            loggingConfig['handlers']['filelog']['level'] = get_log_level(service_config, 'file-level')

    if service_config.has_option('logging', 'ktbs-logurl') and \
       len(service_config.get('logging', 'ktbs-logurl', 1)) > 0:
        # Add a 'kTBS log handler'
        logger_handlers.append('ktbslog')
        loggingConfig['handlers']['ktbslog'] = {
            'class': 'rdfrest.util.ktbsloghandler.kTBSHandler',
            'url': service_config.get('logging', 'ktbs-logurl', 1),
        }
        if service_config.has_option('logging', 'ktbs-level'):
            loggingConfig['handlers']['ktbslog']['level'] = get_log_level(service_config, 'ktbs-level')

    return loggingConfig


def get_log_level(service_config, option, default=logging.WARNING):
    try:
        label = service_config.get('logging', option, 1)
        try:
            value = int(label)
        except ValueError:
            try:
                value = getattr(logging, label.upper())
            except AttributeError:
                raise ValueError("Unknwon log level %s" % label)
        return value
    except NoOptionError:
        return default


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
