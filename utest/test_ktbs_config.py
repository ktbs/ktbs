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

from unittest import skip
from pytest import raises as assert_raises

from ktbs.standalone import build_cmdline_options, parse_configuration_options
from ktbs.config import get_ktbs_configuration

try:
    from io import StringIO
except:
    from io import StringIO

class TestkTBSCmdlineConfig(object):
    """
    Test that kTBS command line configuration parameters are correctly
    managed.
    """

    def setup_method(self):
        self.opt = build_cmdline_options()

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
        assert ktbs_config.get('server', 'host-name', raw=1) == 'toto'

    def test_server_hostport(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--port=4567'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.getint('server', 'port') == 4567

    def test_server_basepath(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--base-path=myktbsroot/'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.get('server', 'base-path', raw=1) == 'myktbsroot/'

    def test_server_ipv4(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--force-ipv4'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.getboolean('server', 'force-ipv4') == True

    def test_server_maxbytes(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--max-bytes=1500'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.getint('server', 'max-bytes') == 1500

    def test_server_cachecontrol(self):
        """Be careful in ConfigParser this parameter is treated as boolean.
           In standalone, it is defined as an integer !!!
        """
        options, args = self.opt.parse_args(['ktbs',
                                             '--cache-control=max-age=2'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.get('server', 'cache-control') == "max-age=2"

    def test_server_nocache(self):
        """Be careful in ConfigParser this parameter is treated as boolean.
           In standalone, it is defined as an integer !!!
        """
        options, args = self.opt.parse_args(['ktbs',
                                             '--no-cache'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.get('server', 'cache-control') == ""

    def test_server_maxtriples(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--max-triples=1000'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.getint('server', 'max-triples') == 1000

    @skip("To write")
    def test_server_corsalloworigin(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--cors-allow-origin'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.getboolean('server', 'cors-allow-origin') == True
        pass

    @skip("To write")
    def test_server_resourcecache(self):
        """USAGE TO BE DISCUSSED !!!!"""
        pass

    def test_ns_prefix_one_item(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--ns-prefix=foaf:http://xmlns.com/foaf/0.1/'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.options('ns_prefix'), ['_', 'skos' == 'foaf']
        assert ktbs_config.get('ns_prefix', 'foaf', raw=1) == 'http://xmlns.com/foaf/0.1/'

    def test_plugins_one_item(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--plugin=test_preproc'])

        ktbs_config = parse_configuration_options(options)
        # There's a default plugin in the config post_via_get
        assert ktbs_config.options('plugins'), ['post_via_get' == 'test_preproc']

    def test_rdf_database_repository(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--repository=/var/myktbs/'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.get('rdf_database', 'repository', raw=1) == '/var/myktbs/'

    def test_rdf_database_forceinit(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--force-init'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.getboolean('rdf_database', 'force-init') == True
        pass

    def test_logging_one_logger(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--loggers=rdfrest'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.get('logging', 'loggers', raw=1) == 'ktbs rdfrest'

    def test_logging_multiple_loggers(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--loggers=ktbs',
                                             '--loggers=rdfrest'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.get('logging', 'loggers', raw=1) == 'ktbs ktbs rdfrest'

    def test_logging_consolelevel(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--console-level=DEBUG'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.get('logging', 'console-level', raw=1) == 'DEBUG'

    def test_logging_filename(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--logging-filename=/var/log/myktbslogs.log'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.get('logging', 'filename', raw=1) == '/var/log/myktbslogs.log'

    def test_logging_filelevel(self):
        options, args = self.opt.parse_args(['ktbs',
                                             '--file-level=WARNING'])

        ktbs_config = parse_configuration_options(options)
        assert ktbs_config.get('logging', 'file-level', raw=1) == 'WARNING'

class TestkTBSFileConfig(object):
    """
    Test that kTBS configuration configuration file parameters are correctly
    managed.

    If you want to use StringIO more dynamically with writelines(), you must
    insert seek(0) before passing the object to ConfigParser code.

        fhandler.writelines(["[server]\n",
                             "host-name = testhost\n"])
        fhandler.seek(0)
    otherwise no line are recored by ConfigParser readline() calls.

    Giving a string to the cStringIO.StringIO() constructor returns an object
    with fewer methods (no write method for instance).

        configstring = '''
        [server]
        host-name = testhost
        '''
        fhandler = StringIO(configstring)

    But this failed to be user by ConfigParser readfp() method.
    """

    #def setUp(self):
    #    self.opt = build_cmdline_options()

    #def tearDown(self):
    #    pass

    def test_server_hostname(self):
        fhandler = StringIO()
        fhandler.writelines(["[server]\n",
                             "host-name = testhost\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.get('server', 'host-name', raw=1) == 'testhost'

    def test_server_hostport(self):
        fhandler = StringIO()
        fhandler.writelines(["[server]\n",
                             "port = 4444\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.getint('server', 'port') == 4444

    def test_server_basepath(self):
        fhandler = StringIO()
        fhandler.writelines(["[server]\n",
                             "base-path = myktbsroot/\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.get('server', 'base-path', raw=1) == 'myktbsroot/'

    def test_server_ipv4(self):
        fhandler = StringIO()
        fhandler.writelines(["[server]\n",
                             "force-ipv4 = true\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.getboolean('server', 'force-ipv4') == True

    def test_server_maxbytes(self):
        fhandler = StringIO()
        fhandler.writelines(["[server]\n",
                             "max-bytes = 1234\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.getint('server', 'max-bytes') == 1234

    def test_server_nocache(self):
        """Be careful in ConfigParser this parameter is treated as boolean.
           In standalone, it is defined as an integer !!!
        """
        fhandler = StringIO()
        fhandler.writelines(["[server]\n",
                             "no-cache = true\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.getboolean('server', 'no-cache') == True

    def test_server_maxtriples(self):
        fhandler = StringIO()
        fhandler.writelines(["[server]\n",
                             "max-triples = 1200\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.getint('server', 'max-triples') == 1200

    @skip("To write")
    def test_server_corsalloworigin(self):
        fhandler = StringIO()
        fhandler.writelines(["[server]\n",
                             "cors-allow-origin = xxx\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.getboolean('server', 'cors-allow-origin') == True
        pass

    @skip("To write")
    def test_server_resourcecache(self):
        """USAGE TO BE DISCUSSED !!!!"""
        pass

    def test_ns_prefix_one_item(self):
        fhandler = StringIO()
        fhandler.writelines(["[ns_prefix]\n",
                             "foaf = http://xmlns.com/foaf/0.1/\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        # In this case, foaf is the first prefix added before the 2
        # default ones added by get_ktbs_configuration()
        assert ktbs_config.options('ns_prefix'), ['foaf', '_' == 'skos']
        assert ktbs_config.get('ns_prefix', 'foaf', raw=1) == 'http://xmlns.com/foaf/0.1/'

    def test_plugins_one_item(self):
        fhandler = StringIO()
        fhandler.writelines(["[plugins]\n",
                             "test_preproc = true\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        # There's a default plugin in the config post_via_get
        assert ktbs_config.options('plugins'), ['post_via_get' == 'test_preproc']

    def test_rdf_database_repository(self):
        fhandler = StringIO()
        fhandler.writelines(["[rdf_database]\n",
                             "repository = /var/myktbs/\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.get('rdf_database', 'repository', raw=1) == '/var/myktbs/'

    def test_rdf_database_forceinit(self):
        fhandler = StringIO()
        fhandler.writelines(["[rdf_database]\n",
                             "force-init = true\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.getboolean('rdf_database', 'force-init') == True

    def test_logging_one_logger(self):
        fhandler = StringIO()
        fhandler.writelines(["[logging]\n",
                             "loggers = ktbs\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.get('logging', 'loggers', raw=1) == 'ktbs'

    def test_logging_multiple_loggers(self):
        fhandler = StringIO()
        fhandler.writelines(["[logging]\n",
                             "loggers = ktbs rdfrest\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.get('logging', 'loggers', raw=1) == 'ktbs rdfrest'

    def test_logging_consolelevel(self):
        fhandler = StringIO()
        fhandler.writelines(["[logging]\n",
                             "console-level = DEBUG\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.get('logging', 'console-level', raw=1) == 'DEBUG'

    def test_logging_filename(self):
        fhandler = StringIO()
        fhandler.writelines(["[logging]\n",
                             "filename = /var/log/myktbslogs.log\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.get('logging', 'filename', raw=1) == '/var/log/myktbslogs.log'

    def test_logging_filelevel(self):
        fhandler = StringIO()
        fhandler.writelines(["[logging]\n",
                             "file-level = WARNING\n"])
        fhandler.seek(0)

        ktbs_config = get_ktbs_configuration(fhandler)
        assert ktbs_config.get('logging', 'file-level', raw=1) == 'WARNING'
