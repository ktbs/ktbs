Installing a kTBS development version
=======================================

Instead of installing a stable kTBS version from the **PyPI** repository, you may need to install kTBS from a source code repository to get the latest changes.

Prerequisites
+++++++++++++

Make sure you have read and executed :ref:`common-prerequisites` instructions, i.e/ installed all dependencies.

The source code of kTBS is hosted on GitHub_.  This allows you to get the latest developer version.  For this, you need to have `Git <http://git-scm.com/>`_ installed; if you don't, type.

.. code-block:: bash

    $ sudo apt-get install git

Also look for a detailed explanation on how to :ref:`create a Python virtual environment <create-python-virtual_env>`.

Installing kTBS
+++++++++++++++

In the activated Python virtual environment, get the source code and use the ``-e`` option of the **pip** command to install kTBS from source.

.. code-block:: bash
    :emphasize-lines: 1,9

    (ktbs-env)user@mymachine:/home/user/ktbs-env$ git clone https://github.com/ktbs/ktbs.git
    Clonage dans 'ktbs'...
    remote: Counting objects: 3896, done.
    remote: Total 3896 (delta 0), reused 0 (delta 0), pack-reused 3896
    Réception d'objets: 100% (3896/3896), 1.40 MiB | 1.66 MiB/s, done.
    Résolution des deltas: 100% (2268/2268), done.
    Vérification de la connectivité... fait.

    (ktbs-env)user@mymachine:/home/user/ktbs-env$ pip install -e ktbs/

.. note::

    The ``-e`` option makes pip install the current project in editable mode (i.e. setuptools "develop mode").

    It means that whenever you update the repository with ``git pull``, of if you edit the code, the changes will be automatically taken into account.

Developer dependencies
++++++++++++++++++++++

If you plan to work on the source code, you might want to install developer dependencies as well.

.. code-block:: bash

    (ktbs-env)user@mymachine:/home/user/ktbs-env$ pip install -r ktbs/requirements.d/dev.txt

You can get information on the currently installed version of ktbs with the ``ktbs-info`` command.

.. code-block:: bash
    :emphasize-lines: 1

    (ktbs-env)user@mymachine:/home/user/ktbs-env$ ktbs-infos
    (system packages python3-dev and zlib2g-dev required by depencies)
    --------------------------------------------------------------------------------
    Platform information
    --------------------------------------------------------------------------------
    System:  Linux
    Release:  4.18.0-16-generic
    Machine:  x86_64
    sys.platform:  linux
    --------------------------------------------------------------------------------
    kTBS general information
    --------------------------------------------------------------------------------
    kTBS version:  0.6
    kTBS directory:  /home/pa/dev/ktbs.prj/ktbs.gh
    --------------------------------------------------------------------------------
    kTBS repository information
    --------------------------------------------------------------------------------
    git branch:  develop
    commit:  3a9d9d20601db62aa87bc14a6a35a6604df4200f

.. _GitHub: https://github.com/ktbs/ktbs
