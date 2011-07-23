#    This file is part of KTBS <http://liris.cnrs.fr/silex/2009/ktbs>
#    Copyright (C) 2009 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> / SILEX
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


# I provide a framework for testing a number of HTTP queries on a given server.
#
# I expect the path to the server to be provided as the global variable SERVER.
# I expect scripts using me to
# * define a set of functions job1, job2, job3... containing test-sets
# * pass the script arguments to the function test_http_main below
#
# The function test_http_main execute all the jobs in order. It stops at the
# first failed test, unless option '--batch' is provided, in which case all
# tests are performed whatever their result. If option '--keep' is provided,
# the server is not stopped after an error, which allows to inspect it for
# debugging. Finally, test_http_main accepts a numeric argument, which allows
# to start at the given job (skipping all the ones before).
#
# Failure messages are written on the standard output, while everything else is
# written on the standard error (controlled by the '--verbose' and '--quiet'
# options). So an automated test procedure can scan the standard output to
# check for failed tests.
#
# jobX functions can use the functions defined below
# * check_get : perform a GET query and check the status code
# * check_put : perform a PUT query and check the status code
# * check_post : perform a POST query and check the status code
# * check_ctype : perform a GET query and check the content-type
# * assert : check a given condition (using the syntax of 'test')
#
# All HTTP response are parsed and used to set a number of global variables,
# which can be used in further calls to 'assert'. This is performed by the file
# 'lib_http_test_parse_response.sed'. Refer to it for the list of those
# variables.
#


######## TEST BUILDING BLOCKS ########

# the functions below are documented in their first lines

assert () {
    # usage: assert [ --msg ERROR_MESSAGE ] TEST ARGUMENTS
    if [ "$1" == "--msg" ]; then
        local MSG=$2
        shift 2
    else
        local MSG="FAIL: Assertion $@"
    fi
    if [ "$@" ]; then
        true
    else
        echo $MSG
        echo " " $PAYLOAD
        if [ "$BATCH" = "" ]; then
            if [ "$KEEP" = "" ]; then
                stop_server
            else
                echo "Keeping server alive for testing..."
                wait $TEST_SERVER_PID
            fi
            exit 1
        fi
    fi
}

check_get () {
    # $1 expected HTTP code
    # $2 CURL URL
    # $3 etag (optional)
    if [ "$3" != "" ]; then
        local IF_NONE_MATCH="If-None-Match: $3"
        local HAS_ETAG="(etag)"
    else
        local IF_NONE_MATCH=""
        local HAS_ETAG=""
    fi
    parse_response $CURL "$2" -H "$IF_NONE_MATCH"
    local MSG="FAIL: GET  $2 $HAS_ETAG => $CODE $STATUSMSG (expected $1)"
    assert --msg "$MSG" "$CODE" == "$1"
}

check_post () {
    # $1 expected HTTP code
    # $2 CURL URL
    # $3 turtle file to post
    # $4 data name (only if $3 == /dev/stdin)
    if [ "$3" == "/dev/stdin" ]; then
        local DATA_NAME="{$4}"
    else
        local DATA_NAME=$3
    fi
    local POST_OPT="-H content-type:text/turtle --data-binary @$3"
    parse_response $CURL $POST_OPT "$2"
    local MSG="FAIL: POST $2 $DATA_NAME => $CODE $STATUSMSG (expected $1)"
    assert --msg "$MSG" "$CODE" == "$1"
}

check_put () {
    # $1 expected HTTP code
    # $2 CURL URL
    # $3 turtle file to post
    # $4 data name (only if $3 == /dev/stdin)
    # $5 etag (optional; $4 if $3 != /dev/stdin)
    if [ "$3" == "/dev/stdin" ]; then
        local DATA_NAME="{$4}"
        local THE_ETAG=$5
    else
        local DATA_NAME=$3
        local THE_ETAG=$4
    fi
    if [ "$THE_ETAG" != "" ]; then
        local IF_MATCH="If-Match: $THE_ETAG"
        local HAS_ETAG="(etag)"
    fi
    local PUT_OPT="-H content-type:text/turtle --data-binary @$3 -X PUT"
    parse_response $CURL $PUT_OPT "$2" -H "$IF_MATCH"
    local MSG="FAIL: PUT  $2 $DATA_NAME $HAS_ETAG => $CODE $STATUSMSG (expected $1)"
    assert --msg "$MSG" "$CODE" == "$1"
}

check_ctype () {
    # $1 expected content type
    # $2 CURL URL
    # $3 accept field (optional)
    if [ "$3" == "" ]; then
        local ACCEPT="Accept: text/turtle,application/rdf+xml;q=0.8,*/*;q=0.1"
    else
        local ACCEPT="Accept: $3"
    fi
    parse_response $CURL "$2" -H "$ACCEPT"
    local MSG="FAIL: Content-type $2 $3 => $CONTENT_TYPE (expected $1)"
    assert --msg "$MSG" "$CONTENT_TYPE" == "$1"
}


######## MAIN FUNCTION ########

usage () {
  echo "usage: $0 [--batch|--keep] [--verbose|--quiet] [start]" >&2
}

test_http_main () {
# $@: the arguments given to the script
# parse arguments
while [ "$*" != "" ]; do
    if [ "$1" = "--batch" -o "$1" = "-b" ]; then
        BATCH=yes
    elif [ "$1" = "--keep" -o "$1" = "-k" ]; then
        KEEP=yes
    elif [ "$1" = "--verbose" -o "$1" = "-v" ]; then
        VERBOSE=yes
    elif [ "$1" = "--quiet" -o "$1" = "-q" ]; then
        QUIET=yes
    elif [ "$1" = "--help" -o "$1" = "-h" ]; then
        usage
        exit 0
    elif [ "$START" = "" ]; then
        START="$1"
    else
        usage
        exit 1
    fi
    shift
done

trap stop_server SIGINT

# main loop
local i=${START:-1}
while true; do
    type job$i &>/dev/null || break
    if [ "$QUIET" != "yes" ]; then
        echo === job$i >&2
    fi
    start_server
    job$i
    stop_server
    i=$(expr $i + 1)
done
true
}

######## UTILITY VARIABLES AND FUNCTIONS ########

CURL="curl -s -D /dev/stderr"

start_server () {
    if [ "$VERBOSE" = "yes" ]; then
        "$SERVER" >&2 &
    else
        "$SERVER" &>/dev/null &
    fi
    TEST_SERVER_PID=$!
    disown # prevent a message on stdout when server will be killed
    # wait until server is running
    while true; do
        curl localhost:8001 -s >/dev/null && break
    done
}

stop_server () {
    if (ps | grep -q $TEST_SERVER_PID); then
        kill $TEST_SERVER_PID
    fi
}

parse_response () {
    # usage: parse_response COMMAND LINE
    # override variables that may be absent from headers
    ETAG=
    X_UP_TO_DATE=
    # get new variable values from header
    OUT1="/tmp/$(basename $0)-$$.1.sh"
    OUT2="/tmp/$(basename $0)-$$.2.sh"
    VARS="/tmp/$(basename $0)-$$.sh"
    "$@" >"$OUT1" 2>"$OUT2"
    cat "$OUT2" "$OUT1" | sed -f lib_test_http_parse_response.sed >"$VARS"
    #echo "===" ">>>"; cat "$VARS"; echo "===" "<<<" ## DEBUG
    . "$VARS"
    PAYLOAD=`cat $OUT1`
    rm -f "$VARS" "$OUT1" "$OUT2"
    if [ "$CODE" == "" ]; then CODE=FAIL; fi
}
