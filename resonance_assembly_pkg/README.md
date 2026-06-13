# resonance_assembly_pkg — 共鳴振動・組立精度・破壊力学ダイアログ

**Bada language (C port)** for resonance-driven **assembly-precision tuning**
in **durability / fracture mechanics**.

A dialog-box (terminal) application that, for a target structure (e.g. a
building frame), takes a **resonance / excitation frequency** and computes the
**assembly-precision adjustment** that keeps the structure off resonance and
safe against fracture — framed in the Yamaguchi / TupleSpace vocabulary the
rest of this repository uses (`Bada::Special`, `Bada::Manifold`,
`Bada::ErrorCorrection`), and implemented in **pure C11 + libm**.

> 姉の許可済み — authorized durability-diagnosis tool.

---

## Build & run

```sh
make            # -> bin/resonance_dialog  (and lib/libbada_resonance.a)
make demo       # non-interactive walkthrough on the default target
./bin/resonance_dialog          # interactive dialog
./bin/resonance_dialog --demo   # same as `make demo`
```

Only `gcc` and `libm` are required.

## Dialog menu

```
1) データ表示      Show target data
2) データ編集      Edit data (field by field — alternately correctable, 交互)
3) 診断実行        Run full diagnosis, then optionally apply the AGM target
                   stiffness and re-run (the back-and-forth correction loop)
4) デフォルト読込  Load the default target
0) 終了            Quit
```

`Enter` keeps the current value of a field; `^D` (EOF) stops editing. Because
every field can be re-entered any number of rounds, and the diagnosis can feed
its AGM target stiffness back into the data, the data is **交互に修正できる**
— alternately correctable.

---

## The five computation blocks

The request maps onto five coupled blocks (each is a section of the dialog):

### 1. Resonance diagnosis — 共鳴診断
The structure is an `N`-storey shear model with equal storey mass `m` and
storey stiffness `k`. Its **modal (natural) frequencies** are the roots of the
tridiagonal secular polynomial:

```
omega_j = 2 sqrt(k/m) · sin( (2j-1)π / (2(2N+1)) ),   j = 1..N
```

The mode nearest the (relativistically corrected) excitation frequency is the
**dangerous mode**. Resonance amplification uses the dynamic amplification
factor with `r = f_exc / f_mode` and damping `ζ`:

```
DAF = 1 / sqrt( (1-r²)² + (2ζr)² ),    σ_dyn = DAF · σ_static
```

### 2. Fracture mechanics / durability — 破壊力学・耐久診断
Linear-elastic fracture mechanics on the dynamic stress:

```
K_I    = Y · σ_dyn · sqrt(π a)
a_crit = (1/π) · ( K_IC / (Y σ_dyn) )²
SF     = K_IC / K_I
```

The verdict is **SAFE** when `SF ≥ 1` and `r` is at least 15 % away from
resonance.

### 3. Assembly-precision adjustment via AGM — 相加相乗平均
To detune the dangerous mode to a safe ratio `r*`, the required stiffness is
`k_target = k · (f_exc/r* / f_mode)²`. Two candidates — the **arithmetic mean**
(相加平均) and the **geometric mean** (相乗平均) of `k` and `k_target` — are
blended with the **arithmetic-geometric mean** (`agm`) into a stable target
`k_AGM`. The relative stiffness change is translated into a **member-dimension
tolerance** through the second-moment relation `I ∝ h³` (so `Δk/k ≈ 3·Δh/h`):

```
k_AGM = AGM( (k+k_target)/2 , sqrt(k·k_target) )
Δh    = (h/3) · (k_AGM - k)/k        # required assembly precision adjustment (mm)
```

### 4. Special-relativity error correction of a complex rotating body — 複素回転体
For a body spinning at `Ω` (rad/s) at radius `R`, the tangential speed gives a
Lorentz factor `γ = 1/sqrt(1 - (ΩR/c)²)`. The frequency read in the rotating
frame is dilated, so the **proper** excitation frequency is `f_proper = γ·f_obs`,
and this corrected value drives block 1. The rotation itself is carried by the
complex phasor `e^{iΩt}` (magnitude-preserving — the `Bada::ErrorCorrection`
spinning-top invariant). For real structures `β ≈ 10⁻⁶`, so the correction is
tiny but reported exactly.

### 5. Galois group / global differential manifold — ガロワ群・大域微分多様体
The **Galois group** of the secular polynomial permutes the modal roots; its
elementary symmetric functions — `Σ ωⱼ²` (trace) and `Π ωⱼ²` (det) — are the
**Galois-invariants**, reported as a conserved gauge. The modal energies are
turned into a measure on the **global partial integral manifold**
`dμ = 1/(x log x)²` and read through the zeta gauge `ζ = β(p,q)/log x` to give
the manifold invariant `Ξ`. The three README Bada operators are exposed as C
functions and shown live:

| Bada | C function | meaning |
|:----:|:-----------|:--------|
| `<-` | `bada_op_left(χ,x)`  | `π(χ,x) = [iπ, f(x)]` non-commutative left |
| `-<` | `bada_op_mid(x)`     | manifold element `1/(x log x)²` |
| `>-` | `bada_op_right(x)`   | `⊕(iℏ∇)^L = e^{-x log x}` quantum right |

---

## Files

| path | contents |
|:-----|:---------|
| `include/bada_resonance.h` | engine API: Bada special functions, operators, AGM, modal spectrum, relativistic correction, diagnosis |
| `lib/bada_resonance.c`     | engine implementation |
| `bin/resonance_dialog.c`   | the terminal dialog-box application |
| `Makefile`                 | `make`, `make demo`, `make clean` |

---

*This is a modelling / diagnostic aid for authorized durability analysis. It
uses standard SDOF/shear-model dynamics and linear-elastic fracture mechanics;
validate against a full FE model and the governing code before acting on any
result.*

© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research
