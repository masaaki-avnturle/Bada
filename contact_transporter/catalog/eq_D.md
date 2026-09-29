# Equations D: bada-source-1 and bada-quantum-reviser-paper

Note: neither paper has numbered display equations. bada-source-1 is mostly a C source listing, so its "equations" are the README math plus the formulas the engine builtins implement. They are written out below from the C code. All CALC values were recomputed in Python and match the papers' printed outputs.

## bada-source-1 (Bada: The Unknown-Prior Engine Language, full source listing)
- S.1 | a = softmax(z) | base distribution over V tokens from logits | ENTROPY, QUANTUM | CALC: a_i = exp(z_i)/Σ_j exp(z_j)
- S.2 | ψ_i = √(a_i) · exp( i · Σ_m β_m H_m φ_m^(i) ) | entropy-phase cognitive core amplitude (×2: README, cognitive_system comment) | QUANTUM, ENTROPY | CALC: with S.21/S.22 inputs
- S.3 | q̂_i = |ψ_i|² / Σ_j |ψ_j|² | posterior from squared amplitude (×2) | QUANTUM | CALC: normalize |ψ|²
- S.4 | |e^{iθ}| = 1  ⇒  |ψ_i|² = a_i  (exactly) | unit-modulus phase preserves base probabilities (×3) | QUANTUM | SYMB
- S.5 | a_i = 0 ⇒ q̂_i = 0 | zero preservation, ruled-out tokens survive (×3) | QUANTUM | SYMB
- S.6 | max_i |q̂_i − a_i| = 5.55e-17 | property (ii) verified at machine precision (×3) | QUANTUM | CALC: 2^-54 = 5.551e-17 (half of 2^-53)
- S.7 | H(unknown_prior(8)) = 2.0794 → 1.9733 → 1.8364 | unknown-prior entropy strictly decreases (×2) | ENTROPY | CALC: ln 8=2.07944; p←norm(0.5p+0.5a) twice gives 1.97330, 1.83638
- S.8 | −p log p | entropic summand (legitimate shape) | ENTROPY | CALC: per-component Shannon term
- S.9 | e^{iθ} | Euler unit-modulus phase (native `phase` type) (×2) | QUANTUM | SYMB
- S.10 | unknown_prior(V)_i = 1/V | uniform max-entropy (Jaynes) prior | ENTROPY | CALC: 1/V; H = ln V
- S.11 | STAR ~ x = true;  x ~ y = (x == y) for num/str, else (type(x)==type(y)) | gradual-typing consistency operator | OTHER | SYMB
- S.12 | softmax(z)_i = exp(z_i − max_j z_j) / Σ_k exp(z_k − max_j z_j) | numerically stable softmax (interp + transpiler) (×2) | ENTROPY | CALC: shift by max, exp, normalize
- S.13 | z_i − max_j z_j < −30  ⇒  p_i := 0, then p ← p/Σp | confident-zero cutoff inside softmax (×2) | ENTROPY | CALC: threshold −30 in logit gap
- S.14 | H(p) = −Σ_i q_i ln q_i,  q_i = max(p_i, 1e-12) | Shannon entropy (nats) with floor clamp (×3: entropy, cognitive_system, b_entropy) | ENTROPY | CALC: sum with clamp
- S.15 | update(p, e, lr)_i = ((1−lr) p_i + lr e_i) / Σ_k ((1−lr) p_k + lr e_k),  lr default 0.5 | prior sharpening by evidence mixture (×2) | ENTROPY | CALC: convex mix then normalize
- S.16 | d_i = Σ_j W_ij x_j  (or d_i = x_i if no W);  d ← d / (‖d‖₂ + 1e-12) | manifold_embed: L2-normalized linear embedding | MANIFOLD | CALC: matvec then divide by norm
- S.17 | θ_i = Σ_m β_m · H(q_m) · φ_m[i],  β_m default 1, φ_m[i] default 0 | accumulated phase from module entropies | ENTROPY, QUANTUM | CALC: H from S.14 times β times φ
- S.18 | ψ_i = √(a_i)·cexp(iθ_i);  |ψ_i|² = Re(ψ_i)² + Im(ψ_i)² | how the C code evaluates the amplitude (×2) | QUANTUM | CALC: complex exp
- S.19 | p_i ← p_i / Σ_k p_k  (if Σ_k p_k > 0) | dist normalization (dist(arr), dist_normalize) | OTHER | CALC: divide by sum
- S.20 | maxdiff(a,b) = max_i |a_i − b_i| | L∞ distance used for property (ii) | OTHER | CALC: max abs diff
- S.21 | zeros_of(d) = { i : d_i = 0 } | index set of confident zeros | OTHER | CALC: filter p_i==0
- S.22 | z = [1.6, 0.6, 0.1, −40, −0.4, 1.1, −40, 0.4],  V = len(a) = 8,  zeros_of(a) = zeros_of(q̂) = [3, 6] | engine example logits, ruled-out tokens 3 and 6 (×2: engine.bada, core.bada) | ENTROPY | CALC: softmax gives a ≈ [0.37964,0.13966,0.08471,0,0.05138,0.23026,0,0.11435]
- S.23 | modules = [[q_ret,φ_ret],[q_syn,φ_syn],[uniform(8), 0.5·1]],  β = [0.7, 0.5, 0.9] | cognitive_system example modules and gains (×2) | ENTROPY, QUANTUM | CALC: H(q_ret)=1.66958, H(q_syn)=1.65002, H(uniform)=ln8=2.07944
- S.24 | θ_i = c (constant) ⇒ q̂ unchanged | uninformative constant-H modules cancel | QUANTUM, ENTROPY | SYMB
- S.25 | a/b = 0 if b = 0;  a % b = fmod(a,b), 0 if b = 0 | interpreter arithmetic conventions | OTHER | SYMB
- S.26 | softmax([2,1,0,−1]) ≈ [0.64391, 0.23688, 0.08714, 0.03206];  H(unknown_prior(4)) = ln 4 = 1.38629 | hello.bada sanity-check values | ENTROPY | CALC: softmax; update(prior,a) gives H ≈ 1.28026 < 1.38629

