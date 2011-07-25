#!/bin/bash
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

#
# I try a number of HTTP queries on localhost:8001, and check that the HTTP 
# return code is as expected. I display an error message for each failed test.
#
# Note that I normally start and stop my own server, but will silently use
# an existing one if any. This is useful if you want to inspect the standard
# error of the server while some tests are failing.
#
# ADDED: this script used to serve as a test for rdfrest.mixins, but they now
# have their own unit-test

cd `dirname $0`
SERVER=./rdfrest_demo.py
. ./lib_test_http.sh

######## DATA GENERATORS ########

make_new_foo () {
    # $1 node (defaults to <new_foo>)
    # $2 additional text to be appended to the turtle
    local node=${1:-<new_foo>}
    echo """
        @prefix : <http://example.org/> .
        <> :rw_in $node .

        $node a :Foo ;
        :rw_out \"rw_in and rw_out are required\".

        $2
    """
}

make_new_bar () {
    # $1 node (defaults to <new_bar/>)
    # $2 additional text to be appended to the turtle
    local node=${1:-<new_bar/>}
    echo """
        @prefix : <http://example.org/> .
        <> :rw_in $node .

        $node a :Bar ;
        :rw_out \"rw_in and rw_out are required\".

        $2
    """
}

######## JOBS ########

job1 () { # check get and put on the server root
# check that the server is here
check_get  200 localhost:8001/
local ORIGINAL=$PAYLOAD
local THE_ETAG=$ETAG
# trying to PUT the same content but without any ETag
check_put  403 localhost:8001/ /dev/stdin no_etag <<<$ORIGINAL
# trying to PUT the same content but without a wrong etag
check_put  412 localhost:8001/ /dev/stdin wrong_etag wrong_etag <<<$ORIGINAL
# trying to PUT the content back
check_put  200 localhost:8001/ /dev/stdin same_content $THE_ETAG <<<$ORIGINAL
# trying to PUT a valid content
check_put  200 localhost:8001/ /dev/stdin valid_content $ETAG <<EOF
  @prefix : <http://example.org/> .
  :something :rw_in <> .

  <> a :Bar ;
    :rw_out "rw_in and rw_out are required" .

EOF
local THE_ETAG=$ETAG
# violating reserved namespace (+type)
check_put  403 localhost:8001/ /dev/stdin add_reserved_type $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  :something :rw_in <> .

  <> a :Bar, :Baz ;
    :rw_out "rw_in and rw_out are required" .

EOF
# violating reserved namespace (-type)
check_put  403 localhost:8001/ /dev/stdin rem_reserved_type $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  :something :rw_in <> .

  <>
    :rw_out "rw_in and rw_out are required" .

EOF
# violating reserved namespace (out)
check_put  403 localhost:8001/ /dev/stdin reserved_out $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  :something :rw_in <> .

  <> a :Bar, :Baz ;
    :other_out "forbidden";
    :rw_out "rw_in and rw_out are required" .

EOF
# violating post-only property in reserved namespace (out)
check_put  403 localhost:8001/ /dev/stdin post_only_in $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  :something :rw_in <> .

  <> a :Bar, :Baz ;
    :rw_out "rw_in and rw_out are required" .

  :something :ro_in <> .
EOF
# violating post-only property in reserved namespace (out)
check_put  403 localhost:8001/ /dev/stdin post_only_out $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  :something :rw_in <> .

  <> a :Bar, :Baz ;
    :ro_out "forbidden";
    :rw_out "rw_in and rw_out are required" .

EOF
# violating reserved namespace (in)
check_put  403 localhost:8001/ /dev/stdin reserved_in $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  :something :rw_in <> .

  <> a :Bar, :Baz ;
    :rw_out "rw_in and rw_out are required" .

  :something :other_in <> .
EOF
# violating cardinality (min in)
check_put  403 localhost:8001/ /dev/stdin card_min_in $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  <> a :Bar ;
    :rw_out "rw_in and rw_out are required" .

EOF
# violating cardinality (max in)
check_put  403 localhost:8001/ /dev/stdin card_max_in $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  :something :rw_in <> .
  :something_else :rw_in <> .

  <> a :Bar ;
    :rw_out "rw_in and rw_out are required" .

EOF
# violating cardinality (min out)
check_put  403 localhost:8001/ /dev/stdin card_min_out $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  :something :rw_in <> .

  <> a :Bar .

EOF
# violating cardinality (max out)
check_put  403 localhost:8001/ /dev/stdin card_max_out $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  :something :rw_in <> .

  <> a :Bar ;
    :rw_out "rw_in and rw_out are required", "too many values" .

EOF
}

