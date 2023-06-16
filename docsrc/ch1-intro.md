# Introduction

The [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) (LSP) provides a way to build editor services for a language that aren't tied to a specific editor or IDE.  [VSCode](https://code.visualstudio.com/api/language-extensions/language-server-extension-guide), [neovim](https://neovim.io/doc/user/lsp.html) and [emacs](https://www.emacswiki.org/emacs/LanguageServerProtocol), for example, all support the LSP at time of writing, meaning a single LSP implementation can be used in all 3 editors.  

Actually, that's not quite true.  Whilst the server component of an LSP implementation can be used as-is, each editor has a different way of integrating the LSP server into it.  This example focuses on [vscode](https://code.visualstudio.com/) as the editor.  By comparison though, the editor-specific clients are a small part of the overall solution.  The server provides all the language "smarts", and that can be reused across editors.  That's the LSP's selling point.


We'll build the server in python using the excellent [pygls](https://github.com/openlawlibrary/pygls) library[^0].

[^0]: why Python?  Because it illustrates using a different language for client and server, it's a popular language, and there are good libraries to support development and testing.  The client implementation language is dictated by the editor - Typescript in the case of vscode.

<a name="lsp-overview"></a>

## LSP Overview

The [LSP specification](https://microsoft.github.io/language-server-protocol/specifications/specification-current/) summarises it thus:

> The Language Server protocol is used between a tool (the client) and a language smartness provider (the server) to integrate features like auto complete, go to definition, find all references and alike into the tool 

That's good enough for here.  There are overviews of the LSP on [Microsoft's official site](https://microsoft.github.io/language-server-protocol/), the [community site](https://langserver.org/) and others too.  Those are worth a read for more background.

```{note}
If you know the basics of how LSP works, you can [skip ahead to the language we'll implement support for](#greet-language).
```

As per the introduction, the solution comprises 2 parts:

* the *client* integrates with the editor - vscode in this case.  Each editor has its own approach to integrating extensions.  Editors support extensions for many languages - so our extension will be one of several installed in any deployment.  The client has to comply with that, so it's job is broadly to:
  * tell the editor what language it supports
  * liaise between the editor and the server
* the *server* provides the smarts on the language (as per the overview quote [above](#lsp-overview))

```{note}
Though vscode calls these "extensions", I'm going to use "plugin" from here on in.  The reason is that "extension" is also used when referring to filenames (e.g. the `.py` part in `file.py`).  We need to refer to both, so I'll use `plugin` for the things that provide language support, and `extension` specifically when referring to file names.
```

<a name="protocol-overview"></a>

(protocol-overview)=

### Client-Server Interaction

The client and server communicate using the language server protocol itself.  It defines two types of interactions:

* **Notifications**.  For example, the client can send a `textDocument/didOpen` notification to the server to indicate that a file, of the type supported by the server, has been opened.  Notifications are one-way events: there's no expectation of a reply.  In this case, the client is just letting the server know a file has been opened.  There's no formal expectation of what the server does with that knowledge.
* **Request/response pairs**.  For example, the client can send the  `textDocument/definition` request to the server if the user invokes the "go to definition" command (e.g. to jump to the implementation of a function from a site where it's called).  The server is expected to respond, in this case with a `textDocument/definition` response.  (As a side note: both client and server can issue requests - not just the client).  

Interactions are encoded using [JSON-RPC](https://www.jsonrpc.org/).  Here's an example (taken from the [official docs](https://microsoft.github.io/language-server-protocol/overviews/lsp/overview/)):

```{code-block} json
:linenos:
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

The position highlights an important point on how the editor and server communicate. It's all founded on the location in a file, comprising line (row) and column.

Here's a typical response (again from the [official docs](https://microsoft.github.io/language-server-protocol/overviews/lsp/overview/)):

```{code-block} json
:linenos:
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

* the `id` is used to correlate the response with the request.  The user might, for example, have changed their mind and started typing again, in which case the editor needs to know it can discard the response.
* the `result` contains the response to the request.  It says:
  * The definition of the symbol referred to in the request is contained in the file specified by the `uri`.  Note it's a different file to the uri in the request.
  * The `start` and `end` define the line & column positions that delimit the definition.  For example, this could be the first and last characters of the name of the function being referenced.  

It's entirely up to the server to decide what constitutes the definition.  Note, again, the use of line and column to define position.

<a name="greet-language"></a>

## The Greet Language

If we're to implement a language *server*, we need a *language*.  Real language servers deal with programming languages.  Implementing programming languages is an entire body of theory and practice in itself.  We don't want to get diverted into that right now, so we'll start with something really simple.

```{note}
If you want to dig into implementing real languages, you could do a lot worse that starting with Bob Nystrom's wonderful book [Crafting Interpreters](https://craftinginterpreters.com/).
```

Thankfully we don't need anything approaching the complexity of a real programming language to implement a language server: we can use something simpler instead.  *Much* simpler, in fact.  Let's call the language *greet*: it's only purpose is to express simple greetings.  First, a couple of examples:

    Hello bob
    Goodbye Nellie

That's it.  Each phrase consists of just two words: a *salutation* - "Hello" or "Goodbye" - and a name.  Here's a grammar[^1] for the language:

[^1]: It's common to formally describe the syntax of a programming language with a grammar, often defined in *Backus-Naur Format* (BNF).  See e.g. [wikipedia](https://en.wikipedia.org/wiki/Syntax_(programming_languages)) for more information.

<a name="greet-grammar"></a>
(greet-grammar)=
```bnf
    greeting    ::= salutation name
    salutation  ::= 'Hello' | 'Goodbye'
    name        ::= [a-zA-Z]+
```

In words, that says:

* A `greeting` comprises a `salutation` followed by a `name`
* A `salutation` is the word `Hello` or the word `Goodbye`
* A `name` is one or more letters, either lower or upper case.  Note there can't be any spaces between the letters: `Nellie` is fine but `Nellie bob` isn't[^3].

[^3]: If the `name` definition is a bit puzzling, read it as follows: 
    * `a-zA-Z` means any lower or upper case letter.  Read it as "any character in the range a to z or A to Z".
    * `[]+` means one or more (`+`) of the thing inside the square brackets `[]`.


We'll write some code to implement the language [a bit later](#language-implementation).  First though, let's look at the structure of the solution.