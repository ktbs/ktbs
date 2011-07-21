#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Try to write the python version of the populate shell scripts.
"""

from os.path import abspath, dirname, join
from sys import path

source_dir = dirname(dirname(abspath(__file__)))
lib_dir = join(source_dir, "lib")
path.insert(0, lib_dir)

from ktbs.client.root import KtbsRoot
from logging import basicConfig, DEBUG
from sys import stdout

def main():
    basicConfig(filename='populate-ktbs.log',level=DEBUG)

    root = KtbsRoot("http://localhost:8001/")
    print "----- root.label: ", root.label

    base1 = root.create_base("base1/")

    model1 = base1.create_model(parents=None, id="model1/")

    try:
        print "----- base1.label: ", base1.label
        print "----- base1.uri: ", base1.uri
        print "----- bases: ", [ b.label for b in root.bases ]

        print "----- model1.label: ", model1.label
        print "----- model1.uri: ", model1.uri

    finally:
        model1.remove()
        base1.remove()

if __name__ == "__main__":
    main()
