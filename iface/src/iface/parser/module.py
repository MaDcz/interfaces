import codemodel
import parsimonious

grammar = parsimonious.Grammar("""
file                = consistent_block*
consistent_block    = include / ns / using_directive / iface / empty
include             = empty* include_decl
attr                = empty* attr_decl attr_value_notation?
ns                  = attr* empty* ns_decl empty* ns_body_open consistent_block* ns_body_close
using_directive     = attr* empty* using_directive_keyword whsp type_name empty* directive_end
iface               = attr* empty* iface_decl empty* iface_body_open field* empty* iface_body_close
field               = attr* empty* field_decl

include_decl        = "include" whsp '"' include_filepath '"'
attr_decl           = "@" attr_path
ns_decl             = "namespace" whsp ns_name
iface_decl          = "interface" whsp type_name
field_decl          = field_type field_is_repeated? whsp field_name whsp? field_id_assignment? attr* field_end
empty               = whsp? comment?

using_directive_keyword = "using"

directive_end = entity_end

entity_end        = ";"
entity_body_start = "{{"
entity_body_end   = "}}"

include_filepath    = ~'[^"]*'

ns_name             = ~"[a-zA-Z_][a-zA-Z0-9_]*"
ns_body_open        = "{{"
ns_body_close       = "}}"

iface_keyword       = "interface"
type_name           = {type_name}
iface_body_open     = "{{"
iface_body_close    = "}}"

field_is_repeated   = whsp? "[]"
field_type          = name_part name_next_part*
field_name          = ~"[a-zA-Z_][a-zA-Z0-9_]*"
field_id_assignment = "=" whsp? field_id
field_id            = ~"[1-9][0-9]*"
field_end           = empty* ";"

name_next_part      = "." name_part
name_part           = ~"[a-zA-Z_][a-zA-Z0-9_]*"

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
""".format(type_name='~"[a-zA-Z_][a-zA-Z0-9_]*"'))


TREATMENT_VALUE_TYPE = "value_type"
TREATMENT_REFERENCE_TYPE = "reference_type"

field_types = {}

def register_type(identifier, treatment="", declaration=None, definition=None):
    if identifier in field_types:
        raise RuntimeError("Type '{}' redefinition.".format(identifier))

    type_info = {}
    if treatment: type_info["treatment"] = treatment
    if declaration: type_info["declaration"] = declaration
    if definition: type_info["definition"] = definition

    field_types[identifier] = type_info
#enddef

register_type("int", treatment=TREATMENT_VALUE_TYPE)
register_type("int32", treatment=TREATMENT_VALUE_TYPE)
register_type("uint", treatment=TREATMENT_VALUE_TYPE)
register_type("uint32", treatment=TREATMENT_VALUE_TYPE)
register_type("float", treatment=TREATMENT_VALUE_TYPE)
register_type("double", treatment=TREATMENT_VALUE_TYPE)
register_type("bool", treatment=TREATMENT_VALUE_TYPE)
register_type("string", treatment=TREATMENT_REFERENCE_TYPE)
register_type("bytes", treatment=TREATMENT_REFERENCE_TYPE)


opts = {
    "debug": False
}

def print_debug(*posargs, **kwargs):
    import sys
    if opts["debug"]:
        print("[D]", *posargs, **kwargs, file=sys.stderr)
#enddef

def get_parent_namespaces(builder):
    namespaces = []
    parent = builder.parent
    while parent is not None:
        if isinstance(parent, NamespaceBuilder):
            namespaces.insert(0, parent.ns_name)
        parent = parent.parent
    pass
    return namespaces
#enddef

