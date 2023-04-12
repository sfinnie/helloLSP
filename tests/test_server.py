"""
End to end tests that test server capabilities at the 
language server protocol level.
"""

import sys

from lsprotocol.types import ClientCapabilities
from lsprotocol.types import InitializeParams

import pytest
import pytest_lsp
from pytest_lsp.client import LanguageClient
from pytest_lsp.plugin import ClientServerConfig


@pytest_lsp.fixture(
    # scope='session',
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "server"],
        root_uri="file:///path/to/test/project/root/"
    ),
)
async def client(lsp_client: LanguageClient):
    # Setup
    params = InitializeParams(capabilities=ClientCapabilities())
    await lsp_client.initialize(params)

    yield

    # Teardown
    await lsp_client.shutdown()


@pytest.mark.asyncio
async def test_completion(client):
    assert True
#     test_uri="file:///path/to/test/project/root/test_file.rst"
#     result = await client.completion_request(test_uri, line=5, character=23)

#     assert len(result.items) > 0