job2() { # check POST on the server root
# accept a parameter, which is the URI to which POST will be attempted
check_post 201 localhost:8001/ /dev/stdin new_foo <<<`make_new_foo`
check_post 201 localhost:8001/ /dev/stdin new_foo_bnode <<<$(make_new_foo '_:x')
check_post 400 localhost:8001/ /dev/stdin candidate_with_fragment \
    <<<$(make_new_foo '<foo#frag>')
check_post 400 localhost:8001/ /dev/stdin candidate_not_linked <<EOF
  @prefix : <http://example.org/> .
  <new_foo> a :Foo ;
    :rw_in <new_foo> ;
    :rw_out "rw_in and rw_out are required".
EOF
check_post 400 localhost:8001/ /dev/stdin too_many_candidates \
    <<<$(make_new_foo '<new_foo1>'; make_new_foo '<new_foo2>')
check_post 400 localhost:8001/ /dev/stdin uri_and_bnodes \
    <<<$(make_new_foo '<new_foo1>'; make_new_foo '_:x' )
check_post 400 localhost:8001/ /dev/stdin uri_and_fragments \
    <<<$(make_new_foo '<with_frag>' "<> :rw_in <other_frag#frag> .")
check_post 201 localhost:8001/ /dev/stdin uri_and_fragments \
    <<<$(make_new_foo '<with_frag>' "<> :rw_in <with_frag#frag> .")
check_post 201 localhost:8001/ /dev/stdin new_bar <<<$(make_new_bar)
check_post 201 localhost:8001/ /dev/stdin new_bar_bnode <<<$(make_new_bar '_:x')
check_post 403 localhost:8001/ /dev/stdin new_bar_wrong_URI \
    <<<$(make_new_bar '<slashless_uri>')
}

job3() { # check POST on another resource
check_post 201 localhost:8001/ /dev/stdin new_bar <<<$(make_new_bar '<bar/>')
check_post 201 localhost:8001/bar/ /dev/stdin new_foo_on_bar <<<$(make_new_foo)
check_post 201 localhost:8001/bar/ /dev/stdin new_bar_on_bar \
    <<<$(make_new_bar '<bar/>')
check_post 201 localhost:8001/bar/bar/ /dev/stdin new_foo_on_bar2 \
    <<<$(make_new_foo)
}

job4 () { # PUTting read-only data generated after a POST
# test whether we can PUT into a bar that contains link to its children
# 1) post a child to /
check_post 201 localhost:8001/ /dev/stdin new_bar <<EOF
  @prefix : <http://example.org/> .
  <> :rw_in <bar/> .

  <bar/> a :Bar ;
    :rw_out "rw_in and rw_out are required".
EOF
# 2) get ETAG for /
check_get 200 localhost:8001/
# 3) PUT same content to /
check_put 200 localhost:8001/ /dev/stdin same_with_posted $ETAG <<<$PAYLOAD
# 4) PUT same content without link to child (must fail as it is reserved)
check_put 403 localhost:8001/ /dev/stdin new_bar $ETAG <<EOF
  @prefix : <http://example.org/> .
  <> :rw_in <bar/> .

  <bar/> a :Bar ;
    :rw_out "rw_in and rw_out are required".
EOF
}

job5 () { # PUTing postable-only properties
# post a new Foo and try to add read-only properties to it
check_post 201 localhost:8001/ /dev/stdin new_foo <<<`make_new_foo '<foo1>'`
# get the etag of the newly created resource
check_get  200 localhost:8001/foo1
THE_ETAG=$ETAG
# tryint to put :ro_in 
check_put  403 localhost:8001/foo1 /dev/stdin add_ro_in $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  <..> :rw_in <> .
  <..> :ro_in <> .

  <> a :Foo ;
    :rw_out "rw_in and rw_out are required" .
EOF
# tryint to put :ro_out 
check_put  403 localhost:8001/foo1 /dev/stdin add_ro_out $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  <..> :rw_in <> .

  <> a :Foo ;
    :ro_out "ro_in and ro_out are read-only";
    :rw_out "rw_in and rw_out are required" .
EOF

# post a new Foo with read-only properties and try to remove them
check_post 201 localhost:8001/ /dev/stdin new_foo <<<`make_new_foo '<foo2>' """
  <> :ro_in <foo2>.
  <foo2> :ro_out \"ro_in and ro_out are read-only\".
"""`
# get the etag of the newly created resource
check_get  200 localhost:8001/foo2
local THE_ETAG=$ETAG
# tryint to remove :ro_in 
check_put  403 localhost:8001/foo2 /dev/stdin rem_ro_in $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  <..> :rw_in <> .

  <> a :Foo ;
    :ro_out "ro_in and ro_out are read-only";
    :rw_out "rw_in and rw_out are required" .
EOF
# tryint to remove :ro_out 
check_put  403 localhost:8001/foo2 /dev/stdin rem_ro_out $THE_ETAG <<EOF
  @prefix : <http://example.org/> .
  <..> :rw_in <> .
  <..> :ro_in <> .

  <> a :Foo ;
    :rw_out "rw_in and rw_out are required" .
EOF
}

job6 () { # check etags
check_get 200 localhost:8001/
local ETAG1=$ETAG
check_get 200 localhost:8001/
assert $ETAG == $ETAG1
check_get 304 localhost:8001/ $ETAG1
check_get 200 localhost:8001/ "'wrong_etag'"
assert $CODE == 200
check_put 200 localhost:8001/ /dev/stdin other_content $ETAG1 \
    <<<"$PAYLOAD <> a <http://other.example.com/Baz> ."
assert $ETAG != $ETAG1
check_get 304 localhost:8001/ $ETAG
}

######## MAIN ########

test_http_main "$@"