class Builder(object):

    def __init__(self):
        self._parent = None
    #enddef

    def add(self, child_builder):
        raise AssertionError("add() not supported by {}".format(type(self).__name__))
    #enddef

    @property
    def parent(self):
        return self._parent
    #enddef

    def set_parent(self, parent):
        self._parent = parent
    #enddef

    def validity_check(self):
        raise AssertionError("validity_check() isn't implemented by {} builder. Every builder needs to implement the function.".format(type(self).__name__))
    #enddef

    def __str__(self):
        return self.__class__.__name__
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
            child_builder.set_parent(self)
        else:
            raise Exception("Unsupported builder type (%s)" % type(child_builder).__name__)
    #enddef

    def _build(self):
        diagram_node = self._create_node(codemodel.Package)

        using = {}
        for full_type, type_info in field_types.items():
            using_type_info = {}

            treatment = type_info.get("treatment", "")
            if not treatment and "declaration" in type_info: treatment = type_info["declaration"].attributes.get("treatment", "")
            if not treatment and "definition" in type_info: treatment = type_info["definition"].attributes.get("treatment", "")
            if treatment:
                if treatment not in [TREATMENT_VALUE_TYPE, TREATMENT_REFERENCE_TYPE]:
                    raise RuntimeError("Invalid treatment '{}' for type '{}'.".format(treatment, full_type))
                using_type_info["treatment"] = treatment

            using[full_type] = using_type_info

        if using:
            diagram_node.attributes["using"] = using

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
            child_builder.set_parent(self)
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

class TypeBuilder(NodeBuilder):

    def __init__(self):
        super(TypeBuilder, self).__init__()
        self._name = None
    #enddef

    @property
    def type_name(self):
        return self._name
    #enddef

    @type_name.setter
    def type_name(self, data):
        self._name = data.strip()
        assert self._name
    #enddef

    def _build(self):
        diagram_node = self._create_node(codemodel.Class)
        diagram_node.attributes["name"] = self._name
        return diagram_node
    #enddef

    def validity_check(self):
        if not self._name:
            raise Exception("Interface name missing")
    #enddef

#endclass

class InterfaceBuilder(TypeBuilder):

    def __init__(self):
        super(InterfaceBuilder, self).__init__()
        self._fields = []
    #enddef

    def add(self, child_builder):
        if isinstance(child_builder, FieldBuilder):
            self._fields.append(child_builder)
            child_builder.set_parent(self)
        else:
            raise Exception("Unsupproted builder type (%s)" % type(child_builder).__name__)
    #enddef

    def _build(self):
        diagram_node = super(InterfaceBuilder, self)._build()
        for field in self._fields:
            diagram_node.add(field.build())
        return diagram_node
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
        # TODO Don't split it, the splitted form can't be used as a key of an json object. The '.' notation
        # is used in 'using' section, so keep it consistent.
        diagram_node.attributes["type"] = self._type.split(".")
        diagram_node.attributes["full_type"] = self._full_type.split(".")
        diagram_node.attributes["name"] = self._name
        # TODO How did I come up with the 'is_repeated' attribute? Is it an UML term?
        diagram_node.attributes["is_repeated"] = self._is_repeated
        return diagram_node
    #enddef

    def validity_check(self):
        if not self._type:
            raise Exception("Field type missing")

        if self._full_type not in field_types:
            # Shouldn't get here as the full type must be resolvable, otherwise an exception
            # will be raised.
            assert False

        if not self._name:
            raise Exception("Field name missing")
    #enddef

    @property
    def _full_type(self):
        """
        Returns full type of the field. Note that the type can be provided
        as a relative path so in order to resolve the full type, we need to
        have the builders tree finalized. Don't use this property when the
        builders tree isn't complete.
        """
        namespaces = get_parent_namespaces(self)
        for i in reversed(range(len(namespaces) + 1)):
            full_type = ".".join(namespaces[0:i] + [ self._type ])
            if full_type in field_types:
                return full_type

        raise RuntimeError("Cannot resolve field type.")
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

class NullBuilder(Builder):

    def __init__(self):
        super(NullBuilder, self).__init__()
    #enddef

    @property
    def attributes(self):
        return {}
    #enddef

    def build(self):
        pass
    #enddef

    def validity_check(self):
        pass
    #enddef

#endclass

