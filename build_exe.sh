#!/bin/sh
mkdir -p build
mkdir -p dist
echo "*" >build/.gitignore
echo "*" >dist/.gitignore
exec pyinstaller bin/ktbs \
    --hidden-import rdflib.plugins.memory \
    --hidden-import rdflib.plugins.sleepycat \
    --hidden-import rdflib.plugins.parsers.notation3 \
    --hidden-import rdflib.plugins.parsers.nt \
    --hidden-import rdflib.plugins.serializers.n3 \
    --hidden-import rdflib.plugins.serializers.nt \
    --hidden-import rdflib.plugins.serializers.rdfxml \
    --hidden-import rdflib.plugins.serializers.turtle \
    --hidden-import ktbs.plugins.cors \
    --hidden-import ktbs.plugins.meth_external \
    --hidden-import ktbs.plugins.profiler \
    --hidden-import ktbs.plugins.sparql_endpoints \
    --hidden-import ktbs.plugins.xgereco_obsel_table \
    -F
