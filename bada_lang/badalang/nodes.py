"""AST node definitions for the Bada language.

Every node carries a ``line`` for diagnostics.  Nodes are plain data
containers; the compiler walks them to emit bytecode.
"""


class Node:
    line = 0


# --- Expressions -----------------------------------------------------------

class Literal(Node):
    def __init__(self, value, line=0):
        self.value = value
        self.line = line


class ListLit(Node):
    def __init__(self, elements, line=0):
        self.elements = elements
        self.line = line


class MapLit(Node):
    def __init__(self, pairs, line=0):
        self.pairs = pairs  # list of (key_node, value_node)
        self.line = line


class Identifier(Node):
    def __init__(self, name, line=0):
        self.name = name
        self.line = line


class SelfExpr(Node):
    def __init__(self, line=0):
        self.line = line


class Attribute(Node):
    """obj.name  or  obj::name (static/namespace access)."""

    def __init__(self, obj, name, line=0):
        self.obj = obj
        self.name = name
        self.line = line


class Index(Node):
    def __init__(self, obj, index, line=0):
        self.obj = obj
        self.index = index
        self.line = line


class Call(Node):
    def __init__(self, callee, args, line=0):
        self.callee = callee
        self.args = args
        self.line = line


class SuperCall(Node):
    def __init__(self, method, args, line=0):
        self.method = method
        self.args = args
        self.line = line


class Unary(Node):
    def __init__(self, op, operand, line=0):
        self.op = op
        self.operand = operand
        self.line = line


class Binary(Node):
    def __init__(self, op, left, right, line=0):
        self.op = op
        self.left = left
        self.right = right
        self.line = line


class Logical(Node):
    def __init__(self, op, left, right, line=0):
        self.op = op  # 'and' | 'or'
        self.left = left
        self.right = right
        self.line = line


class Assign(Node):
    """target <- value, where target is Identifier/Attribute/Index."""

    def __init__(self, target, value, line=0):
        self.target = target
        self.value = value
        self.line = line


# --- Statements ------------------------------------------------------------

class LetStmt(Node):
    def __init__(self, name, value, line=0):
        self.name = name
        self.value = value
        self.line = line


class ExprStmt(Node):
    def __init__(self, expr, line=0):
        self.expr = expr
        self.line = line


class PrintStmt(Node):
    def __init__(self, args, line=0):
        self.args = args
        self.line = line


class Block(Node):
    def __init__(self, statements, line=0):
        self.statements = statements
        self.line = line


class IfStmt(Node):
    def __init__(self, branches, else_block, line=0):
        self.branches = branches  # list of (cond_node, Block)
        self.else_block = else_block
        self.line = line


class WhileStmt(Node):
    def __init__(self, cond, body, line=0):
        self.cond = cond
        self.body = body
        self.line = line


class ForStmt(Node):
    def __init__(self, var, iterable, body, line=0):
        self.var = var
        self.iterable = iterable
        self.body = body
        self.line = line


class ReturnStmt(Node):
    def __init__(self, value, line=0):
        self.value = value
        self.line = line


class BreakStmt(Node):
    def __init__(self, line=0):
        self.line = line


class ContinueStmt(Node):
    def __init__(self, line=0):
        self.line = line


class ImportStmt(Node):
    def __init__(self, path, alias=None, line=0):
        self.path = path  # list of name parts
        self.alias = alias  # bound name override, or None
        self.line = line


class TryStmt(Node):
    def __init__(self, try_block, catch_var, catch_block, finally_block, line=0):
        self.try_block = try_block
        self.catch_var = catch_var      # name string or None
        self.catch_block = catch_block  # Block or None
        self.finally_block = finally_block  # Block or None
        self.line = line


class ThrowStmt(Node):
    def __init__(self, value, line=0):
        self.value = value
        self.line = line


class FuncDecl(Node):
    def __init__(self, name, params, body, line=0):
        self.name = name
        self.params = params
        self.body = body
        self.line = line


class FieldDecl(Node):
    def __init__(self, name, default, line=0):
        self.name = name
        self.default = default  # expr node or None
        self.line = line


class MethodDecl(Node):
    def __init__(self, name, params, body, is_static=False, line=0):
        self.name = name
        self.params = params
        self.body = body
        self.is_static = is_static
        self.line = line


class ClassDecl(Node):
    def __init__(self, name, parent, fields, methods, line=0):
        self.name = name
        self.parent = parent  # name string or None
        self.fields = fields
        self.methods = methods
        self.line = line
