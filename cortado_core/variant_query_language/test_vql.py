from antlr4 import *
from cortado_core.variant_query_language.error_handling import ParseError, LexerError
from cortado_core.variant_query_language.parse_query import (
    parse_query_to_query_tree,
    parse_query_to_tree,
)

def print_tree(tree, lev):
    print(" " * lev) + "` " + str(tree)
    for c in tree.getChildren():
        print_tree(c, lev + 1)


def main():

    with open(".\\cortado_core\\tests\\files\\input.txt", "r") as f:

        for line in f.readlines():

            try:
                print()
                print("Line", line)

                print(parse_query_to_tree(line).toStringTree())
                qT = parse_query_to_query_tree(line)

                print()
                print(qT)

            except LexerError as LE:
                print("Caught Error:", LE.msg)

            except ParseError as PE:
                print("Caught Parse Error", PE.msg)


if __name__ == "__main__":
    """This is executed when run from the command line"""
    main()