## bada-quantum-reviser-paper (Reviser-Extensible Grammars: a Q#-targeted quantum front end)
- Q.1 | a_i = softmax(z)_i | base distribution over V outcomes (×3: §2.1, App A, App C) | ENTROPY, QUANTUM | CALC: exp(z_i)/Σ exp(z_j)
- Q.2 | θ_i = Σ_m β_m · H_m · φ_m^(i) | accumulated phase from module entropies (×3) | QUANTUM, ENTROPY | CALC: weighted sum
- Q.3 | ψ_i = √(a_i) · exp(i·θ_i) | engine native phase value, i.e. the amplitude (×6: abstract, §1, §2.1, §4.1, App A, App C) | QUANTUM | CALC: complex exp
- Q.4 | q_i = |ψ_i|² / Σ_j |ψ_j|² = a_i | normalized posterior equals base (×2: §2.1, App C) | QUANTUM | CALC: normalize |ψ|²
- Q.5 | |exp(iθ)| = 1 | unit modulus of the phase factor (×2) | QUANTUM | SYMB
- Q.6 | |ψ|² = a | Theorem 2: phase step changes no probability, i.e. unitarity (×9) | QUANTUM | SYMB
- Q.7 | a_i = 0 ⇒ q_i = 0 | Theorem 1: zero-preservation, no-resurrection (×3) | QUANTUM | SYMB
- Q.8 | α_i = √(p_i) · e^{iφ_i} | Q# quantum amplitude of basis state i (×3: abstract, §2.2, App A) | QUANTUM | CALC: complex exp
- Q.9 | p_i ↔ a_i,  φ_i ↔ θ_i,  α_i ↔ ψ_i | quantum-to-engine correspondence dictionary (×2) | QUANTUM | SYMB
- Q.10 | P(outcome i) = |α_i|² = |ψ_i|² | Born rule as engine squared modulus (×3) | QUANTUM | CALC: square modulus
- Q.11 | V = 2^n | basis-state count for n-qubit register (×2: §4.1, §5 prepare_unknown(n)) | QUANTUM | CALC: 2^n
- Q.12 | H|0⟩ : a = [0.5, 0.5] | Hadamard as uniform distribution plus one phase module (×4) | QUANTUM | CALC: uniform over 2
- Q.13 | H ≡ cognitive_system(a, [[a, φ_H]], [β_H]),  a uniform | Hadamard denotation on engine core | QUANTUM | SYMB
- Q.14 | S, T, Rz(λ): θ ← θ + Δθ,  a unchanged | phase gates are pure phase contributions | QUANTUM | SYMB
- Q.15 | CNOT: (a, θ)_i ← (a, θ)_{π_c(i)} | control-conditioned basis-index permutation before the phase step | QUANTUM | SYMB
- Q.16 | max_i |q_i − a_i| = 1.11×10^-16 | Hadamard probe unitarity to machine precision (×5) | QUANTUM | CALC: 2^-53 = 1.1102e-16
- Q.17 | amplitudes² = [0.62246, 0.00000, 0.37754],  zeros = [1] | forbidden-transition probe, zero survives phase step | QUANTUM | CALC: softmax([0.5, −∞, 0]); 0.62246 = 1/(1+e^-0.5)
- Q.18 | rule := [ "rule", name, head, pattern, denotation ],  head ∈ {stmt, expr, postfix} | grammar production stored as a ledger fact (×2) | OTHER | SYMB
- Q.19 | unknown_prior(V)_i = 1/V;  prepare_unknown(n) = uniform over 2^n | maximum-entropy tomography starting prior | ENTROPY, QUANTUM | CALC: 2^-n
- Q.20 | H(prior_{k+1}) < H(prior_k) | entropy decreases monotonically as measurements commit | ENTROPY | SYMB
- Q.21 | estimate() = fold(update, unknown_prior(V), trace);  forbidden() = zeros_of(estimate()) | estimator folds over the commit trace | ENTROPY, QUANTUM | SYMB

