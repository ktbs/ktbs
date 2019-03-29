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

from rdfrest.util.config import get_service_configuration

from .namespace import KTBS
from .utils import SKOS

def get_ktbs_configuration(configfile_handler=None):
    """I set kTBS default configuration options and possibly override them
    with the values extracted from a configuration file.

    :param configfile_handler: optional file handler of a configuration file

    :return: Configuration object.
    """
    ktbs_config = get_service_configuration(configfile_handler)

    _set_default(ktbs_config, 'ns_prefix', '_', str(KTBS)),
    _set_default(ktbs_config, 'ns_prefix', 'skos', str(SKOS))

    # plugins enabled by default for backward compatibility
    _set_default(ktbs_config, 'plugins', 'stats_per_type', 'true')


    return ktbs_config

def _set_default(config, section, option, value):
    if not config.has_section(section):
        config.add_section(section)
    if not config.has_option(section, option):
        config.set(section, option, value)
