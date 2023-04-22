# Introduction

The [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) (LSP) provides a way to build editor services for a language that aren't tied to a specific editor or IDE.  [VSCode](https://code.visualstudio.com/api/language-extensions/language-server-extension-guide), [neovim](https://neovim.io/doc/user/lsp.html) and [emacs](https://www.emacswiki.org/emacs/LanguageServerProtocol), for example, all support the LSP at time of writing, meaning a single LSP implementation can be used in all 3 editors.  

Actually, that's not quite true.  Whilst the server component of an LSP implementation can be used as-is, each editor has a different way of integrating the LSP server into it.  This example focuses on [vscode](https://code.visualstudio.com/) as the editor.  By comparison though, the editor-specific clients are a small part of the overall solution.  The server provides all the language "smarts", and that can be reused across editors.  That's the LSP's selling point.


We'll build the server in python using the excellent [pygls](https://github.com/openlawlibrary/pygls) library[^0].

[^0]: why Python?  Because it illustrates using a different language for client and server, it's a popular language, and there are good libraries to support development and testing.  The client implementation language is dictated by the editor - Typescript in the case of vscode.

## Overview

The [LSP specification](https://microsoft.github.io/language-server-protocol/specifications/specification-current/) summarises it thus:

<a name="lsp-overview"></a>
> The Language Server protocol is used between a tool (the client) and a language smartness provider (the server) to integrate features like auto complete, go to definition, find all references and alike into the tool 

That's good enough for here.  There are overviews of the LSP on [Microsoft's official site](https://microsoft.github.io/language-server-protocol/), the [community site](https://langserver.org/) and others too.  Those are worth a read for more background.

We'll focus below on implementing a working LSP client and server, building it incrementally.

## The Language

If we're to implement a language *server*, we need a *language*.  Real language servers deal with programming languages.  Implementing programming languages is an entire body of theory and practice in itself.  We don't want to get diverted into that right now, so we'll start with something really simple.

```{note}
If you want to dig into implementing real languages, you could do a lot worse that starting with Bob Nystrom's [Crafting Interpreters](https://craftinginterpreters.com/).
```

Thankfully we don't need anything approaching the complexity of a real programming language to implement a language server: we can use something simpler instead.  *Much* simpler, in fact.  Let's call the language *greet*: it's only purpose is to express simple greetings.  First, a couple of examples:

    Hello bob
    Goodbye Nellie

That's it.  Each phrase consists of just two words: a *salutation* - "Hello" or "Goodbye" - and a name.  Here's a grammar[^1] for the language:

[^1]: It's common to formally describe the syntax of a programming language with a grammar, often defined in *Backus-Naur Format* (BNF).  See e.g. [wikipedia](https://en.wikipedia.org/wiki/Syntax_(programming_languages)) for more information.

<a name="greet-grammar"></a>

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
    * `a-zA-Z` means any lower or upper case letter.  Read it as "a to z A to Z"
    * `[]+` means one or more (`+`) of the thing inside the square brackets `[]`.


We'll write some code to implement the language [a bit later](#language-implementation).  First though, let's look at the structure of the solution.