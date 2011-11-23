# -*- coding: utf-8 -*-
"""
    turtlelexer
    ~~~~~~~~~~~

    Extension to add a turtle lexer to Sphinx.

    ``http://sphinx.pocoo.org/ext/appapi.html?highlight=pygments#sphinx.application.Sphinx.add%5Flexer``

    It uses the Kier Davis code: ``https://github.com/kierdavis/TurtleLexer``.

    .. code-block:: turtle

       Turtle example TODO

"""

from pygments.lexer import RegexLexer
from pygments.formatter import Formatter
from pygments.token import *

NAME = r"[_a-zA-Z][-_a-zA-Z0-9]*"

class TurtleLexer(RegexLexer):
  name = "Turtle"
  aliases = ["turtle", "ttl"]
  filenames = ["*.ttl"]
  alias_filenames = ["*.txt"]
  mimetypes = ["text/x-turtle", "text/turtle", "application/turtle"]
  
  tokens = {
    "root": [
      (r"#.*\n", Comment.Single),
      (r"<.+>", String.Regex),
      (r"(['\"]).+\1", String.Double),
      (r"_:%s" % NAME, Name.Constant),
      (r"@(prefix|base)", Keyword.Declaration),
      (r"@[a-z]+(-[a-z0-9]+)*", Name.Property),
      (r"\:|\;|\.|\^\^", Punctuation),
      ("%s\:%s" % (NAME, NAME), Name.Variable),
      (NAME, Name.Variable),
      (r"\s+", Whitespace),
      (r".+", Text),
    ],
  }

def setup(app):
    # An instance of the lexer is required
    turtleLexer = TurtleLexer()
    app.add_lexer('turtle', turtleLexer)