Totals: bada-source-1 26 distinct items; quantum-reviser 21 distinct items; 47 distinct in all (about 85 including the repeats).

## Bada language syntax from papers

### Important framing
Neither paper defines a stand-alone quantum programming language. Bada is described as "a small object-oriented language whose runtime is the Unknown-Prior Engine" (an append-only tuple ledger, a maximum-entropy prior, and an entropy-phase core). The quantum part (`qubit`, `H`, `CNOT`, `Measure`, `S`, `T`, `Rz`) is only a design proposal: a sublanguage that `@reviser : grammar { rule ... }` blocks would add. The paper says so directly: "The reviser's grammar-extension front end is not yet wired into parser.c". Its probes call engine builtins directly instead.

### Lexical rules (from src/lexer.c in bada-source-1)
- Comments: `# ...` to end of line, and `// ...` to end of line.
- Whitespace, including newlines, has no meaning. Blocks use `{ ... }`, and `;` is an optional statement terminator.
- Numbers: `123`, `1.5`, `1e-3`, `2.5E+4`.
- Strings: `"..."` with the escapes `\n \t \" \\`.
- Identifiers: `[A-Za-z_@][A-Za-z0-9_]*` with an optional trailing `?` or `!`. `@reviser` is a keyword; any other `@name` is an identifier.
- Keywords: `Omega DATABASE tuplespace TupleSpace asperal struct def typedef return if else while for in static dynamic refine star true false nil let print each`. `do` and `end` are soft keywords, lexed as identifiers and recognised by the parser.
  - `let`, `static`, `dynamic` and `refine` are reserved, but the parser never uses them.
- Operators: `:=` (bind), `>>` (commit to ledger), `=>` or `->` (query/map), `:=>` (definitional arrow), `<-` (append to array), `~` (gradual consistency), `::` (scope), `|x, y|` (pipe params / lambda), `= == != < <= > >= + - * / % ! && || &`.

### Grammar (verbatim from the parser.c header comment)
```
 program   := decl*
 decl      := omegaDB | typedef | struct | func | stmt
 omegaDB   := 'Omega' '::' ('DATABASE'|'Tuplespace') ('[' IDENT ']')? block
 struct    := 'asperal' IDENT ':' 'struct' block
           |  'asperal' IDENT block
 typedef   := 'typedef' (':' qualname)? block
 func      := 'def' IDENT pipeparams? ('>>'|'=>'|':=>'|'{'|...) body
 pipeparams:= '|' (IDENT (',' IDENT)*)? '|'
 lambda    := pipeparams expr            (anonymous, used as call arg)
 stmt      := bind | assign | if | while | for | return | print | exprstmt
 bind      := IDENT ':=' expr
 expr      := commit
 commit    := query ('>>' query)*
 query     := assignment ('=>' assignment)*       (also '->')
```
Precedence, lowest first: `>>` and `<-`; `=>` and `->`; `||`; `&&`; `== != ~`; `< <= > >=`; `+ -`; `* / %`; unary `- !`; postfix (call `f(...)`, index `a[i]`, member `a.b`, method `a.b(...)`, scope `A::B`, `coll.each |x| do ... end`).

