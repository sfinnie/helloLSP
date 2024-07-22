from typing import List

from lark import Lark, Transformer, Tree, UnexpectedInput, UnexpectedToken
from dataclasses import dataclass

greeting_grammar = """
    start: declaration (_NEWLINE+ declaration)* _NEWLINE*
    
    ?declaration: name_definition
                | greeting
    
    name_definition: "name:" name
    
    greeting: salutation name
    
    salutation: /[Hh]ello/  
              | /[Gg]oodbye/
    
    name: WORD
       
    %import common.WORD
    %import common.NEWLINE -> _NEWLINE
    %import common.WS_INLINE
    %ignore WS_INLINE
"""

# Error handling - see
# - https://github.com/lark-parser/lark/blob/master/examples/advanced/error_reporting_lalr.py
# - https://lark-parser.readthedocs.io/en/stable/classes.html#unexpectedinput


class GreetingSyntaxError(SyntaxError):

    def __init__(self):
        self.label = "syntax"
    def __str__(self):
        context, line, column = self.args
        return 'context: "%s" at line %s, column %s.\n\n%s' % (self.label, line, column, context)


parser = Lark(greeting_grammar, parser='lalr')


def parse_greetings(text: str) -> Tree:

    try:
        greetings = parser.parse(text)
        return greetings

    except (UnexpectedInput, UnexpectedToken) as u:
        print(f"Exception caught: {type(u)}")
        exception_class = u.match_examples(parser.parse, {
            GreetingSyntaxError: ["HEllo",
                                'Godbye',
                                'GOodbye'
            ]
        }, use_accepts=True)
        if not exception_class:
            print(f"match examples failed, raising {type(u)} exception")
            raise
        raise exception_class(u.get_context(text), u.line, u.column)


def parse_greetings_file(fname: str) -> Tree:
    with open(fname, "r") as file:
        return parse_greetings(file.read())

@dataclass
class Greeting:
    salutation: str
    name: str


@dataclass
class Name:
    name: str


class GreetingTransformer(Transformer):
    """Convert raw parse tree into a list of Greeting objects"""

    def __init__(self):
        self.names: List[str] = []

    def start(self, greetings):
        return greetings

    def name_definition(self, tree):
        name = Name(tree[0])
        self.names.append(name)
        return name
    def greeting(self, greeting_tree):
        salutation, name = greeting_tree
        greeting = Greeting(salutation, name)
        return greeting

    def salutation(self, tree):
        salutation = tree[0].value
        return salutation

    def name(self, tree):
        name = tree[0].value
        return name



if __name__ == "__main__":

    from sys import argv

    if len(argv) != 2:
        print(f"Usage: {argv[0]} <greet file>")
        exit(255)

    fname = argv[1]

    print(f"Parsing greeting file '{fname}' ...")
    try:
        tree = parse_greetings_file(fname)
        print("\nRaw Greeting Tree:")
        print(tree)

        t = GreetingTransformer()
        transformed_tree = t.transform(tree)
        print("\nTransformed Greeting Tree:")
        print(transformed_tree)
        print(f"Names: {t.names}")

    except Exception as e:
        print(e)