Ktbs Root
=========

This class has exactly one instance in each kTBS, whose URI is the base URI of the kTBS.

GET
---

Retrieve a description of the root. This description contains configuration settings of the kTBS, and references to its children resources, of type `Base`:doc:.

PUT
---

Alters the configuration settings of the kTBS. Children resources can not be modified, and may therefore be ommitted from the payload.

POST
----

Creates a new `Base`:doc:.


Description constraints
-----------------------

The descrtiption of a kTBS root must be `star shaped <star-shaped>`:ref:.
