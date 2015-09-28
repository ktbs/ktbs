#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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

"""I provide access to any kTBS (either local or remote).
"""

# import all mixin classes to ensure they are registered
import ktbs.api.base # unused import ktbs # pylint: disable=W0611
import ktbs.api.builtin_method # reimport ktbs #pylint: disable=W0404
import ktbs.api.ktbs_root # reimport ktbs #pylint: disable=W0404
import ktbs.api.method # reimport ktbs #pylint: disable=W0404
import ktbs.api.obsel # reimport ktbs #pylint: disable=W0404
import ktbs.api.trace # reimport ktbs #pylint: disable=W0404
import ktbs.api.trace_model # reimport ktbs #pylint: disable=W0404
import ktbs.api.trace_obsels # reimport ktbs #pylint: disable=W0404
# import serializers and parsers to ensure they are registered
import ktbs.serpar

from rdfrest.cores.factory import factory


def get_ktbs(uri):
    """I return the root of a kTBS.

    :param basestring uri: the URI of this kTBS
    :rtype: :class:`ktbs.api.ktbs_root.KtbsRoot`

    This assumes that the kTBS already exists, either as a remore server or as
    a local service. If your goal is to *create* a local kTBS service, you must
    use :func:`ktbs.engine.service.make_ktbs` instead.
    """
    ret = factory(uri)
    assert isinstance(ret, ktbs.api.ktbs_root.KtbsRootMixin)
    return ret
                     
