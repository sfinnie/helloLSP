############################################################################
# Original work Copyright(c) Open Law Library. All rights reserved.        #
# See ThirdPartyNotices.txt in the project root for additional notices.    #
#                                                                          #
# All modifications Copyright(c) Scott Finnie.  All rights reserved.       #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License")           #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http: // www.apache.org/licenses/LICENSE-2.0                         #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################

# textDocument/completion command
from lsprotocol.types import (TEXT_DOCUMENT_COMPLETION, 
                              CompletionParams, 
                              CompletionItem)

# validating file content on textDocument/didOpen & textDocument/didChange
from lsprotocol.types import (TEXT_DOCUMENT_DID_OPEN,
                              TEXT_DOCUMENT_DID_CHANGE,
                              DidOpenTextDocumentParams,
                              DidChangeTextDocumentParams,
                              Diagnostic,
                              Range,
                              Position)

from pygls.server import LanguageServer

import re
from typing import List

import logging
logging.basicConfig(filename="greetls.log", level=logging.DEBUG, filemode="w")


class GreetLanguageServer(LanguageServer):
    """entry point for the `greet` language server"""

    CONFIGURATION_SECTION = 'greetServer'

    def __init__(self, *args):
        super().__init__(*args)
        self.show_message_log("Greet Language Server started")

server = GreetLanguageServer("greet-language-server", "v0.1")

# -------------------------------------------------------------
# Language feature implementations
# -------------------------------------------------------------

def _parse(ls: GreetLanguageServer, params: DidOpenTextDocumentParams | DidChangeTextDocumentParams):
    ls.show_message_log('Parsing greeting...')

    text_doc = ls.workspace.get_document(params.text_document.uri)

    source = text_doc.source
    diagnostics = _parse_greet(source) if source else []

    ls.publish_diagnostics(text_doc.uri, diagnostics)


def _parse_greet(source: str) -> List[Diagnostic]:
    """Parses a greeting file.  Generates diagnostic messages for any problems found"""
    diagnostics: List[Diagnostic] = []

    grammar = re.compile(r'^(Hello|Goodbye)\s+([a-zA-Z]+)\s*$')

    lines = [line.rstrip() for line in source.splitlines()]
    for line_num, line_contents in enumerate(lines):
        if len(line_contents) == 0:
            # Don't treat blank lines as an error
            continue
        
        match = re.match(grammar, line_contents)
        if match is None:
            d = Diagnostic(
                    range=Range(
                        start=Position(line=line_num, character=0),
                        end=Position(line=line_num, character=len(line_contents))
                    ),
                    message="Greeting must be either 'Hello <name>' or 'Goodbye <name>'",
                    source=type(server).__name__
                )
            diagnostics.append(d)
 
    return diagnostics

@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message('Text Document Did Open')
    _parse(ls, params)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _parse(ls, params)


@server.feature(TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: CompletionParams):
    return [
        CompletionItem(label="hello"),
        CompletionItem(label="world"),
    ]
