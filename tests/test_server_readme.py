import sys
import pytest
import pytest_lsp
from pytest_lsp import ClientServerConfig

import logging
logging.basicConfig(filename='app.log', 
                    filemode='w', 
                    format='%(name)s - %(levelname)s - %(message)s', 
                    level=logging.DEBUG)

@pytest_lsp.fixture(
    # scope='session',
    config=ClientServerConfig(
        server_command=[sys.executable, "toy_server.py"],
        root_uri="file:///path/to/test/project/root/"
    ),
)
async def client():
    pass


@pytest.mark.asyncio
async def test_completion(client):
    test_uri="file:///path/to/test/project/root/test_file.rst"
    result = await client.completion_request(test_uri, line=5, character=23)

    assert len(result) == 2