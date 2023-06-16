import sys
import pytest
import pytest_lsp
from pytest_lsp import ClientServerConfig

from lsprotocol.types import TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS

@pytest_lsp.fixture(
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "server"]
        # root_uri="file:///path/to/test/project/root/"
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
