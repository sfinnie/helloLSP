import pytest
from server import server
from lsprotocol.types import Diagnostic, Range, Position

@pytest.mark.parametrize("greeting", [("Hello Thelma"), ("Goodbye Louise")])
def test_valid_greeting_accepted(greeting):

    result = server._parse_greet(greeting)
    
    assert result == []


@pytest.mark.parametrize("greeting", [("Wotcha Thelma"), ("Goodbye L0u1se"), ("Goodbye Louise again")])
def test_invalid_greeting_rejected(greeting):

    result = server._parse_greet(greeting)

    assert len(result) == 1

    diagnostic: Diagnostic = result[0]
    assert diagnostic.message == "Greeting must be either 'Hello <name>' or 'Goodbye <name>'"

    start: Position = diagnostic.range.start
    end: Position = diagnostic.range.end
    
    assert start.line == 0
    assert start.character == 0
    assert end.line == 0
    assert end.character == len(greeting)
    