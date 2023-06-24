import sys
import pytest

import pytest_lsp
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient

from lsprotocol.types import TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS
from lsprotocol.types import ClientCapabilities
from lsprotocol.types import InitializeParams

from lsprotocol.types import DefinitionParams

from lsprotocol.types import CompletionParams, Position, TextDocumentIdentifier, CompletionList

from server.server import definition


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "-m", "server.server"]),
)
async def client(lsp_client: LanguageClient):
    # Setup
    params =InitializeParams(capabilities=ClientCapabilities)
    await lsp_client.initialize_session(params)

    yield

    # Teardown
    await lsp_client.shutdown_session()

# -------------------------------------------------------------------
# Completions
# -------------------------------------------------------------------

@pytest.mark.skip(reason="awaiting resolution of pytest-lsp issues")
async def test_completions(client: LanguageClient):
    """Ensure that the server implements completions correctly."""

    results = await client.text_document_completion_async(
        params=CompletionParams(
            position=Position(line=1, character=0),
            text_document=TextDocumentIdentifier(uri="file:///path/to/file.txt"),
        )
    )
    assert results is not None

    if isinstance(results, CompletionList):
        items = results.items
    else:
        items = results

    labels = [item.label for item in items]
    assert labels == ["hello", "world"]


@pytest.mark.skip(reason="awaiting resolution of pytest-lsp issues")
@pytest.mark.asyncio
async def test_completion(client):
    test_uri="file:///path/to/test/project/root/test_file.rst"
    result = await client.completion_request(test_uri, line=5, character=23)

    assert len(result) == 2

# -------------------------------------------------------------------
# Definitions & References
# -------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.skip(reason="awaiting resolution of pytest-lsp issues")
async def test_invalid_reference_returns_None(client: LanguageClient):
    
    #arrange
    params: DefinitionParams

    params.text_document = TextDocumentIdentifier(uri = "./valid.greet")
    params.position = Position(line=3, character=1)

    #act
    rsp = definition(client, DefinitionParams)

    #assert
    assert rsp is None 






# -------------------------------------------------------------------
# Diagnostics (AKA errors & warnings)
# -------------------------------------------------------------------

@pytest.mark.skip(reason="awaiting resolution of pytest-lsp issues")
@pytest.mark.asyncio
async def test_parse_sucessful_on_file_open(client: LanguageClient):
    """Ensure that the server implements diagnostics correctly when a valid file is opened."""

    test_uri = "file:///path/to/file.txt"
    client.notify_did_open(
        uri=test_uri, language="plaintext", contents="Hello Bob"
    )

    # Wait for the server to publish its diagnostics
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 0


@pytest.mark.skip(reason="awaiting resolution of pytest-lsp issues")
@pytest.mark.asyncio
async def test_parse_fail_on_file_open(client):
    """Ensure that the server implements diagnostics correctly when an invalid file is opened."""

    test_uri = "file:///path/to/file.txt"
    client.notify_did_open(
        uri=test_uri, language="plaintext", contents="Hello Bob1"
    )

    # Wait for the server to publish its diagnostics
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 1
    assert client.diagnostics[test_uri][0].message == "Greeting must be either 'Hello <name>' or 'Goodbye <name>'"

@pytest.mark.skip(reason="awaiting resolution of pytest-lsp issues")
@pytest.mark.asyncio
async def test_parse_sucessful_on_file_change(client):
    """Ensure that the server implements diagnostics correctly when a file is changed and the updated contents are valid."""

    # given
    test_uri = "file:///path/to/file.txt"
    client.notify_did_open(
        uri=test_uri, language="plaintext", contents="Hello B0b"
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


@pytest.mark.skip(reason="awaiting resolution of pytest-lsp issues")
@pytest.mark.asyncio
async def test_parse_fails_on_file_change(client):
    """Ensure that the server implements diagnostics correctly when a file is changed and the updated contents are invalid."""

    # given
    test_uri = "file:///path/to/file.txt"
    client.notify_did_open(
        uri=test_uri, language="plaintext", contents="Hello Bob"
    )
    # Get diagnostics from file open before notifying change
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    # when
    client.notify_did_change(
        uri=test_uri, text="Hello B0b"
    )
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 1
    assert client.diagnostics[test_uri][0].message == "Greeting must be either 'Hello <name>' or 'Goodbye <name>'"
