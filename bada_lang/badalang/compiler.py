"""Compiler: lowers a Bada AST into bytecode CodeObjects."""

from . import nodes as N
from . import opcodes as O
from .objects import CodeObject, ClassDescriptor
from .errors import BadaSyntaxError


class LoopContext:
    def __init__(self):
        self.breaks = []
        self.continue_target = None


class Compiler:
    def __init__(self, name="<main>", params=None):
        self.code = CodeObject(name, params)
        self.loops = []

    # --- helpers ----------------------------------------------------------

    def emit(self, op, arg=None):
        return self.code.emit(op, arg)

    def const(self, value):
        return self.code.add_const(value)

    def load_const(self, value):
        self.emit(O.LOAD_CONST, self.const(value))

    def here(self):
        return len(self.code.code)

    def patch(self, idx, target=None):
        if target is None:
            target = self.here()
        self.code.code[idx][1] = target

    # --- public entry -----------------------------------------------------

    def compile_program(self, block):
        for stmt in block.statements:
            self.statement(stmt)
        self.load_const(None)
        self.emit(O.RETURN)
        return self.code

    # --- statements -------------------------------------------------------

    def statement(self, node):
        method = getattr(self, "stmt_" + type(node).__name__, None)
        if method is None:
            raise BadaSyntaxError(f"cannot compile statement {type(node).__name__}", node.line)
        method(node)

    def stmt_LetStmt(self, node):
        self.expression(node.value)
        self.emit(O.DECLARE_NAME, self.const(node.name))

    def stmt_ExprStmt(self, node):
        self.expression(node.expr)
        self.emit(O.POP)

    def stmt_PrintStmt(self, node):
        for arg in node.args:
            self.expression(arg)
        self.emit(O.PRINT, len(node.args))

    def stmt_Block(self, node):
        for stmt in node.statements:
            self.statement(stmt)

    def stmt_IfStmt(self, node):
        end_jumps = []
        for cond, body in node.branches:
            self.expression(cond)
            skip = self.emit(O.JUMP_IF_FALSE)
            self.stmt_Block(body)
            end_jumps.append(self.emit(O.JUMP))
            self.patch(skip)
        if node.else_block is not None:
            self.stmt_Block(node.else_block)
        for j in end_jumps:
            self.patch(j)

    def stmt_WhileStmt(self, node):
        loop = LoopContext()
        self.loops.append(loop)
        start = self.here()
        loop.continue_target = start
        self.expression(node.cond)
        exit_jump = self.emit(O.JUMP_IF_FALSE)
        self.stmt_Block(node.body)
        self.emit(O.JUMP, start)
        self.patch(exit_jump)
        for b in loop.breaks:
            self.patch(b)
        self.loops.pop()

    def stmt_ForStmt(self, node):
        # for VAR in ITER { body }
        self.expression(node.iterable)
        self.emit(O.GET_ITER)
        loop = LoopContext()
        self.loops.append(loop)
        start = self.here()
        loop.continue_target = start
        for_iter = self.emit(O.FOR_ITER)   # pushes next value or jumps to end
        self.emit(O.DECLARE_NAME, self.const(node.var))
        self.stmt_Block(node.body)
        self.emit(O.JUMP, start)
        self.patch(for_iter)               # FOR_ITER jumps here when exhausted
        self.emit(O.POP)                   # pop the iterator
        for b in loop.breaks:
            self.patch(b)
        self.loops.pop()

    def stmt_ReturnStmt(self, node):
        if node.value is not None:
            self.expression(node.value)
        else:
            self.load_const(None)
        self.emit(O.RETURN)

    def stmt_BreakStmt(self, node):
        if not self.loops:
            raise BadaSyntaxError("'break' outside loop", node.line)
        self.loops[-1].breaks.append(self.emit(O.JUMP))

    def stmt_ContinueStmt(self, node):
        if not self.loops:
            raise BadaSyntaxError("'continue' outside loop", node.line)
        self.emit(O.JUMP, self.loops[-1].continue_target)

    def stmt_ImportStmt(self, node):
        bind = node.alias or node.path[-1]
        self.emit(O.IMPORT_MODULE, self.const(tuple(node.path)))
        self.emit(O.DECLARE_NAME, self.const(bind))

    def stmt_ThrowStmt(self, node):
        self.expression(node.value)
        self.emit(O.THROW)

    def stmt_TryStmt(self, node):
        # SETUP_TRY records (catch_ip, finally_ip); a finally section always
        # exists (it may be empty) to simplify the unwinding protocol.
        setup = self.emit(O.SETUP_TRY, None)

        # --- try body ---
        self.stmt_Block(node.try_block)
        self.emit(O.POP_BLOCK)
        jump_to_finally_normal = self.emit(O.JUMP)

        # --- catch body (VM jumps here with the exception value on the stack) ---
        catch_ip = self.here()
        if node.catch_block is not None:
            if node.catch_var is not None:
                self.emit(O.DECLARE_NAME, self.const(node.catch_var))
            else:
                self.emit(O.POP)
            self.stmt_Block(node.catch_block)
            self.emit(O.POP_BLOCK)   # drop the finally-only handler
            jump_after_catch = self.emit(O.JUMP)
        else:
            # no catch clause: discard the pushed value, fall through to reraise
            self.emit(O.POP)
            jump_after_catch = None

        # --- finally (exceptional path): run, then re-raise ---
        finally_ip = self.here()
        if node.finally_block is not None:
            self.stmt_Block(node.finally_block)
        self.emit(O.RERAISE)

        # --- finally (normal / caught path) ---
        normal_finally = self.here()
        self.patch(jump_to_finally_normal, normal_finally)
        if jump_after_catch is not None:
            self.patch(jump_after_catch, normal_finally)
        if node.finally_block is not None:
            self.stmt_Block(node.finally_block)

        # patch SETUP_TRY argument with (catch_ip, finally_ip)
        target_catch = catch_ip if node.catch_block is not None else None
        self.code.code[setup][1] = self.const((target_catch, finally_ip))

    def stmt_FuncDecl(self, node):
        sub = Compiler(node.name, node.params)
        sub.compile_function_body(node.body)
        self.emit(O.MAKE_FUNCTION, self.const(sub.code))
        self.emit(O.DECLARE_NAME, self.const(node.name))

    def stmt_ClassDecl(self, node):
        fields = []
        for f in node.fields:
            default_code = None
            if f.default is not None:
                fc = Compiler(f"{node.name}.{f.name}.default", [])
                fc.expression(f.default)
                fc.emit(O.RETURN)
                default_code = fc.code
            fields.append((f.name, default_code))

        methods = []
        for m in node.methods:
            # `self` is supplied implicitly by the VM via LOAD_SELF, so it is
            # not part of the declared parameter list.
            mc = Compiler(f"{node.name}.{m.name}", list(m.params))
            mc.compile_function_body(m.body)
            methods.append((m.name, mc.code, m.is_static))

        descriptor = ClassDescriptor(node.name, node.parent, fields, methods)
        self.emit(O.BUILD_CLASS, self.const(descriptor))
        self.emit(O.DECLARE_NAME, self.const(node.name))

    # --- function bodies --------------------------------------------------

    def compile_function_body(self, block):
        for stmt in block.statements:
            self.statement(stmt)
        self.load_const(None)
        self.emit(O.RETURN)

    # --- expressions ------------------------------------------------------

    def expression(self, node):
        method = getattr(self, "expr_" + type(node).__name__, None)
        if method is None:
            raise BadaSyntaxError(f"cannot compile expression {type(node).__name__}", node.line)
        method(node)

    def expr_Literal(self, node):
        self.load_const(node.value)

    def expr_Identifier(self, node):
        self.emit(O.LOAD_NAME, self.const(node.name))

    def expr_SelfExpr(self, node):
        self.emit(O.LOAD_SELF)

    def expr_ListLit(self, node):
        for el in node.elements:
            self.expression(el)
        self.emit(O.BUILD_LIST, len(node.elements))

    def expr_MapLit(self, node):
        for k, v in node.pairs:
            self.expression(k)
            self.expression(v)
        self.emit(O.BUILD_MAP, len(node.pairs))

    def expr_Attribute(self, node):
        self.expression(node.obj)
        self.emit(O.LOAD_ATTR, self.const(node.name))

    def expr_Index(self, node):
        self.expression(node.obj)
        self.expression(node.index)
        self.emit(O.LOAD_INDEX)

    def expr_Call(self, node):
        self.expression(node.callee)
        for arg in node.args:
            self.expression(arg)
        self.emit(O.CALL, len(node.args))

    def expr_SuperCall(self, node):
        self.emit(O.LOAD_SUPER_METHOD, self.const(node.method))
        for arg in node.args:
            self.expression(arg)
        self.emit(O.CALL, len(node.args))

    def expr_Unary(self, node):
        self.expression(node.operand)
        self.emit(O.UNARY_OP, self.const(node.op))

    def expr_Binary(self, node):
        self.expression(node.left)
        self.expression(node.right)
        self.emit(O.BINARY_OP, self.const(node.op))

    def expr_Logical(self, node):
        self.expression(node.left)
        if node.op == "and":
            self.emit(O.DUP)
            jump = self.emit(O.JUMP_IF_FALSE)
            self.emit(O.POP)
            self.expression(node.right)
            self.patch(jump)
        else:  # or
            self.emit(O.DUP)
            jump = self.emit(O.JUMP_IF_TRUE)
            self.emit(O.POP)
            self.expression(node.right)
            self.patch(jump)

    def expr_Assign(self, node):
        # All STORE_* ops leave the assigned value on the stack so that
        # assignment is itself an expression.
        target = node.target
        if isinstance(target, N.Identifier):
            self.expression(node.value)
            self.emit(O.STORE_NAME, self.const(target.name))
        elif isinstance(target, N.Attribute):
            self.expression(target.obj)
            self.expression(node.value)
            self.emit(O.STORE_ATTR, self.const(target.name))
        elif isinstance(target, N.Index):
            self.expression(target.obj)
            self.expression(target.index)
            self.expression(node.value)
            self.emit(O.STORE_INDEX)
        else:
            raise BadaSyntaxError("invalid assignment target", node.line)


def compile_source(source, filename="<bada>"):
    from .parser import parse
    from .reviser import Reviser
    # The reviser rewrites the source text (grammar / lexer) before parsing.
    revised, rules = Reviser.process(source)
    ast = parse(revised, filename)
    code = Compiler("<main>").compile_program(ast)
    code.reviser_rules = rules
    return code
