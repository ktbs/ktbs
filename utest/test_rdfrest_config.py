# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2014 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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

"""
Nose unit-testing for the RDF-REST configuration part.
"""
import logging

from rdfrest.util.config import get_service_configuration, make_log_config_dict


class TestServiceConfigDefaults(object):
    """
    Test RDF-REST Service creation with default values.
    """

    def setup(self):
        self.service_config = get_service_configuration()

    def teardown(self):
        del self.service_config

    def test_server_section(self):
        assert self.service_config.has_section('server') == True

    def test_server_hostname(self):
        """
        Do we have to check lower/upper/mixed-case or make the test accept any
        of them ?
        """
        assert self.service_config.get('server', 'host-name', 1) == 'localhost'

    def test_server_hostport(self):
        assert self.service_config.getint('server', 'port') == 8001

    def test_server_basepath(self):
        assert self.service_config.get('server', 'base-path', 1) == ''

    def test_server_ipv4(self):
        assert self.service_config.getboolean('server', 'force-ipv4') == False

    def test_server_maxbytes(self):
        assert self.service_config.getint('server', 'max-bytes') == -1

    def test_server_flashallow(self):
        assert self.service_config.getboolean('server', 'flash-allow') == False

    def test_server_maxtriples(self):
        assert self.service_config.getint('server', 'max-triples') == -1

    def test_server_corsalloworigin(self):
        assert self.service_config.get('server', 'cors-allow-origin', 1) == ''

    def test_server_resetconnection(self):
        assert self.service_config.getboolean('server', 'reset-connection') == False

    def test_server_sendtraceback(self):
        assert self.service_config.getboolean('server', 'send-traceback') == False

    def test_ns_prefix_section(self):
        assert self.service_config.has_section('ns_prefix') == True

    def test_plugins_section(self):
        """
        TODO This section should be empty
        """
        assert self.service_config.has_section('plugins') == True

    def test_rdf_database_section(self):
        assert self.service_config.has_section('rdf_database') == True

    def test_rdf_database_repository(self):
        assert self.service_config.get('rdf_database', 'repository', 1) == ''

    def test_rdf_database_forceinit(self):
        assert self.service_config.getboolean('rdf_database', 'force-init') == False

    def test_logging_section(self):
        assert self.service_config.has_section('logging')
        log_cfg = make_log_config_dict(self.service_config)
        assert log_cfg.get('version', 1)
        assert 'loggers' in log_cfg
        assert 'handlers' in log_cfg
        assert 'console' in log_cfg['handlers']
        assert 'filelog' not in log_cfg['handlers']
        assert 'ktbslog' not in log_cfg['handlers']
        assert 'formatters' in log_cfg
        assert 'simple' in log_cfg['formatters']

    def test_logging_loggers(self):
        cfg = get_service_configuration()
        cfg.set('logging', 'loggers', 'root ktbs rdfrest')
        log_cfg = make_log_config_dict(cfg)
        assert 'root' in log_cfg
        assert 'ktbs' in log_cfg['loggers']
        assert 'rdfrest' in log_cfg['loggers']

    def test_logging_console_level(self):
        cfg = get_service_configuration()
        cfg.set('logging', 'loggers', 'root ktbs rdfrest')
        cfg.set('logging', 'console-level', 'DEBUG')
        log_cfg = make_log_config_dict(cfg)
        assert log_cfg['handlers']['console']['level'] == logging.DEBUG
        # also check that the added loggers "inherit" that level
        assert log_cfg['root']['level'] == logging.DEBUG
        assert log_cfg['loggers']['ktbs']['level'] == logging.DEBUG
        assert log_cfg['loggers']['rdfrest']['level'] == logging.DEBUG

    def test_logging_console_format(self):
        cfg = get_service_configuration()
        cfg.set('logging', 'console-format', 'foo')
        log_cfg = make_log_config_dict(cfg)
        assert 'console' in log_cfg['formatters']
        assert log_cfg['formatters']['console']['format'] == 'foo'
        assert log_cfg['handlers']['console']['formatter'] == 'console'

    def test_logging_file(self):
        cfg = get_service_configuration()
        cfg.set('logging', 'loggers', 'root ktbs rdfrest')
        cfg.set('logging', 'filename', '/tmp/test.log')
        log_cfg = make_log_config_dict(cfg)
        assert 'filelog' in log_cfg['handlers']
        assert log_cfg['handlers']['filelog']['class'] == 'logging.FileHandler'
        assert log_cfg['handlers']['filelog']['filename'] == '/tmp/test.log'

    def test_logging_file_level(self):
        cfg = get_service_configuration()
        cfg.set('logging', 'loggers', 'root ktbs rdfrest')
        cfg.set('logging', 'console-level', 'WARNING')
        cfg.set('logging', 'filename', '/tmp/test.log')
        cfg.set('logging', 'file-level', 'DEBUG')
        log_cfg = make_log_config_dict(cfg)
        assert log_cfg['handlers']['filelog']['level'] == logging.DEBUG
        # also check that the added loggers "inherit" that level
        assert log_cfg['root']['level'] == logging.DEBUG
        assert log_cfg['loggers']['ktbs']['level'] == logging.DEBUG
        assert log_cfg['loggers']['rdfrest']['level'] == logging.DEBUG

    def test_logging_ktbs(self):
        cfg = get_service_configuration()
        cfg.set('logging', 'loggers', 'root ktbs rdfrest')
        cfg.set('logging', 'ktbs-logurl', 'http://localhost:8001/logs/log/')
        log_cfg = make_log_config_dict(cfg)
        assert 'ktbslog' in log_cfg['handlers']
        assert log_cfg['handlers']['ktbslog']['class'] == 'rdfrest.util.ktbsloghandler.kTBSHandler'
        assert log_cfg['handlers']['ktbslog']['url'] == 'http://localhost:8001/logs/log/'

    def test_logging_ktbs_level(self):
        cfg = get_service_configuration()
        cfg.set('logging', 'loggers', 'root ktbs rdfrest')
        cfg.set('logging', 'console-level', 'WARNING')
        cfg.set('logging', 'ktbs-logurl', 'http://localhost:8001/logs/log/')
        cfg.set('logging', 'ktbs-level', 'DEBUG')
        log_cfg = make_log_config_dict(cfg)
        assert log_cfg['handlers']['ktbslog']['level'] == logging.DEBUG
        # also check that the added loggers "inherit" that level
        assert log_cfg['root']['level'] == logging.DEBUG
        assert log_cfg['loggers']['ktbs']['level'] == logging.DEBUG
        assert log_cfg['loggers']['rdfrest']['level'] == logging.DEBUG
