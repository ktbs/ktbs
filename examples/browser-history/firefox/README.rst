===========================================
Populate the kTBS with your firefox history
===========================================

The following code uses the kTBS python client to populate the kTBS with your firefox navigation history.

It was used to make some stats and profiling so you must install `psutil <http://pypi.python.org/pypi/psutil>`_ in your virtualenv::

    $ pip install psutil

Use **-h** to view the script options::

    $ python browser_history_to_ktbs.py -h
    usage: browser_history_to_ktbs.py [-h] [-f [FILE]] [-r [ROOT]] [-o [ORIGIN]]
                                      [-l [LIMIT]] [-p] [-s] [-v]

    Fill a stored trace with browser history items as obsels.

    optional arguments:
      -h, --help            show this help message and exit
      -f [FILE], --file [FILE]
                            File containings the sqlite data to parse. Default is
                            places.sqlite
      -r [ROOT], --root [ROOT]
                            Enter the uri of the kTBS root. Default is
                            http://localhost:8001/
      -o [ORIGIN], --origin [ORIGIN]
                            Enter the trace origin. Default is
                            1970-01-01T00:00:00Z
      -l [LIMIT], --limit [LIMIT]
                            Enter the maximun number of items to collect. Default
                            is 10000
      -p, --profile         Profile current code
      -s, --stats           Mesure execution time
      -v, --verbose         Display print messages

Copy your history database, which in a file named **places.sqlite** located in your firefox profile folder to the current folder, or specify the full path with **-f** option.

Then execute the following command to extract 1000 items of your history::

    $ python browser_history_to_ktbs.py -f /tmp/places.sqlite -l 1000

The model and obsels have to be developped.

When asking the code profiling, a ``profile-ktbs-yyyy-mm-dd-hh:mm.prof`` file will be created in the current directory. You can then process the profiling data with the `pstats.Stats() class <http://docs.python.org/library/profile.html#module-pstats>`_

For a good introduction to profiling, look at Doug Hellmann blog post `profile, cProfile, and pstats – Performance analysis of Python programs <http://www.doughellmann.com/PyMOTW/profile>`_::

    >>> import pstats
    >>> ktbs_ps=pstats.Stats("profile-ktbs-2012-04-03-15:45.prof")
    >>> ktbs_ps.sort_stats("time")
    <pstats.Stats instance at 0x10047d440>
    >>> ktbs_ps.print_stats(30)
    Tue Apr  3 15:46:02 2012    profile-ktbs-2012-04-03-15:45.prof

             2727919 function calls (2727483 primitive calls) in 17.013 seconds

       Ordered by: internal time
       List reduced from 594 to 30 due to restriction <30>

       ncalls  tottime  percall  cumtime  percall filename:lineno(function)
       185153   11.461    0.000   11.461    0.000 {method 'recv' of '_socket.socket' objects}
         6056    0.510    0.000   12.210    0.002 /opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/socket.py:406(readline)
         2016    0.484    0.000    0.484    0.000 {method 'connect' of '_socket.socket' objects}
         1008    0.308    0.000    0.308    0.000 {_socket.getaddrinfo}
        24092    0.125    0.000    0.187    0.000 /Users/fconil/PyEnvs27/ktbs-virtualenv/lib/python2.7/site-packages/rdflib/plugins/memory.py:439(triples)
        13042    0.119    0.000    0.138    0.000 /Users/fconil/PyEnvs27/ktbs-virtualenv/lib/python2.7/site-packages/rdflib/namespace.py:121(term)
       167045    0.115    0.000    0.115    0.000 {method 'find' of 'str' objects}

    >>> ktbs_ps.sort_stats("pcalls")
    <pstats.Stats instance at 0x10047d440>
    >>> ktbs_ps.print_stats(30)
    Tue Apr  3 15:46:02 2012    profile-ktbs-2012-04-03-15:45.prof

             2727919 function calls (2727483 primitive calls) in 17.013 seconds

       Ordered by: call count
       List reduced from 594 to 30 due to restriction <30>

       ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    203280/203218    0.034    0.000    0.034    0.000 {len}
       192123    0.089    0.000    0.089    0.000 {method 'write' of 'cStringIO.StringO' objects}
       185153   11.461    0.000   11.461    0.000 {method 'recv' of '_socket.socket' objects}
       167045    0.115    0.000    0.115    0.000 {method 'find' of 'str' objects}
       165280    0.081    0.000    0.081    0.000 {isinstance}
       126599    0.033    0.000    0.055    0.000 {method 'has_key' of 'dict' objects}
        90454    0.095    0.000    0.095    0.000 /Users/fconil/PyEnvs27/ktbs-virtualenv/lib/python2.7/site-packages/rdflib/plugins/memory.py:286(createIndex)
        82539    0.038    0.000    0.058    0.000 {method 'get' of 'dict' objects}

    >>> ktbs_ps.sort_stats("cumulative")
    <pstats.Stats instance at 0x10047d440>
    >>> ktbs_ps.print_stats(30)
    Tue Apr  3 15:46:02 2012    profile-ktbs-2012-04-03-15:45.prof

             2727919 function calls (2727483 primitive calls) in 17.013 seconds

       Ordered by: cumulative time
       List reduced from 594 to 30 due to restriction <30>

       ncalls  tottime  percall  cumtime  percall filename:lineno(function)
            1    0.023    0.023   17.013   17.013 <string>:1(<module>)
            1    0.001    0.001   16.991   16.991 browser_history_to_ktbs.py:328(collect)
            1    0.078    0.078   16.036   16.036 browser_history_to_ktbs.py:197(collect_history_items)
         1001    0.039    0.000   15.942    0.016 /Users/fconil/PyEnvs27/ktbs-virtualenv/lib/python2.7/site-packages/ktbs/client/trace.py:94(create_obsel)
         1004    0.025    0.000   15.413    0.015 /Users/fconil/PyEnvs27/ktbs-virtualenv/lib/python2.7/site-packages/ktbs/common/utils.py:122(post_graph)
         1008    0.037    0.000   13.873    0.014 /Users/fconil/PyEnvs27/ktbs-virtualenv/lib/python2.7/site-packages/httplib2/__init__.py:1362(request)
         1008    0.006    0.000   13.720    0.014 /Users/fconil/PyEnvs27/ktbs-virtualenv/lib/python2.7/site-packages/httplib2/__init__.py:1285(_request)

Use `Gprof2Dot <http://code.google.com/p/jrfonseca/wiki/Gprof2Dot>`_ to visualize the caller graph based on profiling data::

    $ gprof2dot -f pstats test.prof | dot -Tpng -o caller-graph.png
