# Hello LSP - an incremental introduction to the Language Server Protocol

***Work in Progress***

The [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) (LSP) provides a way to build editor services for a language that aren't tied to a specific editor or IDE.  [VSCode](https://code.visualstudio.com/api/language-extensions/language-server-extension-guide), [neovim](https://neovim.io/doc/user/lsp.html) and [emacs](https://www.emacswiki.org/emacs/LanguageServerProtocol), for example, all support the LSP at time of writing, meaning a single LSP implementation can be used in all 3 editors.  Actually, that's not quite true.  Whilst the server component of an LSP implementation can be used as-is, each editor has a different way of integrating the LSP server into the editor.  This example focuses on vscode - so the client is vscode specific and written in typescript.  The server is in python [^0].

[^0]: why?  Because it illustrates using a different language for client and server, it's a popular language, and there are good libraries to support development and testing.

## Overview

There are overviews of the LSP on [Microsoft's official site](https://microsoft.github.io/language-server-protocol/), the [community site](https://langserver.org/) and others too.

The [LSP spec](https://microsoft.github.io/language-server-protocol/specifications/specification-current/) summarises it thus:

<a name="lsp-overview"></a>
> The Language Server protocol is used between a tool (the client) and a language smartness provider (the server) to integrate features like auto complete, go to definition, find all references and alike into the tool 

That's good enough for here; there's plenty more at the sites above.  We'll focus below on implementing a working LSP client and server, building it incrementally.

## The Language

If we're to implement a language *server*, we need a *language*.  Real language servers deal with programming languages.  Implementing programming languages is an entire body of theory and practice in itself and that's not the objective here (though, if that's your bag, you could do a lot worse that starting with Bob Nystrom's [Crafting Interpreters](https://craftinginterpreters.com/)).  

Thankfully we don't need anythong approaching the complexity of a real programming language to implement a language server: we can use something simpler instead.  *Much* simpler, in fact.  Let's call the language *greet*: it's only purpose is to express simple greetings.  First, a couple of examples:

    Hello bob
    Goodbye Nellie

That's it.  Each phrase consists of just two words: a *salutation* - "hello" or "goodbye" - and a name.  Here's a grammar[^1] for the language:

[^1]: It's common to formally describe the syntax of a programming language with a grammar, often defined in *Backus-Naur Format* (BNF).  See e.g. [wikipedia](https://en.wikipedia.org/wiki/Syntax_(programming_languages) for more information.

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

If you know the basics of how LSP works, [skip ahead to the implementation overview](#implementation-overview).

As per the introduction, the solution comprises 2 parts:

* the *client* integrates with the editor - VSCode in this case.  Each editor has its own approach to integrating extensions.  Editors support extensions for many languages - so our extension will be one of several installed in any installation.  The client has to comply with that, so it's job is broadly to:
  * tell the editor what language it supports
  * liaise between the editor and the server
* the *server* provides the smarts on the language (as per the overview quote [above](#lsp-overview))

### Client-Server Interaction

The client and server communicate using the language server protocol itself.  It defines two types of interactions:

* **Notifications**.  For example, the client can send a `textDocument/didOpen` notification to the server to indicate that a file, of the type supported by the server, has been opened.  Notifications are one-way events: there's no expectation of a reply.  In this case, the client is just letting the server know a file has been opened.  There's no formal expectation of what the server does with that knowledge.  Though, in this case, a reasonable outcome would be for the server to read the file in preparation for subsequent requests.
* **request/response pairs**.  For example, the client can send the  `textDocument/definition` request to the server if the editor user invokes the "go to definition" command (e.g. to jump to the implementation of a function from a site where it's called).  The is expected to respond, in this case with a `textDocument/definition` response.  (As a side note: both client and server can issue requests - not just the client).  

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

The position highlights an important point on how the editor and server synchronise. It's all founded on the position in a file, where the position comprises line (row) and column.

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
  * The definition of the symbol in the request is contained in the `uri`.  Note it's a different file to uri in the request.
  * The `start` and `end` define the line & column positions that delimit the definition.  For example, this could be the name of the function being referenced.  

It's entirely up to the server to decide what constitutes the definition.  Note, again, the use of line and column to define position.

<a name="implementation-ovewrview"></a>
## Implementation Overview

OK, enough of the talking - let's code.  There are [many](https://microsoft.github.io/language-server-protocol/implementors/servers/) [examples](https://github.com/openlawlibrary/pygls/tree/master/examples) [available](https://github.com/microsoft/vscode-python-tools-extension-template) and reading them is worthwhile.

### Pre-Requisites

We're using VSCode as the editor, so you need to [install it first](https://code.visualstudio.com/download).  You'll also need to install [git](https://git-scm.com/),   [Node.js](https://nodejs.org/) and [Python](https://www.python.org/downloads/).  Then create a new directory to hold the project:

```bash
$ cd /my/projects/dir
$ mkdir helloLSP 
$ cd helloLSP
```

There's a fair bit of boilerplate that needs to be in place before we can really get started on the implementing support for `greet`.  It's a bit fiddly and difficult to get right from first principles.  However, luckily, we don't need to. I used [this example](https://github.com/openlawlibrary/pygls/tree/master/examples/json-vscode-extension) as a template.  

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

1. Open one of the sample files.  The ditor should show an information message at the bottom of the main window that says "Text Document Did Open".

With that done, the basics are all in place.  Close the development instance for now and go back to the main project instance.  


<a name="language-implementation"></a>
## Implementing the Language 

TODO
