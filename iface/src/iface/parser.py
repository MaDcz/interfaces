#!/usr/bin/python

import codemodel
import parsimonious

grammar = parsimonious.Grammar("""
file                = consistent_block*
consistent_block    = attr / ns / iface / empty
attr                = attr_decl whsp? attr_value?
ns                  = ns_decl empty* ns_body_open consistent_block* ns_body_close
iface               = iface_decl empty* iface_body_open field* empty* iface_body_close
field               = empty* field_decl

attr_decl           = "@" whsp? attr_path
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

attr_path           = ~"[a-zA-Z_][a-zA-Z0-9_.]*"
attr_value          = ~"(.*)"
attr_value_open     = "("
attr_value_close    = ")"

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
    pass
#endclass

class NodeBuilder(Builder):

    def __init__(self):
        super(NodeBuilder, self).__init__()
        self._attrs = {}
    #enddef

    @property
    def attributes(self):
        return self._attrs
    #enddef

    def add(self, child_builder):
        raise AssertionError("add() not supported by {}".format(type(self).__name__))
    #enddef

    def build(self):
        raise AssertionError("build() not supported by {}".format(type(self).__name__))
    #enddef

    def _create_node(self, node_type):
        node = node_type()
        node.attributes = self._attrs
        return node
    #enddef

#endclass

class FieldBuilder(NodeBuilder):

    def __init__(self):
        super(FieldBuilder, self).__init__()
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

        diagram_node = self._create_node(codemodel.Attribute)
        diagram_node.attributes["name"] = self.field_name
        diagram_node.attributes["type"] = self.field_type
        return diagram_node
    #enddef

#endclass

class InterfaceBuilder(NodeBuilder):

    def __init__(self):
        super(InterfaceBuilder, self).__init__()
        self.iface_name = None
        self.fields = []
    #enddef

    def add(self, child_builder):
        if isinstance(child_builder, FieldBuilder):
            self.fields.append(child_builder)
        else:
            raise Exception("Unsupproted builder type (%s)" % type(child_builder).__name__)
    #enddef

    def build(self):
        if not self.iface_name:
            raise Exception("Interface name missing")

        diagram_node = self._create_node(codemodel.Class)
        diagram_node.attributes["name"] = self.iface_name
        for field in self.fields:
            diagram_node.add(field.build())
        return diagram_node
    #enddef

#endclass

class NamespaceBuilder(NodeBuilder):

    def __init__(self):
        super(NamespaceBuilder, self).__init__()
        self.ns_name = None
        self.content = []
    #enddef

    def add(self, child_builder):
        if isinstance(child_builder, InterfaceBuilder) \
                or isinstance(child_builder, NamespaceBuilder):
            self.content.append(child_builder)
        else:
            raise Exception("Unsupproted builder type (%s)" % type(child_builder).__name__)
    #enddef

    def build(self):
        if not self.ns_name:
            raise Exception("Namespace name missing")

        diagram_node = self._create_node(codemodel.Package)
        diagram_node.attributes["name"] = self.ns_name
        for builder in self.content:
            diagram_node.add(builder.build())
        return diagram_node
    #enddef

#endclass

class FileBuilder(NodeBuilder):

    def __init__(self):
        super(FileBuilder, self).__init__()
        self.content = []
    #enddef

    def add(self, child_builder):
        if isinstance(child_builder, InterfaceBuilder) \
                or isinstance(child_builder, NamespaceBuilder):
            self.content.append(child_builder)
        else:
            raise Exception("Unsupported builder type (%s)" % type(child_builder).__name__)
    #enddef

    def build(self):
        diagram_node = self._create_node(codemodel.Package)
        for builder in self.content:
            diagram_node.add(builder.build())
        return diagram_node
    #enddef

#endclass

class AttributeBuilder(Builder):

    def __init__(self):
        super(AttributeBuilder, self).__init__()
        self._path = None
        self._value = True
    #enddef

    def build(self, builder):
        assert self._path
        dest = builder.attributes
        for part in self._path[:-1]:
            dest[part] = {}
            dest = dest[part]
        dest[self._path[-1]] = self._value
    #enddef

    def _set_path(self, data):
        self._path = data.split(".")
    #enddef

    attr_path = property(fset=_set_path)

    def _set_value(self, data):
        strval = data.strip()
        assert len(strval) > 1
        assert strval[0] == "("
        assert strval[-1] == ")"
        self._value = strval[1:-1]
        # TODO From string to an actual Python object.
    #enddef

    attr_value = property(fset=_set_value)

#endclass

class ClassDiagramGenerator(parsimonious.NodeVisitor):

    def __init__(self, root_builder=None):
        super(ClassDiagramGenerator, self).__init__()
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
            self._top_builder_set_property(node.expr_name, node.text)
        # namespaces
        elif node.expr_name == "ns":
            self._push_builder(NamespaceBuilder())
        elif node.expr_name == "ns_name":
            self._top_builder_set_property(node.expr_name, node.text)
        # interfaces
        elif node.expr_name == "iface":
            self._push_builder(InterfaceBuilder())
        elif node.expr_name == "iface_name":
            self._top_builder_set_property(node.expr_name, node.text)
        elif node.expr_name == "attr":
            self._push_builder(AttributeBuilder())
        elif node.expr_name == "attr_path":
            self._top_builder_set_property("attr_path", node.text)
        elif node.expr_name == "attr_value":
            self._top_builder_set_property("attr_value", node.text)

        ret = super(ClassDiagramGenerator, self).visit(node)

        # finalization
        if node.expr_name in ["ns", "iface", "field"]:
            self._top_builder_add(self._pop_builder())
        elif node.expr_name == "attr":
            attr_builder = self._pop_builder()
            attr_builder.build(self._top_builder)

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

    @property
    def _top_builder(self):
        '''
        Access to the builder currently on top of the stack.
        '''
        return self.builders_stack[-1]
    #enddef

    def _top_builder_set_property(self, name, value):
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

    def _top_builder_add(self, item):
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
