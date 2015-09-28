# -*- coding: utf-8 -*-

#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2015 Françoise Conil <francoise.conil@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    KTBS is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    KTBS is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with KTBS.  If not, see <http://www.gnu.org/licenses/>.

"""
I implement a python log handler that sends log records to a kTBS instance.
"""

import logging
import httplib, urllib
import urlparse

import json

class kTBSHandler(logging.Handler):
    """
    A class which sends records to a Web server, using either GET or
    POST semantics.
    """
    def __init__(self, url):
        """
        Initialize the instance with the host and the request URL.
        A further version may take additional parameters (host, port, ...)

        :param url: URL of the external kTBS where the logs will be sent
        :param ktbsroot: URL of kTBS root to avoid posting into itself
        """
        logging.Handler.__init__(self)
        parsed_url = urlparse.urlparse(url)

        self.host = parsed_url.hostname
        self.port = parsed_url.port
        if parsed_url.port is not None:
            self.server_adress = "{:s}:{:d}".format(self.host, self.port)
        else:
            self.server_adress = self.host
        self.path = parsed_url.path
        self.url = url

    def mapLogRecord(self, record):
        """
        data = record.__dict__
        ==> Resultat :
        {'args': (),
         'created': 1425916467.008846,
         'exc_info': None,
         'exc_text': None,
         'filename': 'kTBShandler.py',
         'funcName': '<module>',
         'levelname': 'WARNING',
         'levelno': 30,
         'lineno': 114,
         'module': 'kTBShandler',
         'msecs': 8.846044540405273,
         'msg': 'warn message',
         'name': 'custom_HTTPHandler',
         'pathname': 'kTBShandler.py',
         'process': 16500,
         'processName': 'MainProcess',
         'relativeCreated': 36943.13597679138,
         'thread': 140330940864320,
         'threadName': 'MainThread'}
        """

        data = {'@type': '#kTBSInternals',
                'beginDT': record.created, 
                'm:exc_info': record.exc_info,
                'm:exc_text': record.exc_text,
                'm:filename': record.filename,
                'm:funcName': record.funcName,
                'm:levelname': record.levelname,
                'm:levelno': record.levelno,
                'm:lineno': record.lineno,
                'm:module': record.module,
                'm:msecs': record.msecs,
                'm:msg': record.msg,
                'm:name': record.name,
                'm:pathname': record.pathname,
                'm:process': record.process,
                'm:processName': record.processName,
                'm:relativeCreated': record.relativeCreated,
                'm:thread': record.thread,
                'm:threadName': record.threadName,
                'subject': record.module}

        return data

    def emit(self, record):
        """
        Emit a record.

        Send the record to the Web server as a percent-encoded dictionary.
        """

        try:
            h = httplib.HTTP(self.host, self.port)
            data = json.dumps(self.mapLogRecord(record))

            h.putrequest("POST", self.path)

            h.putheader("Host", self.server_adress)
            h.putheader("Content-type",
                        "application/json")
            h.putheader("Content-length", str(len(data)))
            h.endheaders(data)

            h.getreply()    #can't do anything with the result

        except (KeyboardInterrupt, SystemExit):
            raise

        except:
            self.handleError(record)
