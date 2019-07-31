Quick start
===========

.. code:: sh

    docker build -t ktbs-dev .
    SRC=/absolute/path/to/your/working-tree
    docker run --name ktbs01 -d -v $SRC:/src -v $PWD/app:/app -p 1234:1234 ktbs-dev
    # you now have a kTBS listening on http://localhost:1234/


Structure of the Docker container
=================================

This docker file builds an image for running a development version of kTBS.
It has two volume that must be linked to existing directories:

* /src must contain a working copy of http://github.com/ktbs/ktbs
* /app must contain at least a config file named app.conf
  (an example is provided)

It is designed for flexibility:
by storing the source and the config file in volumes,
it makes it easy to change the configuration or update the source code.
In fact, each time the container starts,
it runs a 'pip install -e /src' to ensure that it is up-to-date.
This takes some time on the first run,
but should be quite fast afterwards.
