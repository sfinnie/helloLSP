import sys

from lsprotocol.types import ClientCapabilities
from lsprotocol.types import InitializeParams

import pytest_lsp
from pytest_lsp.client import LanguageClient
from pytest_lsp.plugin import ClientServerConfig


@pytest_lsp.fixture(
    config=ClientServerConfig(server_command=[sys.executable, "toy_server.py"]),
)
async def client(lsp_client: LanguageClient):
    # Setup
    params = InitializeParams(capabilities=ClientCapabilities())
    await lsp_client.initialize(params)

    yield

    # Teardown
    await lsp_client.shutdown()


async def test_completions(client: LanguageClient):
    """Ensure that the server implements completions correctly."""

    results = await client.completion_request(
        uri="file:///path/to/file.txt", line=1, character=0
    )

    labels = [item.label for item in results]
    assert labels == ["hello", "world"]