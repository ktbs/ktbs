Installing kTBS behind an Nginx HTTP server
===========================================

Nginx can be used as a proxy in front of a running instance of kTBS.
This has a number of advantages:

* adds HTTPS support;
* allows kTBS to co-exist with other services under the same domain name and port number;
* allows to add access control (not documented yet).

kTBS configuration
++++++++++++++++++

kTBS must first be `installed <install-local-ktbs>`:doc: 
and run independently, listening on a local port.
It must also be aware of the public URI under which it is published
(in the example above: `https://your.domain.com/path/to/ktbs/`).
This is achieved with the following configuration directives:

.. code-block:: ini

  [server]
  scheme = http
  host-name = localhost
  port = 8002

  fixed-root-uri = https://your.domain.com/path/to/ktbs/


Nginx configuration
+++++++++++++++++++

Here is an example Nginx configuration file:

.. code-block:: nginx

  server {
          server_name your.domain.com;
          listen 443;
          ssl on;
          # ... other parameters

          location /path/to/ktbs {
              proxy_pass http://localhost:8002/;
          }
  }

