External
````````
.. important::

  Unlike other methods,
  this method does not work incrementally: each time the source trace is modified,
  the whole computed trace is re-generated.

  Also,
  this method can raise security issues,
  as it allows users to run arbitrary commands on the kTBS server.
  For this reason,
  this method is not anymore provided by default.
  It is available as a plugin, which must be explicitly enabled.

This method invokes an external program to compute a computed trace.
The external program is given as a command line,
expected to produce the obsels graph of the computed trace.

:sources: any number
:parameters:
  :model: the model of the computed trace
  :origin: the origin of the computed trace
  :command-line: the command line to execute (required)
  :format: the format expected and produced by the command line
  :min-sources: the minimum number of sources expected by the command-line
  :max-sources: the maximum number of sources expected by the command-line
  :feed-to-stdin: whether to use the external command standard input
                  (see below)

:extensible: yes (see below)

If parameter ``model`` (resp. ``origin``) is not provided,
the model (resp. origin) of the source trace will be used instead.

The command line query can contain magic strings
of the form ``%(param_name)s``,
that will be replaced by the value of
an additional parameter named ``param_name``.
Note that the following special parameters are automatically provided:

======================== ======================================================
 special parameter name   replaced by
======================== ======================================================
 ``__destination__``      The URI of the computed trace.
 ``__sources__``          The space-separated list of the source traces' URIs.
======================== ======================================================

Parameter ``format`` is used to inform the kTBS
of the format produced by the command line. Default is ``turtle``.

Parameters ``min-sources`` and ``max-sources`` are used to inform the kTBS
of the minimum (resp. maximum) number of sources traces
expected by the command line.
This is especially useful in user-defined methods,
to control that the computed traces using them
are consistent with their expectations.

In the general case, the command line is expected to receive
the source trace(s) URI(s) as arguments,
and query the kTBS to retrieve their obsels.
As an alternative, parameter ``feed-to-stdin`` can be set
to have the kTBS send the source trace obsels
directly to the standard input of the external command process.
Note that this is only possible when there is exactly one source,
and the format used to serialize the obsels
will be the same as parameter ``format``.
