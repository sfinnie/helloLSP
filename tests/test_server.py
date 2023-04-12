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


# @pytest.mark.asyncio
# async def test_completion(client):
#     test_uri="file:///path/to/test/project/root/test_file.rst"
#     result = await client.completion_request(test_uri, line=5, character=23)

#     assert len(result) == 2


@pytest.mark.asyncio
async def test_parse_sucessful_on_file_open(client):
    """Ensure that the server implements diagnostics correctly when a valid file is opened."""

    test_uri = "file:///path/to/file.txt"
    client.notify_did_open(
        uri=test_uri, language="plaintext", contents="Hello Bob"
    )

    # Wait for the server to publish its diagnostics
    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    assert test_uri in client.diagnostics
    assert len(client.diagnostics[test_uri]) == 0
    # assert client.diagnostics[test_uri][0].message == "There is an error here."