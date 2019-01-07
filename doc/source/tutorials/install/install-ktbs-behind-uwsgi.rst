Installing kTBS behing a uWSGI HTTP server
==========================================

uWSGI_ is an application server that supports the WSGI_ protocol.
Therefore, kTBS can be run using uWSGI_.

In fact, since uWSGI_ uses the INI format for its configuration file,
a single configuration file can be used for both kTBS and its uWSGI_ front-end.
It only requires to uncomment the uWSGI section in the example configuration file:

.. literalinclude:: ../../../../examples/wsgi/application.wsgi.conf
    :language: ini
    :emphasize-lines: 32-37


You can use uWSGI_ as a front server,
or behind Apache_ or Nginx_ used as a proxy.
Note that using the appropriate `Apache module`_ or `Nginx module`_,
a dedicated protocol can be used between uWSGI_ and the proxy server,
with less overhead than plain HTTP.


.. _uWSGI: https://uwsgi-docs.readthedocs.io/en/latest/
.. _WSGI: http://wsgi.org/
.. _Apache: http://httpd.apache.org/
.. _Nginx: http://nginx.org/
.. _Apache module: https://uwsgi-docs.readthedocs.io/en/latest/Apache.html
.. _Nginx module: https://uwsgi-docs.readthedocs.io/en/latest/Nginx.html