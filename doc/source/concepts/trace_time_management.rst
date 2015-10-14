Trace time management
=====================

As a trace aims at representing an activity, time management is an important concept in the kTBS.

There are several areas where you manipulate timestamps, and we will focus at first on time management for the :doc:`Stored trace <trace>`.

Use ISO 8601 format for datetimes
---------------------------------

When you want to specify a timestamp that is a real datetime, you MUST use the ISO-8601_ format, with punctuation, see W3C_NOTE-datetime_.

You should **specify the timezone**: if you don't specify anything (1) the timestamp will be considered as an **UTC datetime** as when you end the datetime string with "Z" character (2).

::

    (1) "2015-03-18T08:15:00"
    (2) "2015-03-18T08:15:00Z"

The timezone is specified as an UTC-time-offset_, showing the difference in hours and minutes from Coordinated Universal Time (UTC), from the westernmost (−12:00) to the easternmost (+14:00).

For example, to indicate that the above datetime is in a French timezone, add the UTC offset "+01:00" at the end of the datetime string (3).

::

    (3) "2015-03-18T08:15:00+01:00"

.. _ISO-8601: https://en.wikipedia.org/wiki/ISO_8601
.. _W3C_NOTE-datetime: http://www.w3.org/TR/NOTE-datetime
.. _UTC-time-offset: https://en.wikipedia.org/wiki/List_of_UTC_time_offsets

Stored trace origin
-------------------

Each stored trace must have an origin which should be :

- a timestamp as specified above,
- an *opaque string*, i.e a string that can not be interpreted as a datetime.

If you do not configure the trace origin explicitely, an opaque random generated string will be associated to the stored trace.

Trace Model time-unit
---------------------

The Trace time-unit is specified in the :doc:`Trace Model <trace_model>`.

The kTBS supports 3 time-units:

- ``:millisecond`` which is the **default unit**
- ``:second``
- ``:sequence``

Obsels timestamps
-----------------

For the sake of simplicity, we will only consider the "begin timestamp".

When you create an Obsel in the kTBS, you may :

- omit the "begin timestamp"
- specify an integer "begin timestamp"
- specify a datetime "begin timestamp"

No timestamp specified
++++++++++++++++++++++

If no timestamp is specified, the kTBS will compute the "begin timestamp".

If the trace model unit is ``:second`` or ``:millisecond``, the "begin timestamp" is the difference between the current datetime and the trace origin.

.. warning::

    If the trace origin is an opaque string, an error will occur.

If the trace model unit is ``:sequence``, an automatic integer numbering could be generated.

.. warning::

    This is not yet implemented.

Integer begin timestamp
+++++++++++++++++++++++

The integer value must be passed in the ``:hasBegin`` rdf parameter or in the ``"begin":`` parameter if passed in json format.

The kTBS keeps the integer as ``:hasBegin`` value.

Datetime begin timestamp
+++++++++++++++++++++++++

The datetime value must be passed in the ``:hasBeginDT`` rdf parameter or in the ``"beginDT":`` parameter if passed in json format.

The kTBS keeps the datetime as ``:hasBeginDT`` value and computes ``:hasBegin`` as the difference between the ``:hasBeginDT`` value and the trace origin using the trace model unit.

