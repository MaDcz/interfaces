#!/usr/bin/python

# TODO This is probably the first attempt to generate C++ code from an iface file.
#      The C++ generator in codegen is meant to do this but some configuration will
#      be probably needed.

import codemodel

class CppCodeGenerator(codemodel.ClassDiagramVisitor):

    def visit_package(self, node):
        super(CppCodeGenerator, self).visit_package(node)
    #enddef

    def visit_class(self, node):
        print node.name, "{"
        print "public:"
        super(CppCodeGenerator, self).visit_class(node)
        print "}"
    #enddef

    def visit_attribute(self, node):

        print

        pos = node.type.find("[0..*]")
        if pos >= 0:
            # repeated field
            member_type = "std::vector<{}>".format(node.type[0:pos])
            print "const {0}& {1}() const {{ return m_{1}; }}".format(member_type, node.name)
            print "void {1}(const {0}& {1}) {{ m_{1} = {1}; }}".format(member_type, node.name)
            print "{0} m_{1};".format(member_type, node.name)
        else:
            print "{0} {1}() const {{ return m_{1}; }}".format(node.type, node.name)
            print "void {1}({0} {1}) {{ m_{1} = {1}; }}".format(node.type, node.name)
            print "{0} m_{1};".format(node.type, node.name)

        super(CppCodeGenerator, self).visit_attribute(node)
    #enddef

#endclass

if __name__ == "__main__":
    import sys
    import cPickle

    diagram_root_node = cPickle.load(sys.stdin)
    diagram_root_node.accept(CppCodeGenerator())
#endif __main__
