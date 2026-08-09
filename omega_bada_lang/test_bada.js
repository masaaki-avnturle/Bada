/* Node test harness for bada.js — run: node www/test_bada.js
 * Differential test: the tree-walk INTERPRETER and the bytecode VM must agree. */
"use strict";
var Bada = require("./www/bada.js");
var pass = 0, fail = 0;
function eq(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
function check(name, cond) { if (cond) { pass++; } else { fail++; console.log("  ✗ " + name); } }
function near(a, b, t) { return Math.abs(a - b) <= (t || 1e-9); }

/* Programs that must produce identical output under interpret and execVM. */
var PROGRAMS = {
  "arithmetic": 'set a = 2 + 3 * 4\nprint a\nprint (2+3)*4\nprint 10 % 3\nprint 2 - 5',
  "strings": 'set s = "bada" + " " + "lang"\nprint s\nprint len(s)',
  "booleans": 'print 3 < 5 and 5 <= 5\nprint not (1 == 2)\nprint 0 or 7',
  "if_else": 'set x = 7\nif x > 10 { print "big" } else { print "small" }\nif x == 7 { print "seven" }',
  "while_sum": 'set i = 1\nset s = 0\nwhile i <= 5 { s = s + i\ni = i + 1 }\nprint s',
  "fn_recursion": 'fn fact(n) { if n <= 1 { return 1 }\nreturn n * fact(n - 1) }\nprint fact(5)\nprint fact(6)',
  "fn_fib": 'fn fib(n){ if n < 2 { return n }\nreturn fib(n-1)+fib(n-2) }\nprint fib(10)',
  "closures_global": 'set base = 100\nfn add(x){ return x + base }\nprint add(5)',
  "builtins_math": 'print sqrt(16)\nprint floor(3.9)\nprint pow(2,10)\nprint max(3,9,2)',
  "bada_ops": 'set g = 2.5\ng <- "global manifold"\nprint g\ng -< 3\nprint g\ng >- g\nprint g',
  "push": 'set g = 1.5\ng <- "entropy"\nOmega::push g as node1',
  "nested_calls": 'fn sq(x){ return x*x }\nprint sq(sq(3))'
};

console.log("== differential: interpret == execVM ==");
Object.keys(PROGRAMS).forEach(function (name) {
  var src = PROGRAMS[name], ri, rv;
  try { ri = Bada.interpret(src); } catch (e) { console.log("  ✗ " + name + " interpret threw: " + e.message); fail++; return; }
  try { rv = Bada.execVM(src); } catch (e) { console.log("  ✗ " + name + " execVM threw: " + e.message); fail++; return; }
  check(name + " (agree)", eq(ri.output, rv.output));
});

/* Specific expected outputs. */
console.log("== specific outputs ==");
check("fact(5)=120", Bada.interpret(PROGRAMS.fn_recursion).output[0] === "120");
check("fib(10)=55", Bada.interpret(PROGRAMS.fn_fib).output[0] === "55");
check("while sum 1..5 = 15", Bada.interpret(PROGRAMS.while_sum).output[0] === "15");
check("2+3*4=14", Bada.interpret('print 2+3*4').output[0] === "14");
check("(2+3)*4=20", Bada.interpret('print (2+3)*4').output[0] === "20");
check("string concat", Bada.interpret('print "a"+"b"+"c"').output[0] === "abc");
check("vm string concat", Bada.execVM('print "a"+"b"+"c"').output[0] === "abc");

/* Bada operators vs. direct formula. */
console.log("== Bada operator math ==");
var rt = Bada._rt;
check("<- = π|χ|ln(x+1)", near(rt.badaLeft(2.5, 3), Math.PI * 3 * Math.log(3.5)));
check(">- = e^{-x log x}", near(rt.badaRight(0, 2), Math.exp(-((2 + 1e-6) * Math.log(2 + 1e-6)))));
check("xi deterministic", near(rt.xiOf("hello world"), rt.xiOf("hello world")));

/* Quantum: Bell state H(0)+CNOT(0,1) → 00 and 11 each ~0.5. */
console.log("== quantum backend ==");
var bell = 'set q = qreg(2)\nh(q,0)\ncnot(q,0,1)\nprint probs(q)';
var rq = Bada.interpret(bell);
var probs = rq.output[0].split(" ").map(Number);
check("Bell |00> ~ 0.5", near(probs[0], 0.5, 1e-6));
check("Bell |01> ~ 0", near(probs[1], 0, 1e-6));
check("Bell |10> ~ 0", near(probs[2], 0, 1e-6));
check("Bell |11> ~ 0.5", near(probs[3], 0.5, 1e-6));
check("QASM has cx", rq.qasm.indexOf("cx q[0],q[1];") >= 0);
check("QASM has h", rq.qasm.indexOf("h q[0];") >= 0);
check("VM quantum agrees", eq(Bada.execVM(bell).output, rq.output));

/* Single qubit X gate → |1>. */
var xq = Bada.interpret('set q=qreg(1)\nx(q,0)\nprint probs(q)').output[0].split(" ").map(Number);
check("X|0> = |1>", near(xq[0], 0) && near(xq[1], 1));

/* Compiler produces bytecode with expected opcodes. */
console.log("== compiler ==");
var dis = Bada.disassemble('fn f(x){return x+1}\nprint f(2)');
check("bytecode has CALL", dis.indexOf("CALL") >= 0);
check("bytecode has RET", dis.indexOf("RET") >= 0);
check("bytecode has MKFUN", dis.indexOf("MKFUN") >= 0);

/* Error handling. */
console.log("== errors ==");
var threw = false; try { Bada.interpret('print (1 + '); } catch (e) { threw = e instanceof Bada.BadaError; }
check("parse error is BadaError", threw);

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
