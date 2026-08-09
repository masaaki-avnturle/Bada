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
  "nested_calls": 'fn sq(x){ return x*x }\nprint sq(sq(3))',
  "arrays": 'set a = [1, 2, 3, 4]\nprint a\nprint a[0] + a[3]\nprint len(a)\npush(a, 99)\nprint a\nprint a[-1]',
  "array_index_assign": 'set a = [10, 20, 30]\na[1] = 200\nprint a\nprint a[1]',
  "objects": 'set o = { name: "bada", n: 4 }\nprint o.name\nprint o["n"]\no.n = 5\nprint o.n\nprint keys(o)\nprint has(o, "name")',
  "object_in_array": 'set xs = [ {v: 1}, {v: 2}, {v: 3} ]\nset s = 0\nset i = 0\nwhile i < len(xs) { s = s + xs[i].v\ni = i + 1 }\nprint "sum = " + s',
  "range_sum": 'set r = range(5)\nset s = 0\nset i = 0\nwhile i < len(r) { s = s + r[i]\ni = i + 1 }\nprint r\nprint s',
  "nested_struct": 'set db = { users: ["alice", "bob"], count: 2 }\nprint db.users[1]\nprint db.count\ndb.count = db.count + 1\nprint db.count'
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

/* Arrays & objects: specific outputs. */
console.log("== arrays & objects ==");
check("array literal + index", Bada.interpret('set a=[5,6,7]\nprint a[0]+a[2]').output[0] === "12");
check("array show", Bada.interpret('print [1,2,3]').output[0] === "[1, 2, 3]");
check("array negative index", Bada.interpret('print [1,2,3][-1]').output[0] === "3");
check("push mutates", Bada.interpret('set a=[1]\npush(a,2)\npush(a,3)\nprint len(a)').output[0] === "3");
check("index assign", Bada.interpret('set a=[1,2,3]\na[1]=9\nprint a').output[0] === "[1, 9, 3]");
check("object member", Bada.interpret('set o={x:1,y:2}\nprint o.x + o.y').output[0] === "3");
check("object bracket + assign", Bada.interpret('set o={x:1}\no["y"]=2\nprint o["y"]').output[0] === "2");
check("object show", Bada.interpret('print {a:1,b:2}').output[0] === "{a: 1, b: 2}");
check("keys", Bada.interpret('print keys({a:1,b:2,c:3})').output[0] === "[a, b, c]");
check("nested obj/array", Bada.interpret('set d={xs:[10,20,30]}\nprint d.xs[2]').output[0] === "30");
check("VM arrays == interp", eq(Bada.interpret(PROGRAMS.array_index_assign).output, Bada.execVM(PROGRAMS.array_index_assign).output));
check("VM objects == interp", eq(Bada.interpret(PROGRAMS.nested_struct).output, Bada.execVM(PROGRAMS.nested_struct).output));

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

/* USB resume engine (bada usb). */
console.log("== usb resume ==");
require("./cli/usb.js");
var U = Bada.usb._test;
[2, 8, 10, 16].forEach(function (base) {
  var t = U.defaultDescriptor(0x0781, 0x5581);
  var r = U.recoverAdaptive(t, base, 9, 193, 0.35, 7);
  check("usb base-" + base + " recovers descriptor", r.checksumOk && r.bitOut === 0);
});
(function () {
  var faulted = U.syntheticFleet()[2];
  check("faulted device starts UNAUTHORIZED", Bada.usb.statusOf(faulted) === "UNAUTHORIZED");
  var res = Bada.usb.resume(faulted, { base: 16, apply: false });
  check("usb resume brings device to RESUMED", res.resumed && res.after === "RESUMED");
  check("usb resume is simulation (no sysfs write)", res.applied === false);
})();

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
