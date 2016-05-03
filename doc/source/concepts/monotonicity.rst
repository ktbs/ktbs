Monotonicity
============

Monotonicity is, loosely,
the property of evolving always in the same "direction".

Traces have two ways of evolving: by collecting obsels, or by being amended.
While amendment allows any kind of evolution of the content of the trace,
collecting is more constrained.

By definition, collecting is restricted to adding new obsels,
with their attributes and relations to previously created obsels.
In a sense, those constrained can be considered as a kind of monotonicity,
that we call **logical monotonicity**.

A stronger version of monotonicity is **strict monotonicity**:
it is verified if every newly added obsel has its *end* timestamp greater or equal than the *end* timestamp of any obsel already present in the trace.
In other words, a collecting is strictly monotonic if obsels are added in an order consistent with the internal chronology of the trace.

Why does it matter?
-------------------

The more constrained the evolution of a trace,
the more hypothesis transformations can make,
hence the more optimised they can be.

For example,
consider a transformation filtering obsels between two timestamp *s* and *f*.
If the source trace changes in a strictly monotonic way,
once an obsel after *f* is encountered,
the transformation can safely ignore all subsequent obsels without even checking their timestamps.

On the other hand,
if the source trace changes in a (non-strict) logically monotonic way,
for every new obsel,
the transformation has to check its timestamp,
to decide whether to included it or not in the computed trace.


Monotonicity of computed traces
-------------------------------

Monotonicity does not only apply to stored traces,
but to computed traces as well.
In that case, the monotonicity depends on two factors:
the monotonicity of the source trace(s) (if any),
and the applied method.

In the example above (temporal filtering),
the method perfectly preserves the monotonicity of its source trace.
The computed trace will evolve in a strict (resp. logical, non)
monotonic way if the source trace evolves in a strict (resp. logical, non)
monotonic way.

On the other hand, consider a transformation method that would keep only the last obsel of the source trace.
This kind of transformation does not preserve monotonicity:
even if the source trace is strictly monotonic,
the transformed trace will evolve non monotonically.
Indeed, each time an obsel is added to the source trace,
any existing obsel in the transformed trace will be *removed*,
and replaced by a copy of the latest obsel.

Current handling in kTBS
------------------------

Every trace has a number of etags_ that change at various rates:

.. list-table::
    :header-rows: 1

    * -
      - standard etag
      - strict mon. etag
      - logical mon. etag
    * - obsels are deleted or modified
      - yes
      - yes
      - yes
    * - an obsel is added anywhere
      - yes
      - yes
      - no
    * - an obsel is added at the end of the trace
      - yes
      - no
      - no

Internally,
those etags are used by computed trace to determine how their sources have changed,
and hence decide on which optimisation they can apply.

Externally,
those etags are attached to different representations of the trace,
to help clients efficiently cache those representations.
For example,
considering a trace of 100 obsels,
the representation of "the first 10 obsels of that trace" will not change as long as the trace is modified in a strictly monotonic way.
On the other hand,
the representation of "the last 10 obsels of that trace" may be impacted by any kind of change on the trace.

Actually, kTBS uses a fourth etag,
related to so-called **pseudo monotonicity**.
This etag changes unless an obsel is added *near* the end of a trace
(*i.e.* inside a time window at the end of the trace,
called the *pseudo-monotonicity range*).
The rationale is that in some situations,
strict monotonicity can not be completely guaranteed
(*e.g.* when obsels are collected by several agents with different latencies),
but still obsels will not be added at arbitrary times.
Hence pseudo monotonicity is a weaker property than strict monotonicity,
but stronger than logical monotonicity.


.. _etags: https://tools.ietf.org/html/rfc7232#section-2.3

