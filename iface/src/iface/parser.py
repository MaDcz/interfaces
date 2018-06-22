#!/usr/bin/python

import codemodel
import parsimonious

grammar = parsimonious.Grammar("""
file                = consistent_block*
consistent_block    = attr / ns / iface / empty
attr                = attr_decl attr_value_notation?
ns                  = ns_decl empty* ns_body_open consistent_block* ns_body_close
iface               = iface_decl empty* iface_body_open attr* field* empty* iface_body_close
field               = empty* field_decl

attr_decl           = empty* "@" attr_path
ns_decl             = "namespace" whsp ns_name
iface_decl          = "interface" whsp iface_name
field_decl          = field_type field_is_repeated? whsp? field_name whsp? field_id_assignment? attr* field_end
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
field_end           = empty* ";"

attr_path             = ~"[a-zA-Z_][a-zA-Z0-9_.]*"
attr_value_notation   = attr_value_open attr_value attr_value_close
attr_value            = attr_value_string / attr_value_bool / attr_value_int / attr_value_float
attr_value_string     = ~'"[^"]*"'
attr_value_bool       = attr_value_bool_true / attr_value_bool_false
attr_value_bool_true  = ~"[tT][rR][uU][eE]"
attr_value_bool_false = ~"[fF][aA][lL][sS][eE]"
attr_value_int        = ~"[0-9]+"
attr_value_float      = ~"[0-9]*\.[0-9]+"
attr_value_open       = "("
attr_value_close      = ")"

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

    def validity_check(self):
        raise AssertionError("validity_check() isn't implemented by {} builder. Every builder needs to implement the function.".format(type(self).__name__))
    #enddef

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

    def _create_node(self, node_type):
        node = node_type()
        node.attributes = self._attrs
        return node
    #enddef

    def add(self, child_builder):
        raise AssertionError("add() not supported by {}".format(type(self).__name__))
    #enddef

    def build(self):
        self.validity_check()
        return self._build()
    #enddef

    def _build(self):
        raise AssertionError("build() isn't implemented by {} builder. Every builder needs to implement the function.".format(type(self).__name__))
    #enddef

#endclass

class FileBuilder(NodeBuilder):

    def __init__(self):
        super(FileBuilder, self).__init__()
        self._content = []
    #enddef

    def add(self, child_builder):
        if isinstance(child_builder, InterfaceBuilder) \
                or isinstance(child_builder, NamespaceBuilder):
            self._content.append(child_builder)
        else:
            raise Exception("Unsupported builder type (%s)" % type(child_builder).__name__)
    #enddef

    def _build(self):
        diagram_node = self._create_node(codemodel.Package)
        for builder in self._content:
            diagram_node.add(builder.build())
        return diagram_node
    #enddef

    def validity_check(self):
        pass
    #enddef

#endclass

class NamespaceBuilder(NodeBuilder):

    def __init__(self):
        super(NamespaceBuilder, self).__init__()
        self._name = None
        self._content = []
    #enddef

    @property
    def ns_name(self):
        return self._name
    #enddef

    @ns_name.setter
    def ns_name(self, data):
        self._name = data.strip()
    #enddef

    def add(self, child_builder):
        if isinstance(child_builder, InterfaceBuilder) \
                or isinstance(child_builder, NamespaceBuilder):
            self._content.append(child_builder)
        else:
            raise Exception("Unsupproted builder type (%s)" % type(child_builder).__name__)
    #enddef

    def _build(self):
        diagram_node = self._create_node(codemodel.Package)
        diagram_node.attributes["name"] = self._name
        for builder in self._content:
            diagram_node.add(builder.build())
        return diagram_node
    #enddef

    def validity_check(self):
        if not self._name:
            raise Exception("Namespace name missing")
    #enddef

#endclass

class InterfaceBuilder(NodeBuilder):

    def __init__(self):
        super(InterfaceBuilder, self).__init__()
        self._name = None
        self._fields = []
    #enddef

    @property
    def iface_name(self):
        return self._name
    #enddef

    @iface_name.setter
    def iface_name(self, data):
        self._name = data.strip()
    #enddef

    def add(self, child_builder):
        if isinstance(child_builder, FieldBuilder):
            self._fields.append(child_builder)
        else:
            raise Exception("Unsupproted builder type (%s)" % type(child_builder).__name__)
    #enddef

    def _build(self):
        diagram_node = self._create_node(codemodel.Class)
        diagram_node.attributes["name"] = self._name
        for field in self._fields:
            diagram_node.add(field.build())
        return diagram_node
    #enddef

    def validity_check(self):
        if not self._name:
            raise Exception("Interface name missing")
    #enddef

#endclass

class FieldBuilder(NodeBuilder):

    def __init__(self):
        super(FieldBuilder, self).__init__()
        self._type = ""
        self._name = ""
        self._id = ""
        self._is_repeated = False
    #enddef

    @property
    def field_type(self):
        return self._type
    #enddef

    @field_type.setter
    def field_type(self, data):
        self._type = data.strip()
    #enddef

    @property
    def field_name(self):
        return self._name
    #enddef

    @field_name.setter
    def field_name(self, data):
        self._name = data.strip()
    #enddef

    @property
    def field_id(self):
        return self._id
    #enddef

    @field_id.setter
    def field_id(self, data):
        self._id = data.strip()
    #enddef

    @property
    def field_is_repeated(self):
        return self._is_repeated
    #enddef

    @field_is_repeated.setter
    def field_is_repeated(self, data):
        self._is_repeated = True
    #enddef

    def _build(self):
        diagram_node = self._create_node(codemodel.Attribute)
        diagram_node.attributes["type"] = self._type
        diagram_node.attributes["name"] = self._name
        # TODO How did I come up with the 'is_repeated' attribute? Is it an UML term?
        diagram_node.attributes["is_repeated"] = self._is_repeated
        return diagram_node
    #enddef

    def validity_check(self):
        if not self._type:
            raise Exception("Field type missing")
        if not self._type in field_types:
            raise Exception("Unknown field type '%s'" % (str(self._type), ))
        if not self._name:
            raise Exception("Field name missing")
    #enddef

#endclass

class AttributeBuilder(Builder):

    def __init__(self):
        super(AttributeBuilder, self).__init__()
        self._path = None
        self._value = True
    #enddef

    @property
    def attr_path(self):
        return self._path
    #enddef

    @attr_path.setter
    def attr_path(self, data):
        self._path = data.split(".")
    #enddef

    @property
    def attr_value(self):
        return self._value
    #enddef

    @attr_value.setter
    def attr_value(self, data):
        try:
            strval = data[0]
            strval_rule = data[1]
        except:
            strval = data
            strval_rule = "attr_value_string"

        if strval_rule == "attr_value_string":
            assert len(strval) > 1
            assert (strval[0] == '"' and strval[-1] == '"') \
                    or (strval[0] == "'" and strval[-1] == "'")
            self._value = strval[1:-1]
        elif strval_rule == "attr_value_bool":
            strval = strval.lower()
            self._value = strval == "true"
        elif strval_rule == "attr_value_int":
            self._value = int(strval)
        elif strval_rule == "attr_value_float":
            self._value = float(strval)
        else:
            raise Exception("Unsupportd attribute value rule '{}'".format(strval_rule))
    #enddef

    def build(self, builder):
        self.validity_check()

        dest = builder.attributes
        for part in self._path[:-1]:
            dest[part] = {}
            dest = dest[part]
        dest[self._path[-1]] = self._value
    #enddef

    def validity_check(self):
        if not self._path:
            raise Exception("Attribute path not provided, duno where to store the value")
    #enddef

#endclass

class ClassDiagramBuilder(parsimonious.NodeVisitor):

    def __init__(self, root_builder=None):
        super(ClassDiagramBuilder, self).__init__()
        self.root_builder = root_builder if root_builder else FileBuilder()
        self.builders_stack = [ self.root_builder ]
    #enddef

    def build(self):
        return self.root_builder.build()
    #enddef

    def generic_visit(self, node, visited_children):
        pass
    #enddef

    def visit(self, node):
        # namespaces
        if node.expr_name == "ns":
            self._push_builder(NamespaceBuilder())
        elif node.expr_name == "ns_name":
            self._top_builder_set_property(node.expr_name, node.text)
        # interfaces
        elif node.expr_name == "iface":
            self._push_builder(InterfaceBuilder())
        elif node.expr_name == "iface_name":
            self._top_builder_set_property(node.expr_name, node.text)
        # fields
        elif node.expr_name == "field":
            self._push_builder(FieldBuilder())
        elif node.expr_name in ["field_type", "field_is_repeated", "field_name", "field_id"]:
            self._top_builder_set_property(node.expr_name, node.text)
        # attributes
        elif node.expr_name == "attr":
            self._push_builder(AttributeBuilder())
        elif node.expr_name == "attr_path":
            self._top_builder_set_property("attr_path", node.text)
        elif node.expr_name == "attr_value_string" \
                or node.expr_name == "attr_value_bool" \
                or node.expr_name == "attr_value_int" \
                or node.expr_name == "attr_value_float":
            self._top_builder_set_property("attr_value", (node.text, node.expr_name))
        #endif

        ret = super(ClassDiagramBuilder, self).visit(node)

        # finalization
        if node.expr_name == "ns":
            self._top_builder_add(self._pop_builder())
        if node.expr_name == "iface":
            interface_builder = self._pop_builder()
            self._top_builder_add(interface_builder)
            interface_builder.validity_check()
            # TODO Full name including relative namespace.
            field_types[interface_builder.iface_name] = interface_builder
        elif node.expr_name == "field":
            self._top_builder_add(self._pop_builder())
        elif node.expr_name == "attr":
            attr_builder = self._pop_builder()
            attr_builder.build(self._top_builder)
        #endif

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

    class_diagram_builder = ClassDiagramBuilder()
    class_diagram_builder.visit(grammar.parse(sys.stdin.read()))

    class_diagram = class_diagram_builder.build()
    print(codemodel.to_json(class_diagram))
#endif __main__
