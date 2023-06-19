from lark import Lark

grammar = r"""
name_decl : "name:" NAME

NAME: LETTER+

%import common.LETTER
%import common.WS
%ignore WS
"""

greet_parser = Lark(grammar, start="name_decl")
