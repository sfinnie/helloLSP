# Hello LSP - an incremental introduction to the Language Server Protocol

A work-in-progress tutorial for building a language server that complies with the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/).  The server is written in Python using the [pygls](https://github.com/openlawlibrary/pygls) library.  For more information, see the [tutorial introduction](docs/intro.md).

## Use

There are two ways to use this repository:

1. As documentation only: a guide for building your own language server.  See the [docs/](docs) directory, starting with [the introduction](docs/intro.md).
1. As documentation and an example implementation. Clone this repo and follow along with the docs as above.  Amend the server according to your needs. 

## Setup

**Note**: These instructions assume a Unix-like environment with a `bash` shell.  They should work for Linux, MacOS and Windows subsystem for Linux (WSL).  

There's no setup required for reading the documentation alone.  To build and run the server, you need to install [vscode](https://code.visualstudio.com/download), [git](https://git-scm.com/), [Node.js](https://nodejs.org/) and [Python](https://www.python.org/downloads/).  

Then clone this repository and setup a virtual environment:

```bash
cd /my/projects/dir
git clone https://github.com/sfinnie/helloLSP
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install pygls pytest pytest-lsp tree-sitter PyYAML
```

Setup the nodejs environment (needed for the language client):

```bash
npm install
cd client
npm install
cd ..
```

If you want to run/build/change the documentation, you need a few extra packages:

```bash
python3 -m pip install sphinx livereload myst-parser
```

## Running the Server

1. Open the project in vscode
2. Run a "development" instance of the editor by typing `ctrl-shift-D`, selecting `Server + Client` in the "Launch" dropdown at the top of the screen, and hitting `F5`.
1. In the development instance of vscode, open [samples/valid.greet](samples/valid.greet).
1. Edit the file.  Valid greetings must have the form `Hello <name>` or `Goodbye <name>`, where name is any contiguous string of upper or lower case letters.  The server should highlight any invalid greetings.

## Running the Documentation Server locally

The documentation is created with [sphynx]().  Browsing locally is useful because it ensures all cross-references work and code samples are correctly highlighted.

1. `cd docs`
2. `make html`
3. Open [docs/_build/html/index.html](docs/_build/html/index.html) in your browser.

### Live reloading 

If you want to edit the documentation, you can run the live reload server.  That will automatically refresh browser contents on change:

1. `python3 run_livereload.py`
1. Open your browser at the specified URL ([http://127.0.0.1:5500](http://127.0.0.1:5500) by default) 

## Contributing

Pull Requests welcome.