### Declarations and statements
- Binding: `x := expr`. Reassignment: `x = expr` or `a[i] = expr`. There is no `let` form.
- Functions: `def name(a, b) { ... }`, `def name |a, b| { ... }`, `def f |x| >> expr`, `def f |x| => expr`, `def f |x| :=> expr`, `def f(x) = expr`.
- Lambdas: `|x| expr` or `|x| do ... end`.
- Iteration: `coll.each |x| do ... end`.
- Control flow uses braces, not `end`, and the parentheses around the condition are optional:
  - `if cond { ... } else if cond { ... } else { ... }`
  - `while cond { ... }`
  - `for x in iterable { ... }`
- `return expr`.
- Print: `print(a, b, ...)` or `print a, b`. Arguments are printed space-separated.
- Objects and namespaces: `asperal Name :struct { ... }` (struct template; calling `Name()` makes an instance), `asperal |term| :=> { ... }` (gradual-type union, a no-op at runtime), `typedef [:qual] { ... }`, and `Omega::DATABASE[tuplespace] { ... }` (engine namespace block).
- Reviser: `@reviser <header up to '{'> { ... }`. Today it just runs the block, and the header is skipped.
- Ledger:
  - `x >> tuplespace` commits `x` and yields the right-hand side.
  - `tuplespace.append(v)`, `tuplespace.read()` / `.scan()`, `len(tuplespace)`.
  - `facts <- fact` appends to an array.
- Native types: `num`, `str`, `bool`, `nil`, array `[...]`, `dist`, `phase`, `tuplespace`, struct/instance, `func`/lambda, `star`.
- Builtins: `softmax entropy unknown_prior(V) update(prior,evidence[,lr]) manifold_embed(x[,W]) cognitive_system(base,modules,betas) dist zeros_of maxdiff last_a len sqrt log exp abs f5 sci ledger`.
- CLI: `bada run | build -o | emit -o | tokens | ast <file.bada>`.

### Proposed quantum / reviser-grammar syntax (quantum paper; design only, not implemented)
```
 @reviser : grammar {
    rule "hadamard"  postfix  [ 'H' '(' expr ')' ]
                     => phase_uniform(_1)
    rule "measure"   stmt     [ 'Measure' '(' expr ')' ]
                     => commit_measurement(_1)
}
```
```
 @reviser : grammar { ... quantum rules ... }
reg := qubit(1)          # |0>
reg := H(reg)            # uniform superposition
outcome := Measure(reg)  # commit |psi|^2 to the ledger
print("P(0), P(1) =", outcome)
```
Schema (Appendix B, verbatim):
```
 @reviser : grammar {
    rule NAME HEAD PATTERN => DENOTATION
    ...
}
rule        := [ "rule", name, head, pattern, denotation ]   (a ledger fact)
head        := 'stmt' | 'expr' | 'postfix'
pattern     := [ token-or-hole ... ]      ; holes are _1, _2, ...
denotation  := any Bada expression in the holes (typically an engine call)
parser extension points:
  primary  : before built-ins, try rules with head 'expr'
  postfix  : after a primary, try rules with head 'postfix'
  stmt     : before built-ins, try rules with head 'stmt'
resolution: highest priority first (latest commit wins), then ledger order;
scope:      a rule applies only to input following its committing reviser.
```
- Quantum names: `qubit(n)`, `H`, `S`, `T`, `Rz(λ)`, `CNOT`, `Measure(reg)`.
- Library `Omega::Quantum`: `prepare_unknown(n)`, `observe(reg)`, `estimate()`, `forbidden()`.
- AST node: `N_EXTENDED`. Its holes `_1, _2, ...` are bound in a fresh scope.

