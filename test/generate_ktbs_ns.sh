#!/bin/sh

# I generate the list of KTBS URI that are actually used in the source.
# They are formatted so as to be easily inserted in ktbs/namespaces.py

find lib -name \*.py -exec grep 'KTBS\.[a-zA-Z]' {} -E \; \
| sed 's/^.*KTBS\.\([a-zA-Z0-9_-]*\).*$/        "\1",/' | sort -u
