# Hello LSP - an incremental introduction to the Language Server Protocol

***Work in Progress***

The [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) (LSP) provides a way to build editor services for a language that aren't tied to a specific editor or IDE.  [VSCode](https://code.visualstudio.com/api/language-extensions/language-server-extension-guide), [neovim](https://neovim.io/doc/user/lsp.html) and [emacs](https://www.emacswiki.org/emacs/LanguageServerProtocol), for example, all support the LSP at time of writing, meaning a single LSP implementation can be used in all 3 editors.  Actually, that's not quite true.  Whilst the server component of an LSP implementation can be used as-is, each editor has a different way of integrating the LSP server into the editor.  This example focuses on vscode - so the client is vscode specific and written in typescript.  The server is in python [^0].

[^0]: why Python?  Because it illustrates using a different language for client and server, it's a popular language, and there are good libraries to support development and testing.  The client has to be in javascript or typescript - that's a vscode constraint.

## Overview

There are overviews of the LSP on [Microsoft's official site](https://microsoft.github.io/language-server-protocol/), the [community site](https://langserver.org/) and others too.

The [LSP spec](https://microsoft.github.io/language-server-protocol/specifications/specification-current/) summarises it thus:

<a name="lsp-overview"></a>
> The Language Server protocol is used between a tool (the client) and a language smartness provider (the server) to integrate features like auto complete, go to definition, find all references and alike into the tool 

That's good enough for here; there's plenty more at the sites above.  We'll focus below on implementing a working LSP client and server, building it incrementally.

## The Language

If we're to implement a language *server*, we need a *language*.  Real language servers deal with programming languages.  Implementing programming languages is an entire body of theory and practice in itself and that's not the objective here (though, if that's your bag, you could do a lot worse that starting with Bob Nystrom's [Crafting Interpreters](https://craftinginterpreters.com/)).  

Thankfully we don't need anything approaching the complexity of a real programming language to implement a language server: we can use something simpler instead.  *Much* simpler, in fact.  Let's call the language *greet*: it's only purpose is to express simple greetings.  First, a couple of examples:

    Hello bob
    Goodbye Nellie

That's it.  Each phrase consists of just two words: a *salutation* - "hello" or "goodbye" - and a name.  Here's a grammar[^1] for the language:

[^1]: It's common to formally describe the syntax of a programming language with a grammar, often defined in *Backus-Naur Format* (BNF).  See e.g. [wikipedia](https://en.wikipedia.org/wiki/Syntax_(programming_languages) for more information.

<a name="greet-grammar"></a>

```bnf
    greeting    ::= salutation name
    salutation  ::= 'Hello' | 'Goodbye'
    name        ::= [a-zA-Z]+
```

In words, that says:

* A `greeting` comprises a `salutation` followed by a `name`
* A `salutation` is the word `Hello` or the word `Goodbye`
* A `name` is one or more letters, either lower or upper case.  Note there can't be any spaces between the letters: `Nellie` is fine but `Nellie bob` isn't.

We'll write some code to 'implement' the language [a bit later](#language-implementation).  First though, let's look at the structure of the solution.

## Solution Overview

If you know the basics of how LSP works, [skip ahead to the implementation skeleton](#implementation-skeleton).

As per the introduction, the solution comprises 2 parts:

* the *client* integrates with the editor - vscode in this case.  Each editor has its own approach to integrating extensions.  Editors support extensions for many languages - so our extension will be one of several installed in any installation.  The client has to comply with that, so it's job is broadly to:
  * tell the editor what language it supports
  * liaise between the editor and the server
* the *server* provides the smarts on the language (as per the overview quote [above](#lsp-overview))

Though vscode calls these "extensions", I'm going to use "plugin" from here on in.  The reason is that "extension" is also used when referring to filenames (e.g. the `.py` part in `file.py`).  We need to refer to both, so I'll use `plugin` for the things that provide language support, and `extension` specifically when referring to file names.

<a name="protocol-overview"></a>

### Client-Server Interaction

The client and server communicate using the language server protocol itself.  It defines two types of interactions:

* **Notifications**.  For example, the client can send a `textDocument/didOpen` notification to the server to indicate that a file, of the type supported by the server, has been opened.  Notifications are one-way events: there's no expectation of a reply.  In this case, the client is just letting the server know a file has been opened.  There's no formal expectation of what the server does with that knowledge.  Though, in this case, a reasonable outcome would be for the server to read the file in preparation for subsequent requests.
* **Request/response pairs**.  For example, the client can send the  `textDocument/definition` request to the server if the editor user invokes the "go to definition" command (e.g. to jump to the implementation of a function from a site where it's called).  The server is expected to respond, in this case with a `textDocument/definition` response.  (As a side note: both client and server can issue requests - not just the client).  

Interactions are encoded using [JSON-RPC](https://www.jsonrpc.org/).  Here's an example (taken from the [official docs](https://microsoft.github.io/language-server-protocol/overviews/lsp/overview/)):

```json
{
    "jsonrpc": "2.0",
    "id" : 1,
    "method": "textDocument/definition",
    "params": {
        "textDocument": {
            "uri": "file:///p%3A/mseng/VSCode/Playgrounds/cpp/use.cpp"
        },
        "position": {
            "line": 3,
            "character": 12 
        } 
    } 
}
```

It's pretty self-explanatory:

* The `method` - aka the request - is `textDocument/definition`
* The `uri` defines the document the user is editing
* the `position` defines the line and column in the file that the user's cursor was at when they invoked the "go to definition" command.

The position highlights an important point on how the editor and server communicate. It's all founded on the position in a file, where the position comprises line (row) and column.

Here's a typical response (again from the [official docs](https://microsoft.github.io/language-server-protocol/overviews/lsp/overview/)):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "uri": "file:///p%3A/mseng/VSCode/Playgrounds/cpp/provide.cpp",
    "range": {
      "start": {
        "line": 0,
        "character": 4
      },
      "end": {
        "line": 0,
        "character": 11
      }
    }
  }
}
```

Again, fairly explanatory:

* the `id` is used to correlate the response with the request.  The user might, for example, have changed their mind and started typing again, in which case the editor needs to know it can discard the response.
* the `result` contains the response to the request.  It says:
  * The definition of the symbol in the request is contained in the `uri`.  Note it's a different file to the uri in the request.
  * The `start` and `end` define the line & column positions that delimit the definition.  For example, this could be the first and last characters of the name of the function being referenced.  

It's entirely up to the server to decide what constitutes the definition.  Note, again, the use of line and column to define position.

<a name="implementation-skeleton"></a>

## Implementation Skeleton

OK, enough of the talking - let's code.  

### Pre-Requisites

We're using vscode as the editor, so you need to [install it first](https://code.visualstudio.com/download).  You'll also need to install [git](https://git-scm.com/),   [Node.js](https://nodejs.org/) and [Python](https://www.python.org/downloads/).  Then create a new directory to hold the project:

```bash
$ cd /my/projects/dir
$ mkdir helloLSP 
$ cd helloLSP
```

There's a fair bit of boilerplate that needs to be in place before we can really get started on the implementing support for `greet`.  It's a bit fiddly and difficult to get right from first principles.  However, luckily, we don't need to. I used [this example](https://github.com/openlawlibrary/pygls/tree/master/examples/json-vscode-extension) as a template.  There are [many](https://microsoft.github.io/language-server-protocol/implementors/servers/) [examples](https://github.com/openlawlibrary/pygls/tree/master/examples) [available](https://github.com/microsoft/vscode-python-tools-extension-template) and reading some others too is worthwhile to get a sense of what's involved.

To build initially and check it's working:

1. Set up the Server Python environment

    ```bash
    $ python -m venv venv
    $ source venv/scripts/activate
    $ python -m pip install -U pip
    $ python -m pip install pygls
    ```

1. Set up the client nodejs environment

    ```bash
    $ npm install
    $ cd client
    $ npm install
    $ cd ..
    ```

1. Start vscode in the project root dir

    ```bash
    $ code .
    ```

1. Edit [.vscode/settings.json](vscode/settings.json) to ensure the python interpreter path is set correctly:

    ```json
    {
        "python.interpreterPath": "${workspaceFolder}/.venv/Scripts/python"
    }
    ```

1. Run the extension client and server in a separate "development" instance of vscode by typing `ctrl-shift-D`, selecting `Server + Client` in the "Launch" dropdown at the top of the screen, and hitting `F5`.

1. In the development instance of vscode, open the `samples` sub-directory of this project.

1. Open the sample json file.  The editor should show an information message at the bottom of the main window that says "Text Document Did Open".

With that done, the basics are all in place.  Close the development instance for now and go back to the main project instance.  The code at this point is [tagged as v0.1](https://github.com/sfinnie/helloLSP/releases/tag/v0.1) if you want to have a look.

## Anatomy of the Plugin

Despite all the boilerplate, there are 3 primary files that implement the plugin:

* [client/src/extension.ts](client/src/extension.ts) implements the client
* [server/server.py](server/server.py) implements the server.
* [package.json](./package.json) which describes the capabilities that the client and server provide.


## Tidying up the skeleton

***Note:*** if you're eager to get onto actually implementing language support, then [skip ahead](#language-implementation).  This section tidies up the skeleton and gets ready for that.  Some would argue it's just noise, but understanding how things fit together can be interesting.  Or helpful.  Or both.  If it's not your bag, move along.  

With the skeleton in place, we can start making the changes needed to support our `greet` language.   There are a few housekeeping tasks to complete:

1. Change the plugin so it's activated on files with a `.greet` extension (the skeleton is activated for `json` files)
1. Get rid of the extraneous commands supported by the skeleton that we don't need.
1. Rename the relevant classes, methods and names from `json` to `greet`

### Tiny baby steps - setting the language

Let's start with the filrname extension.  There's actually 2 parts to this, because vscode separates language *identity* from the filename *extension*.  That allows a single language to support multiple extensions.  For example: the Java tooling supports both `.jav` and `.java` extensions.

The language and extension(s) are configured in the `package.json` file.  The relevant section in the skeleton reads as follows:

```json
"activationEvents": [
    "onLanguage:json"
  ],
```

We need to make a few changes.  For a start, the skeleton assumes vscode already knows about `json` as a language.  It won't know anything about `greet` though.  So we need to define the language identity, define the file extensions, and let vscode know when to activate our plugin.  Here's what that looks like[^4]

[^4]: It's not strictly necessary to include the `activationEvents` section: vscode infers that from language contributions in recent versions.  There's no downsides to doing so though, and means the extension will work with older versions of vscode.

```json
"contributes": {
    "languages": [
      {
        "id": "greet",
        "aliases": [
          "Greet",
          "greet"
        ],
        "extensions": [
          ".greet"
        ]
      }
    ]
},
"activationEvents": [
    "onLanguage:greet"
  ],
```

It's also referenced in [extension.ts](client/src/extension.ts):

```typescript
function getClientOptions(): LanguageClientOptions {
    return {
        // Register the server for plain text documents
        documentSelector: [
            { scheme: "file", language: "json" },
            { scheme: "untitled", language: "json" },
        ],
    //...
```

We need to change that to:

```typescript
function getClientOptions(): LanguageClientOptions {
    return {
        // Register the server for plain text documents
        documentSelector: [
            { scheme: "file", language: "greet" },
            { scheme: "untitled", language: "greet" },
        ],
    //...
```

With those changed, we can launch the plugin in a development window again (`ctrl-shift-D`, select "Server + Client", hit `F5`).  Open `samples/valid.greet` in the editor and, again, you should see the `Text Document Did Open` message. CLose the development instance.  Change 1 complete.


### Cleaning up 

The skeleton plugin implements multiple commands for illustration.  We don't need them here, so they can be removed.  If you run the plugin in a development instance and type `ctrl-shift-p` then enter "countdown" in the dialogue box, you should see several options like "Count down 10 seconds [Blocking]".  We don't need those. That needs changes in 2 places:

* `package.json`, which declares the commands the plugin supports
* `server.py` which implements them.

Here's an excerpt from each.

```json
//package.json
    "commands": [
      {
        "command": "countDownBlocking",
        "title": "Count down 10 seconds [Blocking]"
      },
      // several more
    ]
```

```python
class JsonLanguageServer(LanguageServer):
    CMD_COUNT_DOWN_BLOCKING = 'countDownBlocking'
    # several more
 
@json_server.command(JsonLanguageServer.CMD_COUNT_DOWN_BLOCKING)
def count_down_10_seconds_blocking(ls, *args):
    """Starts counting down and showing message synchronously.
    It will `block` the main thread, which can be tested by trying to show
    completion items.
    """
    for i in range(COUNT_DOWN_START_IN_SECONDS):
        ls.show_message(f'Counting down... {COUNT_DOWN_START_IN_SECONDS - i}')
        time.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)

```

The link between the two is the `countdownBlocking` literal.  Removing the unnecessary commands requires removing:

1. the "commands" entry in `package.json`
1. The corresponding constant definition in the `JsonLanguageServer` class
1. The python function that implements the class

We'll remove the configuration and code for the following commands:

* countDownBlocking
* CountDownNonBlocking
* showConfigurationAsync
* showConfigurationCallback
* showConfigurationThread

Launching the development instance, typing `ctrl-shift-p` and entering "countdown" now doesn't show up our commands.  Task complete.

## Naming: enough, already, Json

The skeleton is based on suport for `json` files, and that's used throughout [extension.ts](./client/src/extension.ts), [server.py](server/server.py) and [package.json](package.json).


### Package.json

Let's start with `package.json`.  The first chunk of relevance sits right at the top of the file:

```json
{
  "name": "json-extension",
  "description": "Simple json extension example",
  "author": "Open Law Library",
  "repository": "https://github.com/openlawlibrary/pygls",
  "license": "Apache-2.0",
  "version": "0.11.3",
  "publisher": "openlawlibrary",
  //...
```
We can change that as follows:

```json
{
  "name": "greet",
  "description": "Support for the greet salutation example language",
  "author": "sfinnie",
  "repository": "https://github.com/sfinnie/helloLSP",
  "license": "Apache-2.0",
  "version": "0.0.1",
  "publisher": "sfinnie",
```

The next bit is the configuration section.  It currently reads:

```json
    "configuration": {
      "type": "object",
      "title": "Json Server Configuration",
      "properties": {
        "jsonServer.exampleConfiguration": {
          "scope": "resource",
          "type": "string",
          "default": "You can override this message."
        }
      }
    }
```

It's a bit academic, because we don't have any configuration at the moment. It's helpful to see how it fits together though, so let's leave it in but update it:

```json
    "configuration": {
      "type": "object",
      "title": "Greet Server Configuration",
      "properties": {
        "greetServer.exampleConfiguration": {
          "scope": "resource",
          "type": "string",
          "default": "Greet says you can override this message."
        }
      }
    }
```

That's `package.json` done.  Let's do the client next.

### extension.ts

The first section in the client is in the `getClientOptions()` function that we update earlier.  Here's how it looks currently:

```typescript
function getClientOptions(): LanguageClientOptions {
    return {
        // Register the server for 'greet' documents
        documentSelector: [
            { scheme: "file", language: "greet" },
            { scheme: "untitled", language: "greet" },
        ],
        outputChannelName: "[pygls] JsonLanguageServer",
```

It's the last line we want to change, as follows:
```typescript
        outputChannelName: "[pygls] GreetLanguageServer",
```
I've left `[pygls]` in there.  It's completely optional, but it might be useful to know that's what the server is based on.  If nothing else, it's a nice little acknowledgement for the nice folks who put it together and shared it with the world.


That's it for the client - onto the server.

### server.py

The change in the server is the main language server class:

```python
class JsonLanguageServer(LanguageServer):
    CMD_PROGRESS = 'progress'
    #...

json_server = JsonLanguageServer('pygls-json-example', 'v0.1')
```

Unsurprisingly, that becomes:

```python
class GreetLanguageServer(LanguageServer):
    CMD_PROGRESS = 'progress'
    #...

greet_server = GreetLanguageServer('pygls-json-example', 'v0.1')
```

`greet_server` is referenced in several places in the file, so they all need updated.  Same with `GreetLanguageServer`.

There's a couple of functions for validating the contents of a file (`_validate()`, `_validate_json()`).  We're going to update them later, so can leave the `json` references for now.

That's the renaming complete.  Time, at last, to actually start implementing our support for greet.


<a name="language-implementation"></a>

## Implementing Greet Language Support

Hurrah!  Finally time to implement the language support.  But what does that actually mean?  The Language Server Protocol defines several [language features](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#languageFeatures), for example:

* [Goto Declaration](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_declaration)
* [Find References](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references)
* [Completion Items](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion)

We'll start with checking that a `greet` file is consistent with the [grammar](greet-grammar).  We know from [earlier](#protocol-overview) that notifications can be sent from the client to the server and vice-versa.  One of those notifications is `textDocument/didOpen` which is sent when a document, of the type supported by the plugin, is opened. We saw that in the development instance: it displayed the message `Text Document Did Open` when we opened a file with the `.greet` extension.  Here's the source of that in `server.py`:

```python
@greet_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message('Text Document Did Open')
    _validate(ls, params)
```

It's pretty self-explanatory.  The `@greet_server.feature` line is where `pygls` does its magic.  Behind that simple line, `pygls` manages receiving the notification in `json-rpc` format, parsing out the parameters into a `DidOpenTextDocumentParams` object, and calling the `did_open` function.  Aside from showing the message we saw on screen earlier[^5], the function calls `_validate()` to check the file contents [^6]. 

[^5]: Just in case you're in any doubt, change the message to something like 'Text Document Did Open a greet file' and launch a development instance.  Open a `.greet` file, and marvel at the outcome.

[^6]: the underscore is a convention to indicate that `validate()` is a function only intended for use inside `server.py`.  


The skeleton `_validate()` function checks whether the file is valid `json` so we need to change that.  The compiler world tends to talk about *parsing* rather than *validating*.  It's a bit pedantic, but I'm going to stick to that here.  So the functions we'll look at are named `_parse()` not `_validate()`.  

1. Extracting the source file name from the paramers and reading its contents
1. Checking the contents

We'll stick to that.  The first function doesn't change (other than the name):

```python
def _parse(ls: GreetLanguageServer, params: DidOpenTextDocumentParams):
    ls.show_message_log('Validating json...')

    text_doc = ls.workspace.get_document(params.text_document.uri)

    source = text_doc.source
    diagnostics = _parse_greet(source) if source else []

    ls.publish_diagnostics(text_doc.uri, diagnostics)
```

Note the error handling if there's no source document.  `ls.publish_diagnostics()` passes any errors found back to the client for display in the editor.  The meat is in the `_parse_greet()` function.  How do we parse the file?  The grammar tells us the rules for a greeting, but how do we implement it?  The skeleton takes advantage of Python's `json.loads()` function to do the parsing.  Here's the skeleton implementation:

```python
def _parse_greet(source):
    """Validates json file."""
    diagnostics = []

    try:
        json.loads(source)
    except JSONDecodeError as err:
        msg = err.msg
        col = err.colno
        line = err.lineno

        d = Diagnostic(
            range=Range(
                start=Position(line=line - 1, character=col - 1),
                end=Position(line=line - 1, character=col)
            ),
            message=msg,
            source=type(greet_server).__name__
        )

        diagnostics.append(d)

    return diagnostics
```

The majority of the code deals with creating the `Diagnostic` - the data structure that informs the editor where the error lies, and what the problem is.

Python's standard library doesn't have a built-in function for loading `.greet` files.  There's lots of well-established [theory](https://en.wikipedia.org/wiki/Parsing) on parsing, several techniques, and lots of libraries to support it.  That's a bit overkill for our needs.  Our approach is broadly:

1. Read in the file, breaking it up into lines
1. For each line, check if it contains a valid greeting:
    1. Does it start with either "Hello" or "Goodbye"?
    1. If so, is it followed by a name that satisfies the `[a-zA-Z]+` pattern?





# To Do

1. Testing
1. Packaging and deploying
1. Adding more language features: o to definition, suggestions, others
1. Implement a more realistic language, possibly using tree sitter to parse.

