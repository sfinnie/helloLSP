# Extending the Server: Definitions and References

Our simple `greet` language has been effective in getting a language server implementation up and running.  The LSP has a [lot more](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#languageFeatures) features that a language server can implement, for example:

* [Go to Definition](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition): jump to the definition of a symbol from a point where it's referenced.
* [Find References](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references): complement to above which indicates all the places a given symbol is referenced

These aren't relevant to `greet` in its current form: we don't currently define things and refer to them later.  We could, though, extend the language to do that.  Here's an example:

(extended-greet-example)=

```text
Name: Bob
Name: Dolly

Goodbye Bob
Hello Dolly
```

We've added `name` definitions, such that names have to be defined before they can be used in greetings.  It's a little prosaic, but it's simple and provides the basis for implementing "go to definition" and "find references".  What we'd like to happen is as follows:

* If the user right-clicks on "Bob" on the first line and selects "Find References", then "Bob" in "Goodbye Bob" is highlighted
* If the user right-clicks on "Bob" in "Goodbye Bob" and selects "Go To Definition", then they end up back at line 1.

The same applies for Dolly obviously.  That seems pretty simple.  But getting there is going to mean a fair bit of a detour into how our language server parses and analyses the input file.

```{note}
The LSP differentiates between *declaration* and *definition*.  A *declaration* is made when a symbol is introduced but not bound to a value, for example `foo: str` in Python.  A *definition* both introduces a symbol and binds a value, e.g. `foo: str = "bar"`.  Greet's `name:` statements bind values for names, so definitions are appropriate here.
```

## Extending the Language Grammar

First off, let's extend the [greet BNF Grammar](#greet-grammar) we originally created.

(extended-greet-bnf)=

```{code-block} bnf
:linenos:
:emphasize-lines: 1, 2
    statement   ::= definition | greeting
    definition  ::= 'Name:' name
    greeting    ::= salutation name
    salutation  ::= 'Hello' | 'Goodbye'
    name        ::= [a-zA-Z]+
```

The first two lines are additions to the original grammar (which otherwise remains the same).  They say:

* a `statement` in the language is either a `definition` or a `greeting` (line 1)
* a `definition` is the literal `Name:` followed by a `name` (line 2)

It's worth noting a couple of things about the use of `name`:

1. both `definition` and `greeting` refer to the same term on line 5 of the grammar.  That makes sense: we don't want different rules for a valid name when defining it vs using it.
1. Notwithstanding that, the grammar says nothing about a greeting referencing a name that's been defined.  Based on the grammar alone, the following would be valid:

        Name: Bob
        Hello Dolly

The grammar only specifies the language *syntax*.  It doesn't say anything about its *semantics* - its *meaning*.  We haven't had to deal with semantics up to this point.  As humans reading the language, we understand it would break our new rules to greet someone whose name hasn't been defined.  We need to fnd a way to encode that.

## Starting with an end in mind

Before we get into how to extend our code, it's worth stepping back a little and being clear on what we want from the output.  There are three things:

1. To return the definition location when we receive a [textDocument/definition](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition) request;
1. To return the reference location(s) when we receive a [textDocument/references](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references) request;
1. To continue ensuring the file contents are valid, and, if not, report diagnostics as appropriate when we receive the `textDocument/didChange` notification.

We have an implementation of (3) in [the parser we built in Chapter 2](#regex-based-greet-parser).  We'll need to extend it, as name definitions introduce a new failure mode.  That occurs if a greeting statement uses a name that isn't defined.  We'll come back to that in a bit.

Diagnostics are handled by notifications; we receive the `textDocument/didChange` and send back a `textDocument/diagnostic` notification. Definitions and References are both commands that expect a response.  Let's start with `definition`.  We can get a good handle on it by looking at its type signature and an initial skeleton implementation:

```{code-block} python
:linenos:
# server.py

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

```

Note:

1. the input `params` object tells us the file & position the user was at when they invoked the `goto definition` command:
    * The source file name is provided in `params.text_document.uri`.    
    * The position within the file is supplied in `params.position.line` and `params.position.character`, where `character` is the column in the line.  Both are 0-indexed.
1. The response provides several things:
    * `target_uri` denotes the file containing the definition because, in general, a definition might exist in a different file from the reference.  `greet` doesn't support definitions in different files, so the answer here will always be the same as the `params.text_document.uri` value passed in. 
    * `origin_selection` denotes the range of the reference.  The input `position` tells us the `(line, character)` location of the user's cursor.  It's up to the language server to decide what word, or *token*, exists at that point.  More on this below.
    * `target_range` indicates the position of the definition token being referenced.
    * `target_selection_range` is the enclosing context for the reference token.
1. The return type is `LocationLink | None` - which should be read as "either a `LocationLink` or `None`".  The `None` accommodates the possibility that the user has requested `goto definition` for something that isn't a valid reference.

A couple of examples should make that a bit clearer.  Let's use the following example:

```{code-block}
:linenos:
Name: Daljit
Name: Petunia

Hello Daljit
Goodbye Petunia
```

Let's start with the `None` case.  Assume the user's cursor was on (line 3 character 1) - between the `H` and `e` of `Hello`.  That's not a valid reference; salutations (`Hello` / `Goodbye`) are keywords, so they don't refer to anything.







To support definitions and lookups, we'll need some form of data structure that lets us navigate from one place to another in the file.  Each requires us to process the source file.  It's helpful to think of the output we need each time we process the file contents:

1. A collection of zero or more `Diagnostics`, each defining and describing an error in the file, and
1. A way to map name references to their definitions, and vice-versa.

The shape of Diagnostics are defined for us by the LSP and implemented by `lsprotocol.types.Diagnostic`.   We've seen it before in the [initial parser](#regex-based-greet-parser).  


## Bye-bye regular expressions, hello parser-generator

We [implemented the original grammar](language-regex) using a regular expression (regex).  As noted at the time, regexes are powerful but limited.  We could amend the regex to cover our enhanced grammar, but that has two limitations:

1. It gets complicated.  Regexes are notorious for being "write only", meaning that trying to read them is hard.  Our original grammar is already pushing the boundaries; adding our new grammar rules would take us firmly into inscrutable territory.
1. We need the locations of tokens in the file.  For example, we need to know that "Bob" occupies columns 7, 8 and 9 on line 1 in the [example](#extended-greet-example) (assuming we start counting at column 1, not 0).  Regexes don't give us an easy way to do that.

We could hand-write a parser.  We could instead use a [parser-generator](https://en.wikipedia.org/wiki/Comparison_of_parser_generators) that takes a definition of our grammar and creates a parser for us.  There are good reasons to use either approach; we'll use the latter.  There are [many parser-generators available](https://en.wikipedia.org/wiki/Comparison_of_parser_generators).  I've chosen to use [Lark](https://github.com/lark-parser/lark) for a number of reasons:

1. It installs as a Python library, so setup is easy
1. It's easy to use
1. A Lark grammar specification looks quite similar to our BNF definition.
1. It's [well documented](https://lark-parser.readthedocs.io/en/latest/).

# Installing Lark

Installation is easy:

```bash
python3 -m pip install lark
```


