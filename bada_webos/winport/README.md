# WinPort — Windows → Quantum, via the Reviser

Generate **Ruby on Rails** source in **Bada**, rewrite **Windows 10 → Windows
11** (and **Windows → quantum computer**) with the **Reviser**, expose a
**hardware control panel via symbolic + hard links**, and **bridge a VM to the
quantum substrate with a repeater** — all as a BadaWebOS application.

## Pieces
| module | role |
|:--|:--|
| `apps/winport/lib/rails.bada` | **Rails generator written in Bada** — model, RESTful controller, routes, migration (a functioning scaffold). |
| `reviser_rules.py` | the **Reviser** rule-sets: `Win10 → Win11` (ControlPanel→Settings, Cortana→Copilot, DirectX11→DirectX12, …) and `Windows → quantum` (CPU→QPU, bit→qubit, register→qregister, RAM→QRAM, …); word-boundary, text-preserving. |
| `control_panel.py` | **hardware control panel** built from real **symbolic links** (panel entry → device file) and **hard links** (one shared driver-config inode), sandboxed under a temp root. |
| `quantum_port.py` | **port each Windows feature to the quantum computer** via the Reviser, protecting the ported register with the **Shor 9-qubit code**. |
| `vm_bridge.py` | **VM bridge + repeater** — migrates the ported VM across `win_vm → bridge → repeater → quantum` (the repeater re-amplifies so it arrives). |
| `app.py` | `WinPortApp` integrates all of the above; desktop window. |

## Usage (terminal)
```bash
winport            # boot summary
winport rails Article title body   # generate Rails source in Bada
winport win11      # Windows 10 -> Windows 11 rewrite (reviser)
winport port       # port Windows features to the quantum computer + Shor-9
winport bridge     # migrate the VM to the quantum node via bridge+repeater
```

### Example
```
winport port
kernel: Windows11 kernel: QPU amplitude_scheduler, qubit, qregister,
        entangled_cache, QRAM, qubit quantum_gate, superposed_process model
        [Shor-9 ok]
...
winport bridge
delivered to quantum: True (strength 0.648)
```

## Verified
- Rails: generates `class Article < ApplicationRecord`, a 7-action controller,
  `resources :Articles`, and a migration.
- Reviser: Win10→Win11 and Win→quantum token maps applied (unmapped words kept).
- Control panel: entries are real symlinks resolving to device files; the
  shared config is hard-linked (all entries share one inode).
- Quantum port: every feature ported, Shor-9 fidelity ≈ 1.0.
- VM bridge: the image reaches the `quantum` node; the repeater boosts delivery.
