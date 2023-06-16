from lark import Lark

grammar = r"""
name_decl : "name" ESCAPED_STRING

%import common.ESCAPED_STRING
%import common.WS
%ignore WS
"""

greet_parser = Lark(grammar, start="name_decl")
