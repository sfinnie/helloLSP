
from dataclasses import dataclass
from enum import Enum
from typing import List

from lsprotocol.types import (Diagnostic,
                              Position,
                              Range)
import re


class TokenType(Enum):
    "Enum of the different token types that can be found in a .greet file."
    NAME_KEYWORD = "name:"
    HELLO = "Hello"
    GOODBYE = "Goodbye"
    NAME = "[a-zA-Z]+"
    UNRECOGNISED = "S+" # any non-whitespace


@dataclass
class Token:
    start_col: int
    end_col: int
    token_type: TokenType
    token_value: str

@dataclass
class Statement:
    "Abstract base class for statement"
    pass

@dataclass
class NameDefinition(Statement):
    "A name declaration statement, e.g. 'name: Francesca'"
    keyword: Token
    name: Token

@dataclass
class Greeting(Statement):
    "A greeting, e.g. 'Hello Daljit'"
    salutation: Token
    name: Token

@dataclass
class UnrecognisedStatement(Statement):
    "a way to report unrecognised statements"
    contents: List[Token]


def _scan(source: str) -> List[Token]:
    "scan the supplied source, splitting it into a list of tokens"
    return []


def _parse(tokens: List[Token]) -> List[NameDefinition | Greeting]:
    """parse a list of tokens into a list of valid statements - name definitions or greetings - 
       and any errors found
    """
    return []


def parse_definition(line: str) -> NameDefinition | None:

    match = re.match(TokenType.NAME_KEYWORD.value, line) 
    if match is None:
        return None
    

def parse(source: str) -> List[Diagnostic]:
    
    diagnostics: List[Diagnostic] = []

    greeting = re.compile(r'^(Hello|Goodbye)\s+([a-zA-Z]+)\s*$')

    lines = [line.rstrip() for line in source.splitlines()]
    for line_num, line_contents in enumerate(lines):
        if len(line_contents) == 0:
            # Don't treat blank lines as an error
            continue
        
        tokens = _scan(line_contents)
        statements = _parse(tokens)

        unrecognised_tokens = [t for t in tokens if t.token_type == TokenType.UNRECOGNISED]
        unrecognised_statements = [s for s in statements if type(s) == UnrecognisedStatement]


        match = re.match(greeting, line_contents)
        if match is None:
            d = Diagnostic(
                    range=Range(
                        start=Position(line=line_num, character=0),
                        end=Position(line=line_num, character=len(line_contents))
                    ),
                    message="Greeting must be either 'Hello <name>' or 'Goodbye <name>'",
                    source=type(greet_server).__name__
                )
            diagnostics.append(d)

 
    return diagnostics
