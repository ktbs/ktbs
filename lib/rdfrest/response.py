#    This file is part of RDF-REST <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
I provide a subclass of :class:`webob.Response` more adapted to RDF-REST.

First, :class:`MyResponse` has different default values than
:class:`webob.Response`.

Second, webob is broken regarding etags:

* :func:`webob.descriptors.parse_etag_response` and
  :func:`webob.descripyors.serialize_etag_response` do not support
  weak etags at all (this is acknowledged as a comment).

* :meth:`webob.ETagMatcher.weak_match` naively assumes that any string
  that starts with 'w/' is a weak etag, which seems to be wrong: can't
  a strong etag start with 'w/', e.g. in::

      Etag: "w/a/b"

  (I have to check the RFC).

This module fixes this by:

* introducing a subclass :class:`WeakEtag` of str,
* providing alternatives to :func:`webob.descriptors.parse_etag_response` and
  :func:`webob.descriptors.serialize_etag_response`
  (:func:`new_parse_etag_response` and :func:`new_serialize_etag_response`
  respectively) that use :class:`WeakEtag` to handle weak etags correctly,
* overriding :class:`MyResponse`.`etag` to use the new functions above.

In the long run, these improvements can serve as a base to fix :mod:`webob`.

"""

from webob.descriptors import parse_etag_response as old_parse_etag_response
from webob.descriptors import serialize_etag_response \
    as old_serialize_etag_response
from webob.response import converter, header_getter, Response

class WeakEtag(str):
    "A class for distinguisging weak etags from other etags."
    def __repr__(self):
        return "WeakEtag(%r)" % str(self)

def new_parse_etag_response(value):
    "I add support for :class:`WeakEtag`"
    if value is not None and value.lower()[:2] == "w/":
        ret = WeakEtag(old_parse_etag_response(value[2:]))
    else:
        ret = old_parse_etag_response(value)
    #print "===", "new_parse_etag_response", repr(value), "->", repr(ret)
    return ret
                            
def new_serialize_etag_response(value):
    "I add support for :class:`WeakEtag`"
    ret = old_serialize_etag_response(value)
    if isinstance(value, WeakEtag):
        ret = "w/%s" % ret
    #print "===", "new_serialize_etag_response", repr(value), "->", repr(ret)
    return ret

class MyResponse(Response):
    """A subclass of :class:`webob.Response` more adapted to RDF-REST.
    """
    default_content_type = "text/plain"
    default_conditional_response = True

    etag = converter(
        header_getter('ETag', '14.19'),
        new_parse_etag_response,
        new_serialize_etag_response,
        'Fixed entity tag',
        )

