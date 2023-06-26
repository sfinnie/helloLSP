import sys

from lsprotocol.types import ClientCapabilities
from lsprotocol.types import CompletionList
from lsprotocol.types import CompletionParams
from lsprotocol.types import InitializeParams
from lsprotocol.types import Position
from lsprotocol.types import TextDocumentIdentifier
from lsprotocol.types import TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS
from lsprotocol.types import DidOpenTextDocumentParams
from lsprotocol.types import TextDocumentItem


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

    test_uri = "file:///path/to/file.txt"
    
    params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri="file:///path/to/file.txt",
            language_id="greet",
            version=1,
            text="Hello Petunia"
        )
    )

    client.text_document_did_open(params=params)

    # Wait for the server to publish its diagnostics
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 0



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