# -*- coding: utf-8 -*-
"""
    sparqllexer
    ~~~~~~~~~~~

    Extension to add a sparql lexer to Sphinx.

    ``http://sphinx.pocoo.org/ext/appapi.html?highlight=pygments#sphinx.application.Sphinx.add%5Flexer``

    It uses the Kier Davis code: ``https://github.com/kierdavis/SparqlLexer``.

    .. code-block:: sparql

       Sparql example TODO

    changelog
    `````````

    2013-21-21: pchampin: added incomplete support for functions
    2012-11-27: pchampin: improved a number of token definition

"""

from pygments.lexer import RegexLexer, bygroups
from pygments.formatter import Formatter
from pygments.token import *

PREFIX = r"[a-zA-Z][-_a-zA-Z0-9]*"
NAME = r"[_a-zA-Z][-_a-zA-Z0-9]*"

class SparqlLexer(RegexLexer):
  name = "Sparql"
  aliases = ["sparql", "ttl"]
  filenames = ["*.ttl"]
  alias_filenames = ["*.txt"]
  mimetypes = ["text/x-sparql", "text/sparql", "application/sparql"]
  
  tokens = {
    "root": [
      (r"#.*\n", Comment.Single),
      (r",|;|\.|\(|\)|\[|\]|\{|\}|\^\^", Punctuation),
      ("(%s)?\:(%s)?" % (PREFIX, NAME), Name.Tag),
      (r"_\:%s" % NAME, Name.Variable),
      (r"[\$\?]%s" % NAME, Name.Variable),
      (r"<[^>]*>", Name.Constant),
      (r"(['\"]).+\1", String.Double),
      (r"\d+(\.\d*)?([eE][+\-]?\d+)?", Number),
      (r"\.\d+([eE][+\-]?\d+)?", Number),
      (r"\s+", Whitespace),
      (r"true|false", Keyword.Constant),
      (r"(?i)prefix|select|construct|ask|describe|where|from|as|graph|filter"
        "|optional|a|union|not exists", Keyword.Reserved),
      (r"(?i)distinct|reduced|group by|order by|limit|offset|asc|desc",
       Keyword.Reserved),
      (r"(?i)count|sum|avg|min|max|groupconcat|sample",
       Keyword.Reserved),
      (r"(?i)delete|insert|data|load|clear|create|drop|copy|move|add",
       Keyword.Reserved),
      (r"(?i)regex",
       Keyword.Function),
      (r"\+|-|\*|/|=|!|<|>|\&|\|", Punctuation),
      (r".+", Error),
    ],
  }

def setup(app):
    # An instance of the lexer is required
    sparqlLexer = SparqlLexer()
    app.add_lexer('sparql', sparqlLexer)
