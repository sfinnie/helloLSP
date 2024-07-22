# Testing

We're going to use [pytest](https://pytest.org/) for testing, so let's get that installed:

```{code-block} bash
python3 -m pip install pytest
```


## Testing the Parser

Let's start with testing the parser itself, before we look at the server.  There are a few files to set up:

```{code-block} bash
:linenos:
touch conftest.py
mkdir tests
touch tests/test_parser.py
```

Create the outline of the first test in `tests/test_parser.py`:

```{code-block} python
:linenos:
import pytest
from server import server

def test_valid_greeting_accepted():
    
    assert True # stub for now
```

`conftest.py` lets `pytest` know this is the project root.  It's needed so that `pytest` can resolve the `from server import server` statement in `test_parser.py` above.

Before we go any further, let's make sure it's working (we'll ignore the tests that come with the skeleton - they're out of sync with our implementation, and test things differently to what we're going to cover):

```{code-block} bash
:linenos:
pytest --ignore=server/tests

============== test session starts ==============
platform linux -- Python 3.10.6, pytest-7.2.1, pluggy-1.0.0
rootdir: /home/sfinnie/projects/helloLSP
plugins: typeguard-2.13.3
collected 1 item

tests/test_parser.py . [100%] 

============== 1 passed in 0.03s ============== 
```

### Positive Tests

The parser is pretty simple but there's that regular expression.  We really want to make sure it's accepting what we want, and rejecting what we don't.  Here's the first test:

```{code-block} bash
:linenos:
import pytest
from server import server


def test_valid_greeting_accepted():

    greeting = "Hello Thelma"
    result = server._parse_greet(greeting)
    
    assert result == []
```

`_parse_greet()` returns a list of `Diagnostic` entries, where each entry denotes an error.  If the list is empty then there are no errors.  We also need to check for a valid greeting that uses "Goodbye" as the salutation.  Repeating the test is a bit wordy, but fortunately Pytest lets us [parameterise the test](https://docs.pytest.org/en/6.2.x/parametrize.html):

```{code-block} bash
:linenos:
import pytest
from server import server

@pytest.mark.parametrize("greeting", [("Hello Thelma"), ("Goodbye Louise")])
def test_valid_greeting_accepted(greeting):

    result = server._parse_greet(greeting)
    
    assert result == []
```

We're now passing 2 test cases into the same function: "Hello Thelma" and "Goodbye Louise".  In both cases, we expect the answer to be an empty list.

Let's run the tests:

```{code-block} bash
:linenos:
pytest --ignore=server/tests
============== test session starts ==============
platform linux -- Python 3.10.6, pytest-7.2.1, pluggy-1.0.0
rootdir: /home/sfinnie/projects/helloLSP
plugins: typeguard-2.13.3
collected 2 items

tests/test_parser.py .. [100%] 

============== 2 passed in 0.47s ================= 
```

All good.  Note it says 2 tests passed: that confirms both test cases are being executed.

### Negative Tests

We need to check the parser correctly identifies errors in invalid greetings.  After all, that's a big part of the value we want the server to provide: telling us where we've gone wrong.  Here's a first attempt:

```{code-block} python
:linenos:
def test_invalid_greeting_rejected():

    greeting = "Hell Thelma" # should be Hello, not Hell
    result = server._parse_greet(greeting)
    
    assert result != []
```

That's fine, but it doesn't check that the Diagnostic is correct.  Let's do that:

```{code-block} python
:linenos:
@pytest.mark.parametrize("greeting", [("Wotcha Thelma"), ("Goodbye L0u1se"), ("Goodbye Louise again")])
def test_invalid_greeting_rejected(greeting):

    # when
    result = server._parse_greet(greeting)

    # then
    assert len(result) == 1

    diagnostic: Diagnostic = result[0]
    assert diagnostic.message == "Greeting must be either 'Hello <name>' or 'Goodbye <name>'"

    start: Position = diagnostic.range.start
    end: Position = diagnostic.range.end
    
    assert start.line == 0
    assert start.character == 0
    assert end.line == 0
    assert end.character == len(greeting)
```

(debate-test-error-message)=

There's a bit of a question about whether we should test the error message.  The test is brittle, in that if we want to change the message, it means changing the text in two places.  Arguably a better answer would be to have the message in a separate structure that both the parser function and test referred to.  Against that, it's a bit less readable.  So, for now, we'll leave as is.  

The test has also been parameterised to cover some obvious failures.  Are they enough?  That depends.  We could get smarter, for example using [Hypothesis](https://hypothesis.readthedocs.io/en/latest/) to generate test input rather than relying on 3 specific test cases.  For now, though, the cases we have give sufficient confidence for the purpose here: we're exploring building a language server, not best practice in test coverage.

## Testing the Server

The parser is the core of the implementation so far.  `pygls` provides most of the server implementation, handling communication with the client including marshalling and interpreting the `json-rpc` messages.  There's little value in re-testing `pygls` here: it already has a solid set of tests.  

However: it *is* worth testing that we've wired up the parser correctly. We saw above that we need the parser to be called on both `textDocument/didOpen` and `textDocument/didChange`.  `pygls` can't ensure that for us.  So there's value in running some tests that ensure the full language server responds as expected in terms of `json-rpc` messages sent and received.

```{note}
I've deliberately avoided calling these "unit" or "integration" tests.  That's a holy war that doesn't want getting into here.
```

If we're to test the server, there are a few pre-requisites we need to resolve:

1. How do we start the server, and know it's started?
1. How do we send it messages, and receive the responses?

We could write this from first principles, constructing `json-rpc` messages directly.  That would be a lot of work though.  It's also unnecessary.  The Language Server Protocol is symmetrical; so both client and server can send commands, receive responses and generate notifications.  That means we can reuse the protocol implementation in `pygls`.  It essentially means using an instance of the `pygls` server as a test client.  `pygls` does this itself for its own tests.  

However, there's also [lsp-devtools](https://github.com/alcarney/lsp-devtools).  It provides [pytest-lsp](https://pypi.org/project/pytest-lsp/), a package that makes things a bit more convenient.  See [this discussion thread](https://github.com/openlawlibrary/pygls/discussions/320) for some background.

### Setup 

First, we need to install `pytest-lsp`:

```{code-block} bash
python3 -m pip install pytest-lsp
```

Let's also get rid of the tests in the original skeleton; we're not using them, and they cause an error unless pytest is run with `--ignore=server/tests`.  

```{code-block} bash
rm -rf server/tests
```

### Parsing a valid file on opening

Now we can create some end-to-end tests in `tests/test_server.py`.  Here's the setup and first test:

```{code-block} python
:linenos:
import sys
import pytest
import pytest_lsp
from pytest_lsp import ClientServerConfig

from lsprotocol.types import TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS

@pytest_lsp.fixture(
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "server"],
        root_uri="file:///path/to/test/project/root/"
    ),
)
async def client():
    pass


@pytest.mark.asyncio
async def test_parse_sucessful_on_file_open(client):
    """Ensure that the server implements diagnostics correctly when a valid file is opened."""

    test_uri = "file:///path/to/file.txt"
    client.notify_did_open(
        uri=test_uri, language="greet", contents="Hello Bob"
    )

    # Wait for the server to publish its diagnostics
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 0
```

The `@pytest_lsp.fixture` annotation takes care of setting up the client, starting the server, and establishing communications between them.  Note that the `root_uri` paramter is set to a sample value, but that doesn't matter - the server doesn't actually read the contents of the file from disk.  That's a deliberate design feature of LSP: the client passes the actual content to the server using the protocol itself.  That's because the client "owns" the file being edited.  Were the server to read it independently, it's possible the client and server would have different views of the file's contents due to e.g. file system caching.  So the client passes the actual file contents to the server in the `contents` parameter, as can be seen in the test:

```{code-block} python
:linenos:
:lineno-start: 24
        uri=test_uri, language="greet", contents="Hello Bob"
```

`Hello Bob` is a valid greeting, so we expect there to be no diagnostics returned.  The test assertions check that.

### Parsing an invalid file on opening

Now let's ensure we do get diagnostics published if the file contents are invalid.  Here's the new test:

```{code-block} python
:linenos:
@pytest.mark.asyncio
async def test_parse_fail_on_file_open(client):
    """Ensure that the server implements diagnostics correctly when an invalid file is opened."""

    test_uri = "file:///path/to/file.txt"
    client.notify_did_open(
        uri=test_uri, language="greet", contents="Hello Bob1"
    )

    # Wait for the server to publish its diagnostics
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 1
    assert client.diagnostics[test_uri][0].message == "Greeting must be either 'Hello <name>' or 'Goodbye <name>'"
```

It's largely as before.  The `contents` param is now set to an invalid greeting (`Hello Bob1` is invalid because numbers aren't allowed in names).  We now expect there to be a diagnostic published, so the length of the diagnostics array is 1.  The same [debate](#debate-test-error-message) exists here on checking the actual text of the message.  Again I've chose to replicate the text for simplicity of reading.

### Ensuring file is parsed when changed

Remember that we want to parse the file when changed as well as when opened.  That means another pair of tests, checking for successful & unsuccessful parsing of a changed file.  Here's the successful one:

```{code-block} python
:linenos:
@pytest.mark.asyncio
async def test_parse_sucessful_on_file_change(client):
    """Ensure that the server implements diagnostics correctly when a file is changed and the updated contents are valid."""

    # given
    test_uri = "file:///path/to/file.txt"
    client.notify_did_open(
        uri=test_uri, language="greet", contents="Hello B0b"
    )
    # Get diagnostics from file open before notifying change
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    # when
    client.notify_did_change(
        uri=test_uri, text="Hello Bob"
    )
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    # then
    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 0
```

The LSP says a file must be notified as open before it can be changed, hence the need for `notify_did_open()` before calling `notify_did_change()`.  We await diagnostics from `notify_did_open()` before invoking `notify_did_change()`.  That clears diagnostics on the server from opening (note the contents on opening are set to an invalid greeting before correcting in the change).

Here's the final test: ensuring the correct diagnostic is published when a greeting is changed from valid to invalid:

```{code-block} python
:linenos:
@pytest.mark.asyncio
async def test_parse_fails_on_file_change(client):
    """Ensure that the server implements diagnostics correctly when a file is changed and the updated contents are invalid."""

    # given
    test_uri = "file:///path/to/file.txt"
    client.notify_did_open(
        uri=test_uri, language="greet", contents="Hello Bob"
    )
    # Get diagnostics from file open before notifying change
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    # when
    client.notify_did_change(
        uri=test_uri, text="Hello B0b"
    )
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    # then
    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 1
    assert client.diagnostics[test_uri][0].message == "Greeting must be either 'Hello <name>' or 'Goodbye <name>'"
```

## Wrapping up

We now have some end-to-end tests that check parsing works correctly, both on initial open and on change.  We're not checking all the permutations of parsing because that's covered in the parser tests we created first.

The code at this point is tagged as [v0.3](https://github.com/sfinnie/helloLSP/releases/tag/v0.3).