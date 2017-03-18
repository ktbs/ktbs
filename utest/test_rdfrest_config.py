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

from rdfrest.util.config import get_service_configuration


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
        assert self.service_config.has_section('logging') == True

    def test_logging_loggers(self):
        assert self.service_config.get('logging', 'loggers', 1) == ''

    def test_logging_consolelevel(self):
        assert self.service_config.get('logging', 'console-level', 1) == 'INFO'

    def test_logging_filename(self):
        assert self.service_config.get('logging', 'filename', 1) == ''

    def test_logging_filelevel(self):
        assert self.service_config.get('logging', 'file-level', 1) == 'INFO'

    def test_logging_jsonconfigurationfilename(self):
        """
        Future implementation.
        """
        assert self.service_config.get('logging', 'json-configuration-filename', 1) == 'logging.json'