### Verbatim example programs (bada-source-1)
hello.bada:
```
# hello.bada -- basic sanity check of the Bada language.
print("Bada online.")
# native dist type via max-entropy prior
prior := unknown_prior(4)
print("uniform prior:", prior)
print("entropy(uniform) =", entropy(prior))
# softmax over logits -> dist
a := softmax([2.0, 1.0, 0.0, -1.0])
print("softmax:", a)
# sharpen the prior with evidence; entropy must drop
post := update(prior, a)
print("post:", post)
print("entropy(post) =", entropy(post))
# the append-only ledger
prior >> tuplespace
print("ledger facts:", len(tuplespace))
```
engine.bada (excerpt: core, for loop, reviser):
```
z := [1.6, 0.6, 0.1, -40.0, -0.4, 1.1, -40.0, 0.4]
a := softmax(z)
V := len(a)
modules := [ retrieval, syntax, uninformed ]
betas   := [ 0.7, 0.5, 0.9 ]
q_hat := cognitive_system(a, modules, betas)
for i in z {
    # i ranges over logits' values via dist iteration; recompute index below
}
print("3 :", f5(a[3]), f5(q_hat[3]), "  <-- ruled out")
print("  base zeros     =", zeros_of(a))
print("  ", sci(maxdiff(q_hat, last_a())), "(machine-zero => phase only reweights)")
prior := unknown_prior(V)
@reviser {
    prior := update(prior, q_hat)
    prior >> tuplespace
}
```
The compiler subset (`bada build`, core.bada) covers only `:=`, `=` on identifiers, `print`, arrays, indexing, `+ - * /` and `< >`, `if`/`else`, `>>`, and the builtins `softmax entropy unknown_prior dist len sqrt log exp ledger update cognitive_system .append`. `def`, `asperal` and `struct` are emitted as C comments. `while`, `for` and `each` are not lowered: they fall to the default expression path, which emits nothing useful.

### Comparison with /home/user/Bada/bada_c/bada.c (711 lines, "bada-c 0.1.0")
bada.c is a different dialect. It is not the paper's lexer.c/parser.c/interp.c. It is a cons-list, homoiconic, Ruby-like language:
- Blocks end with `end`, and newlines are significant.
- Keywords: `let def end if elsif else while print return true false nil and or not`.
- Comments: `#` only.
- Operators: `+ - * / == != < <= > >= = . ( ) [ ] ,` plus the directive operators `<-` (assign), `-<` (branch) and `>-` (merge). `%` and `;` are not lexed.
- Builtins: `list car cdr cons at len append str directive lanes cfn cint cstr gamma beta xlogx element zeta_gauge entropy xi thermal exp log sqrt sin cos pow mod floor abs pi class new method send get_slot set_slot class_name read_file write_file`.
- CLI: `run | build -o | eval | repl | version`.

I checked each form with `./bada eval`. Runs in bada.c:
- `let x = 3` and bare `x = 3`.
- `def f(x) ... return ... end` and anonymous `def(x) ... end`.
- `if ... elsif ... else ... end` and `while ... end`.
- `print x` and `print("a")` (the parentheses are just grouping).
- `[1,2,3]` literals; `list(...)` and `at(list, i)` (0-based).
- `and`, `or`, `not`; string `+` concatenation; `obj.method()` via `send`.

Paper syntax that fails in bada.c:
- `:=` fails with "Bada lex: unexpected ':'", so every paper example fails at its first binding.
- `print("a", 1)` with several arguments fails with "expected ')'".
- `>>` commit, `tuplespace`, `Omega::DATABASE`, `@reviser` ("unexpected '@'"), and `asperal`/`struct`/`typedef` are all missing.
- Brace blocks fail: `if c { }`, `while c { }` and `for x in xs { }` give "unexpected '{'". bada.c has no `for` loop at all.
- `// comments`, `%` and `;` are not supported.
- Lambdas `|x| expr` and `.each |x| do ... end` are not supported.
- Engine builtins `softmax unknown_prior update cognitive_system manifold_embed zeros_of maxdiff last_a f5 sci dist ledger` are all "undefined".
- The quantum forms `qubit`, `H`, `CNOT` and `Measure` exist in neither the paper's reference nor bada.c.

Semantic differences for shared names:
- `entropy` in bada.c uses log2 (bits). The paper uses natural log: `entropy([0.5,0.5])` is 1 in bada.c and 0.693 in the paper.
- `<-` means directive assign in bada.c and array append in the paper.

bada.c adds math that the papers do not have:
- `gamma = tgamma`, `beta(p,q) = Γ(p)Γ(q)/Γ(p+q)`, `xlogx`.
- `element(x) = 1/(x ln x)^2` for x > 1, else 1.
- `zeta_gauge(p,q,x) = B(p,q)/ln x`.
- `xi(ps) = B(H₂+1, m+1)/ln(N+1)` with `m = Σ p_i·element(i+2)`.
- `thermal(w) = xi(w/Σw)`.

Checked values: `beta(2,3) = 0.0833333`, `xi([0.5,0.25,0.25]) = 0.185528`, `thermal(list(18,5,4)) = 0.191576`.

Only the shared core runs in both: identifiers, numbers, strings, `[ ]` arrays, calls, arithmetic and comparison, `if`/`else`/`while`/`return`/`def` keywords, and single-argument `print(...)`. Even there the block syntax differs: braces in the paper, `end` in bada.c.
