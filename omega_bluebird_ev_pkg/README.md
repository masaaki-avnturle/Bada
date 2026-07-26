# omega_bluebird_ev_pkg — Bluebird EV 自動走行OS + Badaソースコード生成 (Bada language)

Bluebird 車体デザインの電気自動車のための、**自動走行オペレーティングシステムとしての
生成AI**を、量子コンピューターの **Bada言語** で記述した概念パッケージ。中核は、
**ガンマ関数における大域的部分積分多様体のエントロピー方程式**で駆動する
**Bada言語ソースコード自動生成機能**と、**熱エネルギー体の Jones 多項式**で駆動する
**周りの映像化（画像）**・**音の映像化（音声波形）**です。

> A generative-AI operating system for a Bluebird-styled electric car, written
> in the conceptual **Bada** language. Its headline feature is a **source-code
> generator**: it measures the entropy of the gamma-function *global
> partial-integral manifold* and synthesizes a Bada autonomous-driving policy
> from it, while the **Jones polynomial of the thermal-energy body** drives an
> environment **image** and an engine **sound**.

---

## ⚠️ 何が本物で、何がシミュレーションか — Real vs. simulation

House style of this repo = conceptual / simulation software. Be precise:

| Component | Status | Honest note |
|:--|:--|:--|
| **Entropy equation** (`manifold_entropy.c`) | **Real math** | Shannon `H`, Lanczos `Γ`, `∬ 1/(x log x)² dμ`, `Xi = β(H+1,M+1)/log(N+2)`. Genuinely computed. |
| **Source-code generation** (`codegen.c`) | **Real, but a small synthesizer** | A deterministic generative grammar *seeded* by `Xi` and the Jones invariant — same context → same source, different context → different valid Bada. It is **not** a trained large language model. |
| **Jones polynomial of thermal body** (`jones_thermal.c`) | **Real math, metaphorical mapping** | Kauffman-bracket state-sum is a true knot invariant; "battery/inverter heat flow = knot" is a modelling metaphor. |
| **Environment visualization** (`viz_env.c`) | **Real renderer** | Ordinary PPM rasterizer; `Xi`/`H` only modulate texture and lane cadence. |
| **Sound visualization** (`viz_sound.c`) | **Real synth** | Standard 16-bit PCM WAV additive synthesis; the Jones invariants pick the fundamental/timbre. |
| **Autonomous-driving kernel** (`badaev_os.c`) | **Real (small) controller** | `π-softmax` policy over driving actions — a simulated autopilot, **not** a validated safety system. |

**Do not put this in a real car.** The driving policy is illustrative; it has no
sensor stack, no validation, and no safety case.

---

## Build & run

```sh
make                 # builds bin/launcher
mkdir -p out
```

### Commands

```sh
# 1. the entropy equation of a percept file
./bin/launcher entropy   examples/road_scene.txt

# 2. GENERATE Bada driving source from that entropy (+ Jones thermal seed)
./bin/launcher codegen   examples/road_scene.txt out/policy.bada

# 3. 周りの映像化 — environment image (PPM) + ASCII map
./bin/launcher viz-env   examples/road_scene.txt out/env.ppm

# 4. 音の映像化 — engine sound (WAV) + ASCII spectrogram from Jones(thermal)
./bin/launcher viz-sound examples/thermal_body.knot 1.2 320 out/engine.wav

# 5. the OS control loop
./bin/launcher boot
```

`codegen` is deterministic: the same road/thermal context always regenerates
byte-identical Bada source, and a different context synthesizes a different but
valid program (different `v_cap`, `brake_d`, `steer_k`, rule order).

---

## 生成の流れ — Generative pipeline

```
percept file ──▶ gamma-manifold entropy  Xi = β(H+1,M+1)/log(N+2)
thermal knot ──▶ Jones(thermal body)     <D> · β(1+T, 1+1/T)
                        │
                        ▼
        codegen ──▶ Bada autopilot SOURCE (thresholds/gains/rules ← Xi, Jones)
        viz-env ──▶ surroundings IMAGE  (PPM,  texture ← Xi, H)
        viz-sound ▶ engine SOUND        (WAV,  partials ← Jones)
                        │
                        ▼
        badaev kernel ──▶ π-softmax drive action ──▶ Omega::push (Akashic)
```

`bada/bluebird_os.bada` is the Bada-language surface; `bada/generated_policy.bada`
is a captured sample of `codegen` output.

---

## File map

| File | Contents |
|:--|:--|
| `include/omega_bluebird.h` | types + API + honesty note |
| `lib/manifold_entropy.c` | gamma-manifold entropy equation (H, M, Xi) |
| `lib/jones_thermal.c` | Kauffman bracket + Γ global-partial thermal weight |
| `lib/codegen.c` | **Bada source-code generator** |
| `lib/viz_env.c` | environment visualization (PPM + ASCII) |
| `lib/viz_sound.c` | sound visualization (WAV + spectrogram) |
| `lib/badaev_os.c` | π-softmax OS kernel + Bluebird body design |
| `lib/omega_interp.c` | command interpreter |
| `bin/launcher.c` | entry point |
| `bada/bluebird_os.bada` | Bada-language OS program |
| `bada/generated_policy.bada` | sample generated source |
| `examples/road_scene.txt` | percept stream |
| `examples/thermal_body.knot` | thermal-flow knot diagram |

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research —
conceptual / simulation package.*
