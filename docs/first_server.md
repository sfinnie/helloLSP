# A First Server

<a name="implementation-skeleton"></a>

## Implementation Skeleton

OK, enough of the talking - let's code.  I'm assuming a Unix-like environment below, with a `bash` shell.  That should work for Linux, MacOS and Windows subsystem for Linux (WSL).  

### Pre-Requisites

We're using vscode as the editor, so you need to [install it first](https://code.visualstudio.com/download).  You'll also need to install [git](https://git-scm.com/),   [Node.js](https://nodejs.org/) and [Python](https://www.python.org/downloads/).  

Then create a new directory to hold the project:

```{code-block} bash
:linenos:
cd /my/projects/dir
mkdir helloLSP 
cd helloLSP
```

```{note}
You can copy all the code from the git repository [here](https://github.com/sfinnie/helloLSP) if you'd prefer not to follow these steps.
```

There's a fair bit of boilerplate that needs to be in place before we can really get started on implementing support for `greet`.  It's a bit fiddly and difficult to get right from first principles.  However, luckily, we don't need to. I used [this example](https://github.com/openlawlibrary/pygls/tree/master/examples/json-vscode-extension) as a template.  There are [many](https://microsoft.github.io/language-server-protocol/implementors/servers/) [examples](https://github.com/openlawlibrary/pygls/tree/master/examples) [available](https://github.com/microsoft/vscode-python-tools-extension-template) and reading some others too is worthwhile to get a sense of what's involved.

To build initially and check it's working:

1. Set up the Server Python environment

    ```{code-block} bash
    :linenos:
    python3 -m venv venv
    source venv/bin/activate
    python3 -m pip install -U pip
    python3 -m pip install pygls
    ```

1. Set up the client nodejs environment

    ```{code-block} bash
    :linenos:
    npm install
    cd client
    npm install
    cd ..
    ```

1. Start vscode in the project root dir

    ```{code-block} bash
    :linenos:
    code .
    ```

1. Edit `vscode/settings.json` to ensure the python interpreter path is set correctly:

    ```{code-block} json
    :linenos:
    {
        "python.interpreterPath": "${workspaceFolder}/venv/bin/python3"
    }
    ```

    You'll need to adjust this as required for your platform.  On Windows, this is likely to be `${workspaceFolder}/venv/Scripts/python`.

1. Run the extension client and server in a separate "development" instance of vscode by typing `ctrl-shift-D`, selecting `Server + Client` in the "Launch" dropdown at the top of the screen, and hitting `F5`.

1. In the development instance of vscode, open the `samples` sub-directory of this project.

1. Open the sample json file.  The editor should show an information message at the bottom of the main window that says "Text Document Did Open".

With that done, the basics are all in place.  Close the development instance for now and go back to the main project instance.  The code at this point is [tagged as v0.1](https://github.com/sfinnie/helloLSP/releases/tag/v0.1) if you want to have a look.

## Anatomy of the Plugin

Despite all the boilerplate, there are 3 primary files that implement the plugin:

* [client/src/extension.ts](../client/src/extension.ts) implements the client
* [server/server.py](../server/server.py) implements the server.
* [package.json](../package.json) describes the capabilities that the client and server provide.


## Tidying up the skeleton

```{note}
If you're eager to get onto actually implementing language support, then [skip ahead](#language-implementation).  This section cleans up the skeleton and gets ready for that.  Understanding how things fit together can be instructive, but if it's not your bag, move along.  
```

With the skeleton in place, we can start making the changes needed to support our `greet` language.   There are a few housekeeping tasks to complete:

1. Change the plugin so it's activated on files with a `.greet` extension (the skeleton is activated for `json` files)
1. Get rid of the extraneous commands supported by the skeleton that we don't need.
1. Rename the relevant classes, methods and names from `json` to `greet`

### Tiny baby steps - setting the language

Let's start with the filename extension.  There's actually 2 parts to this, because vscode separates language *identity* from the filename *extension*.  That allows a single language to support multiple extensions.  For example: the Java tooling supports both `.jav` and `.java` extensions.

The language and extension(s) are configured in the `package.json` file.  The relevant section in the skeleton reads as follows:

```{code-block} json
:linenos:
"activationEvents": [
    "onLanguage:json"
  ],
```

We need to make a few changes.  For a start, the skeleton assumes vscode already knows about `json` as a language.  It won't know anything about `greet` though.  So we need to define the language identity, define the file extensions, and let vscode know when to activate our plugin.  Here's what that looks like[^4]

[^4]: It's not strictly necessary to include the `activationEvents` section: vscode infers that from language contributions in recent versions.  There's no downsides to doing so though, and means the extension will work with older versions of vscode.

```{code-block} json
:linenos:
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

It's also referenced in `client/src/extension.ts`:

```{code-block} typescript
:linenos:
function getClientOptions(): LanguageClientOptions {
    return {
        // Register the server for plain text documents
        documentSelector: [
            { scheme: "file", language: "json" },
            { scheme: "untitled", language: "json" },
        ],
    //...
    }
}
```

We need to change that to:


```{code-block} typescript
:linenos:
:emphasize-lines: 5, 6
function getClientOptions(): LanguageClientOptions {
    return {
        // Register the server for 'greet' documents
        documentSelector: [
            { scheme: "file", language: "greet" },
            { scheme: "untitled", language: "greet" },
        ],
    //...
    }
}
```

With those changed, we can launch the plugin in a development window again (`ctrl-shift-D`, select "Server + Client", hit `F5`).  Open `samples/valid.greet` in the editor and, again, you should see the `Text Document Did Open` message. Close the development instance.  Change 1 complete.


### Cleaning up 

The skeleton plugin implements multiple commands for illustration.  We don't need them here, so they can be removed.  If you run the plugin in a development instance and type `ctrl-shift-p` then enter "countdown" in the dialogue box, you should see several options like "Count down 10 seconds [Blocking]".  That needs changes in 2 places:

* `package.json`, which declares the commands the plugin supports
* `server.py` which implements them.

Here's an excerpt from each.

```{code-block} json
:linenos:
:emphasize-lines: 4
//package.json
    "commands": [
      {
        "command": "countDownBlocking",
        "title": "Count down 10 seconds [Blocking]"
      },
      // several more
    ]
```

```{code-block} python
:linenos:
:emphasize-lines: 3, 6
# server.py
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

The skeleton is based on suport for `json` files, and that's used throughout `client/src/extension.ts`, `server/server.py` and `package.json`.


### Package.json

Let's start with `package.json`.  The first chunk of relevance sits right at the top of the file:

```{code-block} json
:linenos:
{
  "name": "json-extension",
  "description": "Simple json extension example",
  "author": "Open Law Library",
  "repository": "https://github.com/openlawlibrary/pygls",
  "license": "Apache-2.0",
  "version": "0.11.3",
  "publisher": "openlawlibrary",
  //...
}
```
We can change that as follows:

```{code-block} json
:linenos:
:emphasize-lines: 2, 3, 4, 5, 7, 8
{
  "name": "greet",
  "description": "Support for the greet salutation example language",
  "author": "sfinnie",
  "repository": "https://github.com/sfinnie/helloLSP",
  "license": "Apache-2.0",
  "version": "0.0.1",
  "publisher": "sfinnie",
  //...
}
```

The next bit is the configuration section.  It currently reads:

```{code-block} json
:linenos:
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

```{code-block} json
:linenos:
:emphasize-lines: 3, 8
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

The only relevant section in the client is in the `getClientOptions()` function that we update earlier.  Here's how it looks currently:

```{code-block} typescript
:linenos:
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
```{code-block} typescript
:linenos:
:lineno-start: 8
        outputChannelName: "[pygls] GreetLanguageServer",
```
I've left `[pygls]` in there.  It's completely optional, but it might be useful to know that's what the server is based on.  If nothing else, it's a nice little acknowledgement for the good folks who put `pygls` together and shared it with the world.


That's it for the client - onto the server.

### server.py

The change in the server is the main language server class:

```{code-block} python
:linenos:
class JsonLanguageServer(LanguageServer):
    CMD_PROGRESS = 'progress'
    #...

json_server = JsonLanguageServer('pygls-json-example', 'v0.1')
```

Unsurprisingly, that becomes:

```{code-block} python
:linenos:
:emphasize-lines: 1, 5
class GreetLanguageServer(LanguageServer):
    CMD_PROGRESS = 'progress'
    #...

greet_server = GreetLanguageServer('pygls-greet-example', 'v0.1')
```

`greet_server` is referenced in several places in the file, so they all need updated.  Same with `GreetLanguageServer`.

There's a couple of functions for validating the contents of a file (`_validate()`, `_validate_json()`).  We're going to update them later, so can leave the `json` references for now.

That's the renaming complete.  Time, at last, to actually start implementing our support for greet.

(language-implementation)=

## Implementing Greet Language Support

Hurrah!  Finally time to implement the language support.  But what does that actually mean?  The Language Server Protocol defines several [language features](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#languageFeatures), for example:

* [Goto Declaration](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_declaration)
* [Find References](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_references)
* [Completion Items](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_completion)

We'll start with checking that a `greet` file is consistent with the [greet grammar](greet-grammar).  We know from [earlier](#protocol-overview) that notifications can be sent from the client to the server and vice-versa.  One of those notifications is `textDocument/didOpen` which is sent when a document, of the type supported by the plugin, is opened. We saw that in the development instance: it displayed the message `Text Document Did Open` when we opened a file with the `.greet` extension.  Here's the source of that in `server.py`:

(did-open)=

```{code-block} python
:linenos:
:emphasize-lines: 1, 5
@greet_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message('Text Document Did Open')
    _validate(ls, params)
```

The `@greet_server.feature` line is where `pygls` does its magic.  Behind that simple line, `pygls` manages receiving the notification in `json-rpc` format, parsing out the parameters into a `DidOpenTextDocumentParams` object, and calling the `did_open` function.  Aside from showing the message we saw on screen earlier[^5], the function calls `_validate()` to check the file contents [^6]. 

[^5]: Just in case you're in any doubt, change the message to something like 'Text Document Did Open a greet file' and launch a development instance.  Open a `.greet` file, and marvel at the outcome.

[^6]: the underscore is a convention to indicate that `validate()` is a function only intended for use inside `server.py`.  


The skeleton `_validate()` function checks whether the file is valid `json` so we need to change that.  The compiler world tends to talk about *parsing* rather than *validating*.  It's a bit pedantic, but I'm going to stick to that here.  So the functions we'll look at are named `_parse()` not `_validate()`.  The skeleton functions cover the following:

1. Extracting the source file contents from the parameters
1. Checking the contents

It's worth noting at this point that the `DidOpenTextDocumentParams` object contains the *actual content* of the file being edited, not just a `uri` reference for it.  This is a deliberate design decision in the protocol.  From the [spec](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_didOpen):

> The document’s content is now managed by the client and the server must not try to read the document’s content using the document’s Uri. 

Back to the functions.  The first one doesn't change (other than the name and log message):

```{code-block} python
:linenos:
def _parse(ls: GreetLanguageServer, params: DidOpenTextDocumentParams):
    ls.show_message_log('Validating greeting...')

    text_doc = ls.workspace.get_document(params.text_document.uri)

    source = text_doc.source
    diagnostics = _parse_greet(source) if source else []

    ls.publish_diagnostics(text_doc.uri, diagnostics)
```

Note the error handling if there's no source content.  `ls.publish_diagnostics()` passes any errors found back to the client for display in the editor.  The meat is in the `_parse_greet()` function.  How do we parse the file?  The grammar tells us the rules for a greeting, but how do we implement it?  The skeleton takes advantage of Python's `json.loads()` function to do the parsing.  Here's the skeleton implementation:

```{code-block} python
:linenos:
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

Not unreasonably, Python's standard library doesn't have a built-in function for reading `.greet` files.  There's lots of well-established [theory](https://en.wikipedia.org/wiki/Parsing) on parsing, several techniques, and lots of libraries to support it.  We'll explore those later.  But for now, that's a bit overkill for our needs here.  Our approach is broadly:

1. Read in the file, breaking it up into lines
1. For each line, check if it contains a valid greeting:
    1. Does it start with either "Hello" or "Goodbye"?
    1. If so, is it followed by a name that satisfies the `[a-zA-Z]+` pattern?

Here's the implementation:

```{code-block} python
:linenos:
:emphasize-lines: 7
def _parse_greet(source: str):
    """Parses a greeting file.  
        Generates diagnostic messages for any problems found
    """
    diagnostics = []

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
```

The first thing to note is the grammar:

<a name="language-regex"></a>

```{code-block} python
:linenos:
:lineno-start: 7
grammar = re.compile(r'^(Hello|Goodbye)\s+([a-zA-Z]+)\s*$')
```

 It's a [regular expression](https://docs.python.org/3/howto/regex.html) (aka regex) and shows off the pros and cons of using them.  On the 'pro' side, it's a very succinct way of expressing the grammar.  On the 'con' side, it's a very succinct way of expressing the grammar.  This is about the limit of regex complexity I'm personally comfortable with: it's still readable with some concentration.  Much more than this, though, and I'd want to take a different approach.  For sake of clarity, let's break it down.

 * The `^` means the grammar must match the start of the line: there can't be any characters (including white space) before the first pattern
 * The first pattern matches the salutation: `(Hello|Goodbye)` means match the string 'Hello' or the string 'Goodbye'.  The brackets mean the match will capture which string matched: we're not using that here but will later.
 * The second pattern - `\s+` - means match one or more white space characters after the salutation and before what follows.  `\s` means match a single whitespace character (space, tab); `+` means match one or more.
 * The third pattern matches the name: `([a-zA-Z]+)`.  This is exactly the same as the formal grammar defined [previously](#greet-grammar).  Again, the surrounding brackets mean the value should be captured if match is successful
 * The final pattern - `\s*$` - means match zero or more whitespace characters before the end of the line.  `\s` means match a single whitespace character as before; `*` means match zero or more; and `$` means match the end of the string.

 We iterate through each line in the file in turn, checking if it matches the grammar.  If it doesn't, we create a `Diagnostic` instance that specifies the location of the problem and the error message to show.  In this first incarnation, we're not breaking down where the error lies.  That's viable with a grammar as simple as `greet` in its current form.  Anything more complex and we'd want to be a bit more specific with error messages, but it's plenty good for now.  Spin up a development instance (`ctrl-shift-D` and `f5`), open the sample .greet file, and have a play.  The editor should show a red squiggly for any lines that don't match the grammar, and show the diagnostic message if you hover over an error:

 ![Sample diagnostics](images/diagnostics1.png)

Play about in the development instance, and the editor will respond as a line moves between being valid and invalid.  Now, if you've had your porridge/coffee/whatever, and are feeling super alert, you might be wondering why.  So far, we've only looked at the `textDocument/didOpen` message.  That only gets sent when a file is opened.  So how is the editor responding as we edit the file?  The answer is the skeleton already implements another notification, `textDocument/didChange`:

```{code-block} python
:linenos:
@greet_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _parse(ls, params)
```

Compare it to the `textDocument/didOpen` function [above](#did-open) and you'll see the implementation is exactly the same: call the `_parse()` function.  So parsing gets invoked both when a file is opened, and when it's changed.

That's it for our first language feature implementation - job done.  It's notable that the code for actually checking the file has taken a lot less column inches than all of the preparation that preceded it.  Of course, `greet` is a trivial language.  And, so far, we've only implemented basic diagnostics.  

The code at this point is tagged as [v0.2](https://github.com/sfinnie/helloLSP/releases/tag/v0.2).

Before we add any additional capabilities, we should think about testing.


