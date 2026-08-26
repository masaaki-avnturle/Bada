"""
controller.py — 内部統制システム (Internally-Controlled Möbius-Drive System)
===========================================================================

3 つの部品を 1 つの閉ループ制御系に統合する：

    [擬似量子VM] --bits--> [メビビウス回路HDD] --polarity--> [反ダランベルシアン場]
          ^                                                        |
          |------------------ lift_index フィードバック -----------|

サイクル:
  1. 擬似量子VM が 1 ビットを生成（測定）
  2. そのビットをメビウス・ディスクに書き込み、ヘッドを 1 歩進める
     （境界で面が反転＝電子制御装置としての極性切替）
  3. ディスク面の極性を、反ダランベルシアン場の制御ソース S(x,t) に変換
  4. 場を 1 ステップ発展させ、lift_index（見かけの浮揚指標）を測る
  5. lift_index の符号を次サイクルの VM 位相にフィードバック（内部統制）

⚠️ 全体はシミュレーション／アート。反重力を発生させる実機ではなく、
   PC 内部で完結する数値モデルである。標準ライブラリのみで動作。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Dict

from .pseudo_quantum import PseudoQuantumVM
from .mobius_disk import MobiusDisk
from .dalembert import DAlembertField, FieldConfig


@dataclass
class Telemetry:
    cycle: int
    bit: int
    disk_head: int
    disk_face: int
    field_energy: float
    lift_index: float


class MobiusDriveSystem:
    """反重力発生器（シミュレーション）としての内部統制システム。"""

    def __init__(self, sectors: int = 64, field_cfg: FieldConfig | None = None,
                 seed: int = 0x9E3779B1) -> None:
        self.vm = PseudoQuantumVM(n_regs=4, seed=seed)
        self.disk = MobiusDisk(sectors=sectors)
        self.field = DAlembertField(field_cfg or FieldConfig(nx=96, dt=0.4))
        self.field.seed_gaussian(amp=0.5)
        self.log: List[Telemetry] = []
        self._feedback_phase = 0.0

    # ---- 1 サイクル ------------------------------------------------------ #
    def _cycle(self, cycle: int) -> Telemetry:
        # 1. 擬似量子VMで1ビット生成（フィードバック位相を注入）
        prog = [
            ("LOAD", 0, 0),
            ("H", 0),
            ("PHASE", 0, self._feedback_phase),
            ("MEASURE", 0),
            ("HALT",),
        ]
        self.vm.output = []
        self.vm.halted = False
        bit = self.vm.run(prog)[0]

        # 2. メビウス・ディスクへ書き込み、ヘッド前進（境界で面反転）
        self.disk.write(0xFF if bit else 0x00)
        self.disk.seek(max(1, self.disk.n // 8))  # 8サイクルで境界を跨ぐ設計

        # 3. ディスク面の極性 → 制御ソース S(x,t)
        face = self.disk.face
        head = self.disk.head
        x_inject = int((head / self.disk.n) * self.field.cfg.nx)

        def source_fn(i: int, t: float, _face=face, _x=x_inject) -> float:
            # 面の極性で符号が変わる局所ソース（メビウス回路の電子制御）
            return _face * math.cos(0.5 * t) if i == _x else 0.0

        # 4. 反ダランベルシアン場を1ステップ発展
        self.field.step(source_fn=source_fn)
        e = self.field.energy()
        lift = self.field.lift_index()

        # 5. lift_index の符号を次サイクルの位相へフィードバック（内部統制）
        self._feedback_phase = 0.3 * math.tanh(lift)

        tm = Telemetry(cycle, bit, head, face, e, lift)
        self.log.append(tm)
        return tm

    def run(self, cycles: int = 32) -> List[Telemetry]:
        for c in range(cycles):
            self._cycle(c)
        return self.log

    # ---- 診断 ------------------------------------------------------------ #
    def summary(self) -> Dict[str, float]:
        if not self.log:
            return {}
        lifts = [t.lift_index for t in self.log]
        energies = [t.field_energy for t in self.log]
        return {
            "cycles": len(self.log),
            "final_energy": energies[-1],
            "max_energy": max(energies),
            "mean_lift": sum(lifts) / len(lifts),
            "final_lift": lifts[-1],
            "disk_orientable_return": float(self.disk.is_orientable_return()),
            "stable": float(all(math.isfinite(e) for e in energies)),
        }

    def report(self) -> str:
        s = self.summary()
        lines = [
            "=== Möbius-Drive 内部統制システム レポート (シミュレーション) ===",
            f"サイクル数            : {int(s['cycles'])}",
            f"最終場エネルギー      : {s['final_energy']:.4f}",
            f"最大場エネルギー      : {s['max_energy']:.4f}",
            f"平均 lift_index      : {s['mean_lift']:.4e}",
            f"最終 lift_index      : {s['final_lift']:.4e}",
            f"ディスク面が表に復帰  : {'はい' if s['disk_orientable_return'] else 'いいえ(裏面)'}",
            f"数値安定              : {'安定' if s['stable'] else '発散'}",
            "",
            "注記: lift_index は物理的揚力ではなくシミュレーション診断値です。",
            "      本システムは反重力を発生させる実機ではありません。",
        ]
        return "\n".join(lines)


if __name__ == "__main__":
    sys = MobiusDriveSystem(sectors=64, seed=7)
    sys.run(cycles=40)
    print(sys.report())
