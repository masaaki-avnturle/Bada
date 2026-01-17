#!/usr/bin/env python3
# omega-proof.py
# Small utility to demonstrate symbolic/safe arithmetic handling.
# If sympy is available it will be used; otherwise a limited safe evaluator is used.
# This script is intended for education/visualization only.

from __future__ import annotations
import sys
import ast
import operator as op

# Try to import sympy; set flag accordingly
try:
    import sympy as sp
    SYMPY = True
except Exception:
    SYMPY = False

# Allowed operators mapping for safe evaluator
_ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
}

def safe_eval_expr(expr: str):
    """
    Safely evaluate a numeric expression consisting only of numbers and
    + - * / ** % // unary ops and parentheses.
    Returns a Python numeric result (int/float).
    Raises ValueError on disallowed constructs.
    """
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Num):  # type: ignore[attr-defined]
            return node.n  # type: ignore[attr-defined]
        if isinstance(node, ast.Constant):  # Python 3.8+: numbers arrive as Constant
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants are allowed")
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_OPERATORS:
                raise ValueError(f"Operator {op_type} not allowed")
            left = _eval(node.left)
            right = _eval(node.right)
            return _ALLOWED_OPERATORS[op_type](left, right)
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_OPERATORS:
                raise ValueError(f"Unary operator {op_type} not allowed")
            operand = _eval(node.operand)
            return _ALLOWED_OPERATORS[op_type](operand)
        if isinstance(node, ast.Call):
            raise ValueError("Function calls are not allowed in safe_eval")
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")

    parsed = ast.parse(expr, mode='eval')
    return _eval(parsed)

def show_with_sympy(expr: str):
    """
    Use sympy to parse and show manipulations.
    """
    x = sp.symbols  # quick alias (not used directly here but available)
    try:
        e = sp.sympify(expr)
    except Exception as exc:
        raise ValueError(f"SymPy failed to parse expression: {exc}")
    # Provide a few simple transformations for demonstration
    expanded = sp.expand(e)
    simplified = sp.simplify(e)
    latex_repr = sp.latex(e)
    return {
        "original": str(e),
        "expanded": str(expanded),
        "simplified": str(simplified),
        "latex": latex_repr,
    }

def print_usage():
    prog = sys.argv[0] if sys.argv else "omega-proof.py"
    print(f"Usage: {prog} <expression>")
    print("Example: ")
    print(f"  {prog} \"(1+2)*(3+4)\"")
    print("If SymPy is installed you get symbolic results (expand/simplify).")
    print("Otherwise a safe numeric evaluation will be attempted.")

def main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print_usage()
        return 2
    expr = " ".join(argv).strip()
    if not expr:
        print_usage()
        return 2

    print("Expression:", expr)
    if SYMPY:
        try:
            info = show_with_sympy(expr)
            print("SymPy detected. Results:")
            print("  original:  ", info["original"])
            print("  expanded:  ", info["expanded"])
            print("  simplified:", info["simplified"])
            print("  latex:     ", info["latex"])
            return 0
        except ValueError as e:
            print("SymPy parsing error:", e)
            # fall through to safe numeric attempt
    # Fallback: try safe numeric evaluation
    try:
        val = safe_eval_expr(expr)
        print("Numeric evaluation (safe):", val)
        return 0
    except Exception as e:
        print("Error: could not evaluate expression safely:", e)
        return 3

if __name__ == "__main__":
    sys.exit(main())
