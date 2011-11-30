Monotonicity
============

Monotonicity is, loosely, the property of evolving always in the same "direction".

Traces have two ways of evolving: by collecting obsels, or by being amended. While amendment allows any kind of evolution of the content of the trace, collecting is more constrained.

By definition, collecting is restricted to adding new obsels with their attributes and relations to previously created obsels. In a sense, those constrained can be considered as a kind of monotonicity that we call **simple monotonicity**.

A stronger version of monotonicity is **temporal monotonicity**: it is verified if newly added obsel have their *end* timestamp greater or equal than the *end* timestamp of any obsel already present in the trace. In other words, a collecting is temporally monotonic if obsels are created in an order consistent with the internal chronology of the trace.

In its current state, kTBS only accepts temporally monotonic collecting (see below for `Future evolutions`_).

Why enforce monotonicity?
-------------------------

The more constrained the evolution of a trace, the more hypothesis transformations can make, hence the more optimised they can be.

For example, consider a transformation filtering obsels between two timestamp *s* and *f*. If the source trace is temporally monotonic, once an obsel above *f* is encountered, the transformation can safely ignore all subsequent obsels without even checking their timestamps (unless of course the source trace gets amended).

Monotonicity of computed traces
-------------------------------

Monotonicity does not only apply to stored traces, but to computed traces as well. In that case, the monotonicity depends on two factors: the monotonicity of the source trace(s) (if any), and the applied method.

For example, a transformation method filtering obsels between two timestamps will perfectly preserve the monotonicity of its source trace: if it temporally monotonic, the transformed trace will also be; if it is only simply monotonic, the transformed trace can not be guaranteed to be more than simply monotonic.

Another example is a transformation method that would keep only the last obsel. This kind of transformation does not preserve monotonicity: even if the source trace is temporally monotonic, the transformed trace will evolve non monotonically. Indeed, each time an obsel is added to the source trace, any existing obsel in the transformed trace will be *removed* and replaced by a copy of the latest obsel.

In its current state, kTBS assumes that all methods ensure temporal monotonicity, just as collecting does. This allows method to assume that their traces are always temporally monotonic, but it also puts a very strong constraint on the order in which they produce obsels. This may change in `Future evolutions`_.

Future evolutions
-----------------

Although the constraint of temporal monotonicity may seem reasonable for collecting, it is not always easy to ensure -- for example when independent collectors contribute to the same trace. Furthermore, this constraint is much harder on computed traces, as illustrated above.

An easy evolution will be to allow collection to be only simply monotonic. In that case, the stored trace will be marked as amended. This is will require no change in the code of transformations, which can still make the assumption that a non-amended trace is temporally monotonic.

In the longer term, kTBS may let methods handle it as they wish. It would allow simply monotonic collecting, or even fine-grained amendment (by PUTing or DELETEing obsels individually). Methods would then have to be able handle those different kinds of events:

* temporally monotonic collecting,
* simply monotonic collecting,
* (amendment by obsel modification,)
* (amendment by obsel deletion,)
* global amendment.

This increased flexibility would increase the complexity of the Method python API, but fall-back behaviour can be provided to let implementers support only some of those events.

This would also make the internals of kTBS more complex: for the moment, source traces simply notify computed traces that they have changed, and computed traces only keep track of the last obsel they have seen. This kind of evolution would require each computed trace to maintain an event queue. This also raise the question of optimising the event queue: several events related to an obsel may be collapsed into a single one or even cancelled. This has to be studied.