class ParsimoniousNodeVisitor(parsimonious.NodeVisitor):

    class Node(object):

        def __init__(self, parsimonious_node):
            self._parsimonious_node = parsimonious_node
        #enddef

        @property
        def name(self):
            return self._parsimonious_node.expr_name
        #enddef

        @property
        def text(self):
            return self._parsimonious_node.text
        #enddef

        def __str__(self):
            return self.name
        #enddef

    #endclass

    NOI = set([ "include", "include_filepath",
                "ns", "ns_name",
                "using_directive",
                "type_name",
                "iface",
                "field", "field_type", "field_is_repeated", "field_name", "field_id",
                "attr", "attr_path", "attr_value_string", "attr_value_bool", "attr_value_int", "attr_value_float" ])

    def __init__(self, builders=[]):
        super(ParsimoniousNodeVisitor, self).__init__()

        self._builders = builders
    #enddef

    def generic_visit(self, node, visited_children):
        pass
    #enddef

    def visit(self, parsimonious_node):
        node = ParsimoniousNodeVisitor.Node(parsimonious_node)

        assert "iface" in ParsimoniousNodeVisitor.NOI
        interested = node.name in ParsimoniousNodeVisitor.NOI

        if interested:
            print_debug("Node {} begin.".format(node))
            for builder in self._builders:
                builder.node_begin(node)

        ret = super(ParsimoniousNodeVisitor, self).visit(parsimonious_node)

        if interested:
            print_debug("Node {} end.".format(node))
            for builder in self._builders:
                builder.node_end(node)

        return ret
    #enddef

    @classmethod
    def process_file(cls, fpath, builders):
        with open(fpath, "r") as f:
            inp = f.read()
            cls.process_input(inp, builders)
    #enddef

    @classmethod
    def process_input(cls, inp, builders):
        tree = grammar.parse(inp)
        tree_visitor = cls(builders)
        tree_visitor.visit(tree)
    #enddef

#endclass

class InterfacesIndexBuilder(object):

    def __init__(self, include_paths):
        self._include_paths = include_paths
        self._nodes_stack = []
        self._type_nodes_stack = []

        self._attribute_builder = None
    #enddef

    def node_begin(self, node):
        if node.name == "ns":
            self._type_nodes_stack.append(NamespaceBuilder())

        elif node.name == "ns_name":
            assert self._type_nodes_stack
            assert isinstance(self._type_nodes_stack[-1], NamespaceBuilder)
            setattr(self._type_nodes_stack[-1], node.name, node.text)

        elif node.name == "iface":
            self._type_nodes_stack.append(InterfaceBuilder())

        elif node.name == "using_directive":
            self._type_nodes_stack.append(TypeBuilder())

        elif node.name == "type_name":
            def get_name(builder_or_name):
                if isinstance(builder_or_name, str):
                    return builder_or_name
                elif isinstance(builder_or_name, NamespaceBuilder):
                    return builder_or_name.ns_name
                elif isinstance(builder_or_name, TypeBuilder):
                    return builder_or_name.type_name
                else:
                    assert False
            #enddef

            def get_full_name(stack):
                full_name_parts = map(lambda b: get_name(b), stack)
                return ".".join(full_name_parts)
            #enddef

            full_name = ""
            declaration = None
            definition = None
            if self._find_parent_by_name("iface"):
                assert self._type_nodes_stack
                assert isinstance(self._type_nodes_stack[-1], InterfaceBuilder)
                setattr(self._type_nodes_stack[-1], node.name, node.text)
                full_name = get_full_name(self._type_nodes_stack)
                definition = self._type_nodes_stack[-1]
            elif self._find_parent_by_name("using_directive"):
                assert self._type_nodes_stack
                assert isinstance(self._type_nodes_stack[-1], TypeBuilder)
                setattr(self._type_nodes_stack[-1], node.name, node.text)
                full_name = get_full_name(self._type_nodes_stack)
                declaration = self._type_nodes_stack[-1]
            else:
                assert False

            # Register interface.
            assert full_name
            print_debug("Registering type '{}'.".format(full_name))
            register_type(full_name, declaration=declaration, definition=definition)

        # attributes
        elif node.name == "attr":
            assert not self._attribute_builder
            self._attribute_builder = AttributeBuilder()
        elif node.name == "attr_path":
            assert self._attribute_builder
            self._attribute_builder.attr_path = node.text
        elif node.name == "attr_value_string" \
                or node.name == "attr_value_bool" \
                or node.name == "attr_value_int" \
                or node.name == "attr_value_float":
            assert self._attribute_builder
            self._attribute_builder.attr_value = (node.text, node.name)

        elif node.name == "include_filepath":
            for include_path in self._include_paths:
                import os.path
                # TODO Detect already indexed and loops.
                filepath = os.path.join(include_path, node.text)
                print_debug(">>> Indexing file '{}'".format(filepath))
                ParsimoniousNodeVisitor.process_file(filepath,
                        [ InterfacesIndexBuilder(self._include_paths) ])
                print_debug("<<< Indexing file '{}'".format(filepath))
        #endif

        self._nodes_stack.append(node)
    #enddef

    def node_end(self, node):
        self._nodes_stack.pop()

        if node.name == "ns":
            assert self._type_nodes_stack
            assert isinstance(self._type_nodes_stack[-1], NamespaceBuilder)
            self._type_nodes_stack.pop()

        elif node.name == "iface":
            assert self._type_nodes_stack
            assert isinstance(self._type_nodes_stack[-1], InterfaceBuilder)
            self._type_nodes_stack.pop()

        elif node.name == "using_directive":
            assert self._type_nodes_stack
            assert isinstance(self._type_nodes_stack[-1], TypeBuilder)
            self._type_nodes_stack.pop()

        elif node.name == "attr":
            assert self._type_nodes_stack
            assert self._attribute_builder
            self._attribute_builder.build(self._type_nodes_stack[-1])
            self._attribute_builder = None
    #enddef

    def _find_parent_by_name(self, name):
        for node in reversed(self._nodes_stack):
            if node.name == name:
                return node
        return None
    #enddef

