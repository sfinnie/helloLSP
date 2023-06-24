from tree_sitter import Language, Parser

Language.build_library(
    'build/greet-parser.so',

    [
        '../tree-sitter-greet'
    ]
)

GREET_LANGUAGE = Language('build/greet-parser.so', 'greet')

parser = Parser()
parser.set_language(GREET_LANGUAGE)

sample = bytes("""hello Petunia""", "utf8")
tree = parser.parse(sample)

root_node = tree.root_node
assert root_node.type == "source_file"
assert root_node.start_point == (0,0)
assert root_node.end_point == (0,13)


