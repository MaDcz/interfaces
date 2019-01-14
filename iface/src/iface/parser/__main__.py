from .module import *

if __name__ == "__main__":
    import argparse
    import sys

    args_parser = argparse.ArgumentParser(description="Generate code based on the input.")
    args_parser.add_argument("-o", "--output", dest="output", default="", help="output file base name or empty (default) for stdout")
    args_parser.add_argument("-I", "--includepath", dest="include_paths", action="append", default=[], help="paths where to look for included files")
    args_parser.add_argument("-d", "--debug", dest="debug", default=False, action="store_true", help="turns debugging messages on")
    args_parser.add_argument("input_files", metavar="INPUT_FILE", nargs="*")

    args = args_parser.parse_args()

    opts["debug"] = args.debug

    # TODO Don't use global register, provide it to the builders explicitly so
    # the purpose of the index builder is more clear.
    interfaces_index_builder = InterfacesIndexBuilder(args.include_paths)
    class_diagram_builder = ClassDiagramBuilder()

    # Parse input into the parsimonious tree and process it in order to build
    # a class diagram from it.
    builders = [ interfaces_index_builder, class_diagram_builder ]
    if args.input_files:
        for input_filepath in args.input_files:
            if input_filepath.strip() == "-":
                ParsimoniousNodeVisitor.process_input(sys.stdin.read(), builders)
            else:
                print_debug("Processing file '{}'.".format(input_filepath))
                ParsimoniousNodeVisitor.process_file(input_filepath, builders)
    else:
        ParsimoniousNodeVisitor.process_input(sys.stdin.read(), builders)

    class_diagram = class_diagram_builder.build()

    # Print the codemodel class diagram to output.
    def print_class_diagram(class_diagram, f):
        print(codemodel.to_json(class_diagram), end="", file=f)

    if args.output:
        with open(args.output, "w") as f:
            print_class_diagram(class_diagram_builder.build(), f)
    else:
        print_class_diagram(class_diagram, sys.stdout)
#endif __main__