#endclass

class ClassDiagramBuilder(object):

    def __init__(self, root_builder=None):
        self.root_builder = root_builder if root_builder else FileBuilder()
        self.builders_stack = [ self.root_builder ]
    #enddef

    def build(self):
        return self.root_builder.build()
    #enddef

    def node_begin(self, node):
        # namespaces
        if node.name == "ns":
            self._push_builder(NamespaceBuilder())
        elif node.name == "ns_name":
            self._top_builder_set_property(node.name, node.text)
        # using directive (used only to build index, not class diagram)
        elif node.name == "using_directive":
            self._push_builder(NullBuilder())
        # interfaces
        elif node.name == "iface":
            self._push_builder(InterfaceBuilder())
        elif node.name == "type_name":
            self._top_builder_set_property(node.name, node.text)
        # fields
        elif node.name == "field":
            self._push_builder(FieldBuilder())
        elif node.name in ["field_type", "field_is_repeated", "field_name", "field_id"]:
            self._top_builder_set_property(node.name, node.text)
        # attributes
        elif node.name == "attr":
            self._push_builder(AttributeBuilder())
        elif node.name == "attr_path":
            self._top_builder_set_property("attr_path", node.text)
        elif node.name == "attr_value_string" \
                or node.name == "attr_value_bool" \
                or node.name == "attr_value_int" \
                or node.name == "attr_value_float":
            self._top_builder_set_property("attr_value", (node.text, node.name))
        #endif
    #enddef

    def node_end(self, node):
        if node.name == "ns":
            self._top_builder_add(self._pop_builder())
        elif node.name == "using_directive":
            self._pop_builder()
        elif node.name == "iface":
            self._top_builder_add(self._pop_builder())
        elif node.name == "field":
            self._top_builder_add(self._pop_builder())
        elif node.name == "attr":
            attr_builder = self._pop_builder()
            attr_builder.build(self._top_builder)
    #enddef

    def _push_builder(self, builder):
        print_debug("Pushing {} on top of the builders stack.".format(builder))

        if not isinstance(builder, Builder):
            raise TypeError("Not a Builder instance")

        self.builders_stack.append(builder)
    #enddef

    def _pop_builder(self):
        builder = self.builders_stack.pop()

        print_debug("Popping {} from top of the builders stack.".format(builder))

        return builder
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
