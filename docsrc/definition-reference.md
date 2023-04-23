# Extending the Server: Definitions and References

Our simple `greet` language has been effective in getting a language server implementation up and running.  The LSP has a [lot more](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#languageFeatures) features that a language server can implement, for example:

* [Go to Definition](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition): jump to the definition of a symbol from a point where it's referenced.
* [Find References](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references): complement to above which indicates all the places a given symbol is referenced

These aren't relevant to `greet` in its current form: we don't currently define things and refer to them later.  We could, though, extend the language to do that.  Here's an example:

(extended-greet-example)=

```text
name: Bob
name: Dolly

Goodbye Bob
Hello Dolly
```

We've added `name` definitions, such that names have to be defined before they can be used in greetings.  It's a little prosaic, but it's simple and provides the basis for implementing "go to definition" and "find references".  What we'd like to happen is as follows:

* If the user right-clicks on "Bob" on the first line and selects "Find References", then "Bob" in "Goodbye Bob" is highlighted
* If the user right-clicks on "Bob" in "Goodbye Bob" and selects "Go To Definition", then they end up back at line 1.

The same applies for Dolly obviously.  That seems pretty simple.  But getting there is going to mean a fair bit of a detour into how our language server parses and stores the input file.

```{note}
The LSP provides differentiates between *declaration* and *definition*.  A *declaration* is made when a symbol is introduced but not bound, for example `foo: str` in Python.  A *definition* both introduces a symbol and binds it to a value, e.g. `foo: str = "bar"`.  Greet's `name:` statements bind values for names, so definitions are appropriate.
```

## Extending the Language Grammar

First off, let's extend the [greet BNF Grammar](#greet-grammar) we originally created.

(extended-greet-bnf")=

```{code-block} bnf
:linenos:
:emphasize-lines: 1, 2
    statement   ::= definition | greeting
    definition  ::= 'name:' name
    greeting    ::= salutation name
    salutation  ::= 'Hello' | 'Goodbye'
    name        ::= [a-zA-Z]+
```

The first two lines are additions to the original grammar (which otherwise remains the same).  They say:

* a `statement` in the language is either a `definition` or a `greeting` (line 1)
* a `definition` is the literal `name:` followed by a `name` (line 2)

It's worth noting a couple of things about the use of `name`:

1. both `definition` and `greeting` refer to the same term on line 5 of the grammar.  That makes sense: we don't want different rules for a valid name when defining it vs using it.
1. Notwithstanding that, the grammar says nothing about a greeting referencing a name that's been defined.  Based on the grammar alone, the following would be valid:

        name: Bob
        Hello Dolly

The grammar only specifies the language *syntax*.  It doesn't say anything about its *semantics* - its *meaning*.  We haven't had to deal with semantics up to this point.  As humans reading the language, we understand it would break our new rules to greet someone whose name hasn't been defined.  We need to fnd a way to encode that.

## Bye-bye regular expressions, hello parser-generator

We [implemented the original grammar](language-regex) using a regular expression (regex).  As noted at the time, regexes are powerful but limited.  We could amend the regex to cover our enhanced grammar, but that has two limitations:

1. It gets complicated.  Regexes are notorious for being "write only", meaning that trying to read them is hard.  Our original grammar is already pushing the boundaries; adding our new grammar rules would take us firmly into inscrutable territory.
1. We need the locations of tokens in the file.  For example, we need to know that "Bob" occupies columns 7, 8 and 9 on line 1 in the [example](#extended-greet-example) (assuming we start counting at column 1, not 0).  Regexes don't give us an easy way to do that.

We could hand-write a parser.  We could instead use a [parser-generator](https://en.wikipedia.org/wiki/Comparison_of_parser_generators) that takes a definition of our grammar and creates a parser for us.  There are good reasons to use either approach; we'll use the latter.  There are [many parser-generators available](https://en.wikipedia.org/wiki/Comparison_of_parser_generators).  I've chosen to use [tree-sitter](https://tree-sitter.github.io/) for a number of reasons:

1. It's fast. It was originally created for the [Atom](https://github.com/atom) editor, specifically for parsing and syntax highlighting programming languages.
1. It's easy to use (after a bit of setup)
1. It has python bindings, meaning it's easy to interact with from Python
