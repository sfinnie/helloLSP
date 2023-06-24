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

from lsprotocol.types import TEXT_DOCUMENT_COMPLETION
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionParams
from pygls.server import LanguageServer

import logging
logging.basicConfig(filename="pygls.log", level=logging.DEBUG, filemode="w")


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


@server.feature(TEXT_DOCUMENT_COMPLETION)
def completion(ls: LanguageServer, params: CompletionParams):
    return [
        CompletionItem(label="hello"),
        CompletionItem(label="world"),
    ]


if __name__ == "__main__":
    server.start_io()