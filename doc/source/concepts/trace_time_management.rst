Trace time management
=====================

As a trace aims at representing an activity, time management is an important concept in the kTBS.

There are several areas where you manipulate timestamps, and we will focus at first on time management for the :doc:`Stored trace <trace>`.

Use ISO 8601 format for datetimes
---------------------------------

When you want to specify a real datetime, you MUST use the ISO-8601_ format and you should **specify the timezone**.

If you don't specify anything the datetime string (1) will be considered as an **UTC datetime** as when the datetime string ends with "Z" character (2) because "Z" character is the zone designator for the **zero UTC offset**.

::

    (1) "2016-01-06T08:15:00"
    (2) "2016-01-06T08:15:00Z"

The timezone is specified as an UTC-time-offset_, showing the difference in hours and minutes from Coordinated Universal Time (UTC), from the westernmost (−12:00) to the easternmost (+14:00).

Suppose that it is "09:15 am" in French local time on January 6th 2016, the UTC time is then "08:15 am". To specify that your datetime string as a French datetime, you must use the UTC datetime and add the French UTC offset (+ 1 hour) at the end of the UTC datetime string (3).

::

    (3) "2016-01-06T08:15:00+01:00"
        "2016-01-06T08:15:00+0100"
        "2016-01-06T08:15:00+01"

See `ISO-8601 time zones representation <https://en.wikipedia.org/wiki/ISO_8601#Time_zone_designators>`_

.. _ISO-8601: https://en.wikipedia.org/wiki/ISO_8601
.. _UTC-time-offset: https://en.wikipedia.org/wiki/List_of_UTC_time_offsets

Stored trace origin
-------------------

Each stored trace must have an origin which should be either:

- a datetime in ISO-8601 format, as specified above;
- the special string ``now``, which will be replaced by the current datetime;
- any other string that can not be interpreted as a datetime,
  called an **opaque** origin.

If you do not configure the trace origin explicitly, an random opaque origin will be generated and associated to the stored trace.

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

    If the trace origin is opaque, an error will occur.

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
Note that this only happens when the obsel is created.
If after that the obsel is modified, and one of the timestamp (``begin`` or ``beginDT``),
the other one will *not* be automatically updated.

