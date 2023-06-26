import sys

from lsprotocol.types import ClientCapabilities
from lsprotocol.types import CompletionList
from lsprotocol.types import CompletionParams
from lsprotocol.types import InitializeParams
from lsprotocol.types import Position
from lsprotocol.types import TextDocumentIdentifier
from lsprotocol.types import TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS
from lsprotocol.types import DidOpenTextDocumentParams
from lsprotocol.types import DidChangeTextDocumentParams
from lsprotocol.types import TextDocumentItem
from lsprotocol.types import VersionedTextDocumentIdentifier
from lsprotocol.types import TextDocumentContentChangeEvent_Type1
from lsprotocol.types import TextDocumentContentChangeEvent_Type2
from lsprotocol.types import Range
from lsprotocol.types import Position



import pytest_lsp
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient

import pytest
import asyncio

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "-m", "server"]),
)
async def client(lsp_client: LanguageClient):
    # Setup
    params = InitializeParams(capabilities=ClientCapabilities())
    await lsp_client.initialize_session(params)

    yield

    # Teardown
    await lsp_client.shutdown_session()


# =============================================================================
# Integration tests i.e. using test language client
# =============================================================================

# -------------------------------------------------------------------
# Diagnostics (AKA errors & warnings)
# -------------------------------------------------------------------

async def test_parse_sucessful_on_file_open(client: LanguageClient):
    """Ensure that the server implements diagnostics correctly when a valid file is opened."""

    # given
    test_uri = "file:///path/to/file.txt"

    params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri="file:///path/to/file.txt",
            language_id="greet",
            version=1,
            text="Hello Petunia"
        )
    )

    # when
    client.text_document_did_open(params=params)

    # Wait for the server to publish its diagnostics
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    # then
    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 0


async def test_parse_fail_on_file_open(client: LanguageClient):
    """Ensure that the server implements diagnostics correctly when an invalid file is opened."""

    #given
    test_uri = "file:///path/to/file.txt"

    params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri="file:///path/to/file.txt",
            language_id="greet",
            version=1,
            text="Hello Petunia123"
        )
    )

    # when
    client.text_document_did_open(params=params)
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    # then
    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 1
    assert client.diagnostics[test_uri][0].message == "Greeting must be either 'Hello <name>' or 'Goodbye <name>'"


async def test_parse_sucessful_on_file_change(client: LanguageClient):
    """Ensure that the server implements diagnostics correctly when a file is changed and the updated contents are valid."""

    # given
    test_uri = "file:///path/to/file.txt"
    test_content = "Hello Petunia"

    open_params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri=test_uri,
            language_id="greet",
            version=1,
            text="test_content"
        )
    )

    changes = TextDocumentContentChangeEvent_Type1(
        range=Range(Position(0,0), Position(0, len(test_content))),
        text=test_content
    )

    change_params = DidChangeTextDocumentParams(
        content_changes=[changes],
        text_document=VersionedTextDocumentIdentifier(
            uri=test_uri,
            version=1,
        )
    )


    # when - note need to notify doc open before change
    client.text_document_did_open(params=open_params)
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    client.text_document_did_change(params=change_params)
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    # then
    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 0


async def test_parse_unsucessful_on_file_change(client: LanguageClient):
    """Ensure that the server implements diagnostics correctly when a file is changed and the updated contents are invalid."""

    # given
    test_uri = "file:///path/to/file.txt"
    test_content = "Hello Petunia"

    open_params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri=test_uri,
            language_id="greet",
            version=1,
            text="test_content"
        )
    )

    test_content = "Hello Petunia42"
    changes = TextDocumentContentChangeEvent_Type1(
        range=Range(Position(0,0), Position(0, len(test_content))),
        text=test_content
    )

    change_params = DidChangeTextDocumentParams(
        content_changes=[changes],
        text_document=VersionedTextDocumentIdentifier(
            uri=test_uri,
            version=1,
        )
    )


    # when - note need to notify doc open before change
    client.text_document_did_open(params=open_params)
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    client.text_document_did_change(params=change_params)
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    # then
    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 1
    assert client.diagnostics[test_uri][0].message == "Greeting must be either 'Hello <name>' or 'Goodbye <name>'"


# -------------------------------------------------------------------
# Completions
# -------------------------------------------------------------------

# @pytest.mark.asyncio
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