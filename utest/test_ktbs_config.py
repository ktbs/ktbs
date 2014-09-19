# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2014 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

"""
Nose unit-testing for the kTBS configuration part.

TODO : write failing test
"""

from unittest import TestCase
from unittest import skip

from nose.tools import assert_raises, eq_

from optparse import OptionParser, OptionGroup
from ktbs.standalone import parse_configuration_options

class TestkTBSConfig(TestCase):
    """
    Test that kTBS configuration parameters are correctly managed.
    """

    def setUp(self):
        self.opt = OptionParser()
        self.opt.add_option('--host-name')
        self.opt.add_option('--port', type=int)
        self.opt.add_option('--base-path')
        self.opt.add_option('--repository')
        self.opt.add_option('-c', '--configfile')
        self.opt.add_option('--ns-prefix', action='append')
        self.opt.add_option('--plugin', action='append')
        # OptionGroup is not needed, it's just for display ?
        self.opt.add_option('--force-ipv4', action='store_true')
        self.opt.add_option('--max-bytes')
        self.opt.add_option('--no-cache')
        self.opt.add_option('--flash-allow', action='store_true')
        self.opt.add_option('--max-triples')
        self.opt.add_option('--cors-allow-origin', action='store_true')
        self.opt.add_option('--force-init', action='store_true')
        self.opt.add_option('--resource-cache', action='store')
        self.opt.add_option('--loggers', action='append')
        self.opt.add_option('--console-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        self.opt.add_option('--file-level',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        self.opt.add_option('--logging-filename')
        self.opt.add_option('--once')
        self.opt.add_option('-2')

    def tearDown(self):
        pass

    def test_server_hostname(self):
        """
        Do we have to check lower/upper/mixed-case or make the test accept any
        of them ?
        """
        options, args = self.opt.parse_args(['ktbs', 
                                             '--host-name=toto'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.get('server', 'host-name', 1), 'toto')

    def test_server_hostport(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--port=4567'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.getint('server', 'port'), 4567)

    def test_server_basepath(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--base-path=myktbsroot/'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.get('server', 'base-path', 1), 'myktbsroot/')

    def test_server_ipv4(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--force-ipv4'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.getboolean('server', 'force-ipv4'), True)

    def test_server_maxbytes(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--max-bytes=1500'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.getint('server', 'max-bytes'), 1500)

    @skip("To write")
    def test_server_nocache(self):
        """Be careful in ConfigParser this parameter is treated as boolean.
           In standalone, it is defined as an integer !!!
        """
        pass

    def test_server_flashallow(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--flash-allow'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.getboolean('server', 'flash-allow'), True)

    def test_server_maxtriples(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--max-triples=1000'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.getint('server', 'max-triples'), 1000)

    @skip("To write")
    def test_server_corsalloworigin(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--cors-allow-origin'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.getboolean('server', 'cors-allow-origin'), True)
        pass

    @skip("To write")
    def test_server_resourcecache(self):
        """USAGE TO BE DISCUSSED !!!!"""
        pass

    @skip("To write")
    def test_ns_prefix_one_item(self):
        """SYNTAX TO BE SPECIFIED"""
        options, args = self.opt.parse_args(['ktbs', 
                                             '--ns-prefix=foaf'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.get('ns_prefix', 'loggers', 1), 'foaf')

    def test_plugins_one_item(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--plugin=test_preproc'])

        ktbs_config = parse_configuration_options(options)
        # There's a default plugin in the config post_via_get
        eq_(ktbs_config.options('plugins'), ['post_via_get', 'test_preproc'])

    def test_rdf_database_repository(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--repository=/var/myktbs/'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.get('rdf_database', 'repository', 1), '/var/myktbs/')

    def test_rdf_database_forceinit(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--force-init'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.getboolean('rdf_database', 'force-init'), True)
        pass

    def test_logging_one_logger(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--loggers=ktbs'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.get('logging', 'loggers', 1), 'ktbs')

    def test_logging_multiple_loggers(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--loggers=ktbs',
                                             '--loggers=rdfrest'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.get('logging', 'loggers', 1), 'ktbs rdfrest')

    def test_logging_consolelevel(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--console-level=DEBUG'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.get('logging', 'console-level', 1), 'DEBUG')

    def test_logging_filename(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--logging-filename=/var/log/myktbslogs.log'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.get('logging', 'filename', 1), '/var/log/myktbslogs.log')

    def test_logging_filelevel(self):
        options, args = self.opt.parse_args(['ktbs', 
                                             '--file-level=WARNING'])

        ktbs_config = parse_configuration_options(options)
        eq_(ktbs_config.get('logging', 'file-level', 1), 'WARNING')
