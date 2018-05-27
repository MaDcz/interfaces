#!/usr/bin/python

import codemodel
import parsimonious

grammar = parsimonious.Grammar("""
file                = consistent_block*
consistent_block    = ns / iface / empty
ns                  = ns_decl empty* ns_body_open consistent_block* ns_body_close
iface               = iface_decl empty* iface_body_open field* empty* iface_body_close
field               = empty* field_decl

ns_decl             = "namespace" whsp ns_name
iface_decl          = "interface" whsp iface_name
field_decl          = field_type field_is_repeated? whsp? field_name whsp? field_id_assignment? whsp? field_end
empty               = whsp? comment?

ns_name             = ~"[a-zA-Z_][a-zA-Z0-9_]*"
ns_body_open        = "{"
ns_body_close       = "}"

iface_name          = ~"[a-zA-Z_][a-zA-Z0-9_]*"
iface_body_open     = "{"
iface_body_close    = "}"
field_is_repeated   = "[]"
field_type          = ~"[a-zA-Z_][a-zA-Z0-9_]*"
field_name          = ~"[a-zA-Z_][a-zA-Z0-9_]*"
field_id_assignment = "=" whsp? field_id
field_id            = ~"[1-9][0-9]*"
field_end           = ";"
whsp                = ~"\s+"
comment             = ~"#.*"
""")

field_types = {
    "int"       : None,
    "int32"     : None,
    "uint"      : None,
    "uint32"    : None,
    "float"     : None,
    "double"    : None,
    "bool"      : None,
    "string"    : None,
    "bytes"     : None,
}

class Builder(object):

    def add(self):
        raise AssertionError("add() not supported by Builder instance")
    #enddef

    def build(self):
        raise AssertionError("build() not supported by Builder instance")
    #enddef

#endclass

class FieldBuilder(Builder):

    def __init__(self):
        self.field_type = ""
        self.field_name = ""
        self.field_id = ""
        self.field_is_repeated = ""
    #enddef

    def build(self):
        if not self.field_name:
            raise Exception("Field name missing")
        if not self.field_type:
            raise Exception("Field type missing")
        if not self.field_type in field_types:
            raise Exception("Unknown field type '%s'" % (str(self.field_type), ))

        field_type = self.field_type
        if self.field_is_repeated:
            field_type = field_type + "[0..*]"

        diagram_node = codemodel.Attribute()
        diagram_node.attributes["name"] = self.field_name
        diagram_node.attributes["type"] = self.field_type
        return diagram_node
    #enddef

#endclass

class InterfaceBuilder(Builder):

    def __init__(self):
        self.iface_name = None
        self.fields = []
    #enddef

    def add(self, builder):
        if isinstance(builder, FieldBuilder):
            self.fields.append(builder)
        else:
            raise Exception("Unsupproted builder type (%s)" % type(builder).__name__)
    #enddef

    def build(self):
        if not self.iface_name:
            raise Exception("Interface name missing")

        diagram_node = codemodel.Class()
        diagram_node.attributes["name"] = self.iface_name
        for field in self.fields:
            diagram_node.add(field.build())
        return diagram_node
    #enddef

#endclass

class NamespaceBuilder(Builder):

    def __init__(self):
        self.ns_name = None
        self.content = []
    #enddef

    def add(self, builder):
        if isinstance(builder, InterfaceBuilder) or isinstance(builder, NamespaceBuilder):
            self.content.append(builder)
        else:
            raise Exception("Unsupproted builder type (%s)" % type(builder).__name__)
    #enddef

    def build(self):
        if not self.ns_name:
            raise Exception("Namespace name missing")

        diagram_node = codemodel.Package()
        diagram_node.attributes["name"] = self.ns_name
        for builder in self.content:
            diagram_node.add(builder.build())
        return diagram_node
    #enddef

#endclass

class FileBuilder(Builder):

    def __init__(self):
        self.content = []
    #enddef

    def add(self, builder):
        if isinstance(builder, InterfaceBuilder) or isinstance(builder, NamespaceBuilder):
            self.content.append(builder)
        else:
            raise Exception("Unsupported builder type (%s)" % type(builder).__name__)
    #enddef

    def build(self):
        diagram_node = codemodel.Package()
        for builder in self.content:
            diagram_node.add(builder.build())
        return diagram_node
    #enddef

#endclass

class ClassDiagramGenerator(parsimonious.NodeVisitor):

    def __init__(self, root_builder=None):
        self.root_builder = root_builder if root_builder else FileBuilder()
        self.builders_stack = [ self.root_builder ]
    #enddef

    def generic_visit(self, node, visited_children):
        pass
    #endif

    #enddef

    def visit(self, node):
        # fields
        if node.expr_name == "field":
            self._push_builder(FieldBuilder())
        elif node.expr_name in ["field_type", "field_is_repeated", "field_name", "field_id"]:
            self.top_builder_set_property(node.expr_name, node.text)
        # namespaces
        elif node.expr_name == "ns":
            self._push_builder(NamespaceBuilder())
        elif node.expr_name == "ns_name":
            self.top_builder_set_property(node.expr_name, node.text)
        # interfaces
        elif node.expr_name == "iface":
            self._push_builder(InterfaceBuilder())
        elif node.expr_name == "iface_name":
            self.top_builder_set_property(node.expr_name, node.text)

        ret = super(ClassDiagramGenerator, self).visit(node)

        # finalization
        if node.expr_name in ["field", "ns", "iface"]:
            self.top_builder_add(self._pop_builder())

        return ret
    #enddef

    def _push_builder(self, builder):
        if not isinstance(builder, Builder):
            raise TypeError("Not a Builder instance")

        self.builders_stack.append(builder)
    #enddef

    def _pop_builder(self):
        return self.builders_stack.pop()
    #enddef

    def top_builder_set_property(self, name, value):
        if not self.builders_stack:
            raise Exception("No builder initialized")

        #def to_camel_case(what):
        #    res = u""
        #    to_upper = False
        #    for cp in unicode(what):
        #        if cp == u"_":
        #            if res:
        #                to_upper = True
        #                continue
        #        elif to_upper:
        #            res += cp.upper()
        #        else:
        #            res += cp
        #        to_upper = False
        #    #endfor
        #    return str(res)
        ##enddef

        setattr(self.builders_stack[-1], name, value)
    #enddef

    def top_builder_add(self, item):
        if not self.builders_stack:
            raise Exception("No builder initialized")

        self.builders_stack[-1].add(item)
    #enddef
        
#endclass

if __name__ == "__main__":
    import sys

    diagram_generator = ClassDiagramGenerator()
    diagram_generator.visit(grammar.parse(sys.stdin.read()))

    root = diagram_generator.root_builder.build()
    print(codemodel.to_json(root))
#endif __main__
