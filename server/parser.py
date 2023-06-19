from lark import Lark, UnexpectedInput

grammar = r"""
start : statement+

statement : name_decl | greeting

name_decl : "name:" NAME

greeting : salutation NAME

salutation : HELLO | GOODBYE

NAME: LETTER+
HELLO: "Hello"
GOODBYE: "Goodbye"

%import common.LETTER
%import common.WS
%ignore WS
"""

_parser = Lark(grammar, start="start")


class GreetSyntaxError(SyntaxError):
    def __str__(self):
        context, line, column = self.args
        return f"{self.label} at line {line}, column {column}"
    
class GreetMalformedName(GreetSyntaxError):
    label = "Malformed name declaration"

class GreetMalformedGreeting(GreetSyntaxError):
    label = "Malformed greeting"


def parse(input: str):
    try:
        _parser.parse(input)
    except UnexpectedInput as ue:
        exc_class = ue.match_examples(_parser.parse, {
            GreetMalformedName: ["name ",
                                 "nam:",
                                 "nme:"],
            GreetMalformedGreeting: ["hello",
                                     "goodbye"]
        }, use_accepts=True)

        if not exc_class:
            raise
        raise exc_class(ue.get_context(input), ue.line, ue.column)



if __name__ == "__main__":

    good_examples = ["name: Bobby", "Hello Esmerelda"]
    for ex in good_examples:
        res = parse(ex)
        print(f"'{ex}' parsed successfully")


    bad_examples = ["name Bobby", "hello Esmerelda"]
    for ex in bad_examples:
        try:
            parse(ex)
        except GreetMalformedName as mn:
            # print(f"line: {e.line}, col: {e.column}, message:\n{e.get_context(msg)}")
            print(mn)
        except GreetMalformedGreeting as mg:
            print(mg)
    

    big_example = """
    name: Bobby
    name: Esmerelda
    
    Hello Bobby
    Goodbye Esmerelda
    """
    parse(big_example)
    print("big example parsed successfully")


