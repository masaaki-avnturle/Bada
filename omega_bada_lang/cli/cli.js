/* cli.js — Bada command-line compiler & interpreter (bundled after bada.js).
 * In the SEA bundle, bada.js has already run and set globalThis.Bada.
 *
 *   bada run  prog.bada     tree-walking interpreter (default)
 *   bada vm   prog.bada     compile to bytecode and run on the stack VM
 *   bada dis  prog.bada     print the compiled bytecode (disassembly)
 *   bada qasm prog.bada     run and print the lowered OpenQASM 2.0 circuit
 *   bada check prog.bada    verify the interpreter and the VM agree
 *   bada version
 *   echo 'print 2+2' | bada run -
 */
(function () {
  "use strict";
  var fs = require("fs");
  var Bada = globalThis.Bada;
  var argv = process.argv.slice(process.argv[0] && /node|bada/i.test(process.argv[0]) ? 2 : 1);
  // In a SEA binary argv is [exe, cmd, file]; slice(2) works the same as node.
  argv = process.argv.slice(2);
  var cmd = argv[0] || "run";
  var file = argv[1];

  function read(p) { return p === "-" ? fs.readFileSync(0, "utf8") : fs.readFileSync(p, "utf8"); }
  function usage() {
    process.stderr.write(
      "Bada " + Bada.VERSION + " — command-line compiler & interpreter\n" +
      "usage: bada <run|vm|dis|qasm|check|version> <file.bada|->\n" +
      "  run   tree-walking interpreter (default)\n" +
      "  vm    compile to bytecode and run on the stack VM\n" +
      "  dis   print the compiled bytecode (disassembly)\n" +
      "  qasm  run and print the lowered OpenQASM 2.0 circuit\n" +
      "  check verify the interpreter and the VM produce the same output\n");
  }
  if (cmd === "version" || cmd === "-v" || cmd === "--version") { process.stdout.write("bada " + Bada.VERSION + "\n"); return; }
  if (cmd === "help" || cmd === "-h" || cmd === "--help") { usage(); return; }
  if (!file) { usage(); process.exit(2); }

  try {
    var src = read(file);
    if (cmd === "run") { Bada.interpret(src).output.forEach(function (l) { console.log(l); }); }
    else if (cmd === "vm") { Bada.execVM(src).output.forEach(function (l) { console.log(l); }); }
    else if (cmd === "dis") { console.log(Bada.disassemble(src)); }
    else if (cmd === "qasm") { var r = Bada.interpret(src); console.log(r.qubits > 0 ? r.qasm : "; (no quantum instructions in this program)"); }
    else if (cmd === "check") {
      var a = Bada.interpret(src).output, b = Bada.execVM(src).output;
      var same = JSON.stringify(a) === JSON.stringify(b);
      console.log(same ? "OK: interpreter and VM agree (" + a.length + " lines)" : "MISMATCH");
      process.exit(same ? 0 : 1);
    } else { process.stderr.write("unknown command: " + cmd + "\n"); usage(); process.exit(2); }
  } catch (e) { process.stderr.write((e && e.message ? e.message : String(e)) + "\n"); process.exit(1); }
})();
