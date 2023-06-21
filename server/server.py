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
import asyncio
import json
import re
import time
import uuid
from json import JSONDecodeError
from typing import List, Optional

# Command and notification names
from lsprotocol.types import (TEXT_DOCUMENT_COMPLETION, TEXT_DOCUMENT_DID_CHANGE,
                               TEXT_DOCUMENT_DID_CLOSE, TEXT_DOCUMENT_DID_OPEN,
                               TEXT_DOCUMENT_REFERENCES,
                               TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL)

# Datatypes passed in commands/responses/notifications
from lsprotocol.types import (CompletionItem, CompletionList, CompletionOptions,
                              CompletionParams, ConfigurationItem,
                              # document didChange/didOpen notifications
                              DidOpenTextDocumentParams, 
                              DidChangeTextDocumentParams,
                              
                              # Returning diagnostics when issues detected with source file
                              Diagnostic,
                              Range, 
                              DidCloseTextDocumentParams,

                              MessageType, Position,
                              Registration, RegistrationParams,
                              SemanticTokens, SemanticTokensLegend, SemanticTokensParams,
                              Unregistration, UnregistrationParams,
                              WorkDoneProgressBegin, WorkDoneProgressEnd,
                              WorkDoneProgressReport,
                              WorkspaceConfigurationParams)

# textDocument/definition: return the location where a symbol is defined
from lsprotocol.types import ( TEXT_DOCUMENT_DEFINITION, # command alias
                               DefinitionParams,         # command params
                               LocationLink)             # response

from pygls.server import LanguageServer

COUNT_DOWN_START_IN_SECONDS = 10
COUNT_DOWN_SLEEP_IN_SECONDS = 1


class GreetLanguageServer(LanguageServer):
    CMD_PROGRESS = 'progress'
    CMD_REGISTER_COMPLETIONS = 'registerCompletions'
    CMD_UNREGISTER_COMPLETIONS = 'unregisterCompletions'

    CONFIGURATION_SECTION = 'jsonServer'

    def __init__(self, *args):
        super().__init__(*args)


greet_server = GreetLanguageServer('pygls-json-example', 'v0.1')


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
                    source=type(greet_server).__name__
                )
            diagnostics.append(d)

 
    return diagnostics


@greet_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message('Text Document Did Open')
    _parse(ls, params)


@greet_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _parse(ls, params)


@greet_server.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: GreetLanguageServer, params: DidCloseTextDocumentParams):
    """Text document did close notification."""
    server.show_message('Text Document Did Close')


@greet_server.feature(TEXT_DOCUMENT_REFERENCES)
def references(ls: GreetLanguageServer):
    """returns a list of 0 or more locations that reference the specified token"""
    pass


@greet_server.feature(TEXT_DOCUMENT_DEFINITION)
def definition(ls: GreetLanguageServer,  params: DefinitionParams) -> LocationLink | None:
    """returns the location where the specified token is defined if found,
       None otherwise
    """
    origin_range = Range(start=params.position,
                         end=Position(line=params.position.line, 
                                      character=params.position.character+1))
    
    definition_range = Range(start=Position(line=0, character=6),
                             end=Position(line=0, character=11))
    
    loc = LocationLink(target_uri=params.text_document.uri,
                       origin_selection_range=origin_range,
                       target_range=definition_range,
                       target_selection_range=definition_range)
    return loc


# ---------------------------------------------------------------------------
# Features from original skeleton
# ---------------------------------------------------------------------------

@greet_server.feature(TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: CompletionParams):
    return [
        CompletionItem(label="hello"),
        CompletionItem(label="world"),
    ]


@greet_server.feature(
    TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
    SemanticTokensLegend(
        token_types = ["operator"],
        token_modifiers = []
    )
)
def semantic_tokens(ls: GreetLanguageServer, params: SemanticTokensParams):
    """See https://microsoft.github.io/language-server-protocol/specification#textDocument_semanticTokens
    for details on how semantic tokens are encoded."""

    TOKENS = re.compile('".*"(?=:)')

    uri = params.text_document.uri
    doc = ls.workspace.get_document(uri)

    last_line = 0
    last_start = 0

    data = []

    for lineno, line in enumerate(doc.lines):
        last_start = 0

        for match in TOKENS.finditer(line):
            start, end = match.span()
            data += [
                (lineno - last_line),
                (start - last_start),
                (end - start),
                0,
                0
            ]

            last_line = lineno
            last_start = start

    return SemanticTokens(data=data)



@greet_server.command(GreetLanguageServer.CMD_PROGRESS)
async def progress(ls: GreetLanguageServer, *args):
    """Create and start the progress on the client."""
    token = str(uuid.uuid4())
    # Create
    await ls.progress.create_async(token)
    # Begin
    ls.progress.begin(token, WorkDoneProgressBegin(title='Indexing', percentage=0))
    # Report
    for i in range(1, 10):
        ls.progress.report(
            token,
            WorkDoneProgressReport(message=f'{i * 10}%', percentage= i * 10),
        )
        await asyncio.sleep(2)
    # End
    ls.progress.end(token, WorkDoneProgressEnd(message='Finished'))


@greet_server.command(GreetLanguageServer.CMD_REGISTER_COMPLETIONS)
async def register_completions(ls: GreetLanguageServer, *args):
    """Register completions method on the client."""
    params = RegistrationParams(registrations=[
                Registration(
                    id=str(uuid.uuid4()),
                    method=TEXT_DOCUMENT_COMPLETION,
                    register_options={"triggerCharacters": "[':']"})
             ])
    response = await ls.register_capability_async(params)
    if response is None:
        ls.show_message('Successfully registered completions method')
    else:
        ls.show_message('Error happened during completions registration.',
                        MessageType.Error)




@greet_server.command(GreetLanguageServer.CMD_UNREGISTER_COMPLETIONS)
async def unregister_completions(ls: GreetLanguageServer, *args):
    """Unregister completions method on the client."""
    params = UnregistrationParams(unregisterations=[
        Unregistration(id=str(uuid.uuid4()), method=TEXT_DOCUMENT_COMPLETION)
    ])
    response = await ls.unregister_capability_async(params)
    if response is None:
        ls.show_message('Successfully unregistered completions method')
    else:
        ls.show_message('Error happened during completions unregistration.',
                        MessageType.Error)
