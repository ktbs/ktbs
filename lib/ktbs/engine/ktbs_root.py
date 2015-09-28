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

"""
I provide the implementation of ktbs:KtbsRoot .
"""

from rdfrest.exceptions import MethodNotAllowedError

from .resource import KtbsPostableMixin, KtbsResource
from .lock import WithLockMixin
from ..api.ktbs_root import KtbsRootMixin
from ..namespace import KTBS


class KtbsRoot(WithLockMixin, KtbsRootMixin, KtbsPostableMixin, KtbsResource):
    """I provide the implementation of ktbs:KtbsRoot .
    """
    ######## ILocalCore (and mixins) implementation  ########

    RDF_MAIN_TYPE = KTBS.KtbsRoot

    def delete(self, parameters=None, _trust=True):
        """I override :meth:`rdfrest.util.EditableCore.delete`.

        A kTBS root can never be deleted.
        """
        # We do not use check_deletable, because that would raise a
        # CanNotProceedError, which is semantically less correct.
        raise MethodNotAllowedError("Can not delete KtbsRoot")

    def ack_post(self, parameters, created, new_graph):
        """I override :meth:`rdfrest.util.GraphPostableMixin.ack_post`.
        """
        super(KtbsRoot, self).ack_post(parameters, created, new_graph)
        with self.edit(_trust=True) as editable:
            editable.add((self.uri, KTBS.hasBase, created))

    def find_created(self, new_graph):
        """I override :meth:`rdfrest.util.GraphPostableMixin.find_created`.

        I look for the ktbs:hasBase property, pointing to a ktbs:Base.
        """
        query = """PREFIX ktbs: <%s>
                   SELECT DISTINCT ?c
                   WHERE { <%s> ktbs:hasBase ?c . ?c a ktbs:Base . }
        """ % (KTBS, self.uri)
        return self._find_created_default(new_graph, query)
