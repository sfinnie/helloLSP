import pytest
from server import server

@pytest.mark.parametrize("greeting, expected", [("Hello Thelma", []), ("Goodbye Louise", [])])
def test_valid_greeting_accepted(greeting, expected):

    greeting = "Hello Thelma"
    result = server._parse_greet(greeting)
    
    assert result == expected