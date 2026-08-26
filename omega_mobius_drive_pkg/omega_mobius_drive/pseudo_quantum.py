"""
pseudo_quantum.py — ノイマン型 擬似量子コンピュータ (Pseudo-Quantum von Neumann VM)
=================================================================================

ノイマン型（プログラム内蔵方式）の小さな仮想機械。レジスタが単なるビットでは
なく「擬似量子ビット状態」= 実振幅ベクトル (a0, a1) を持つところが擬似量子。
測定 (MEASURE) で確率 |a1|² により 0/1 に収束させる。

⚠️ これは本物の量子コンピュータではない（重ね合わせを実数振幅で模しただけの
   決定論＋擬似乱数シミュレーション）。標準ライブラリのみで動作。

命令セット（超小型）:
    LOAD r imm      レジスタ r に古典値 imm をロード (a0=1-imm, a1=imm 正規化)
    H r             擬似アダマール: (a0,a1) -> ((a0+a1)/√2,(a0-a1)/√2)
    X r             ビット反転: swap(a0,a1)
    PHASE r θ       位相回転（実部のみ近似）: a1 *= cos θ
    ENT r s         擬似もつれ: r と s の振幅を平均で結合
    MEASURE r       確率 |a1|²/(|a0|²+|a1|²) で 0/1 に収束、結果を古典出力へ
    HALT            停止
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple


class _LCG:
    """決定論的擬似乱数（seed 固定で再現可能）。"""

    def __init__(self, seed: int = 0x9E3779B1) -> None:
        self.state = seed & 0xFFFFFFFF

    def random(self) -> float:
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return self.state / 0x7FFFFFFF


@dataclass
class QReg:
    a0: float = 1.0
    a1: float = 0.0

    def normalize(self) -> None:
        n = math.hypot(self.a0, self.a1)
        if n > 1e-12:
            self.a0 /= n
            self.a1 /= n

    def prob_one(self) -> float:
        n = self.a0 * self.a0 + self.a1 * self.a1
        return (self.a1 * self.a1) / n if n > 1e-12 else 0.0


class PseudoQuantumVM:
    def __init__(self, n_regs: int = 4, seed: int = 0x9E3779B1) -> None:
        self.regs: List[QReg] = [QReg() for _ in range(n_regs)]
        self.rng = _LCG(seed)
        self.output: List[int] = []
        self.halted = False

    def run(self, program: List[tuple]) -> List[int]:
        for instr in program:
            if self.halted:
                break
            self._exec(instr)
        return self.output

    def _exec(self, instr: tuple) -> None:
        op = instr[0].upper()
        if op == "LOAD":
            _, r, imm = instr
            self.regs[r] = QReg(a0=1.0 - imm, a1=float(imm))
            self.regs[r].normalize()
        elif op == "H":
            r = instr[1]
            reg = self.regs[r]
            a0, a1 = reg.a0, reg.a1
            reg.a0 = (a0 + a1) / math.sqrt(2)
            reg.a1 = (a0 - a1) / math.sqrt(2)
        elif op == "X":
            r = instr[1]
            self.regs[r].a0, self.regs[r].a1 = self.regs[r].a1, self.regs[r].a0
        elif op == "PHASE":
            _, r, theta = instr
            self.regs[r].a1 *= math.cos(theta)
            self.regs[r].normalize()
        elif op == "ENT":
            _, r, s = instr
            avg0 = (self.regs[r].a0 + self.regs[s].a0) / 2
            avg1 = (self.regs[r].a1 + self.regs[s].a1) / 2
            for q in (self.regs[r], self.regs[s]):
                q.a0, q.a1 = avg0, avg1
                q.normalize()
        elif op == "MEASURE":
            r = instr[1]
            bit = 1 if self.rng.random() < self.regs[r].prob_one() else 0
            self.regs[r] = QReg(a0=1.0 - bit, a1=float(bit))
            self.output.append(bit)
        elif op == "HALT":
            self.halted = True
        else:
            raise ValueError(f"unknown opcode: {op}")


if __name__ == "__main__":
    vm = PseudoQuantumVM(seed=42)
    prog = [
        ("LOAD", 0, 0),
        ("H", 0),          # 重ね合わせ
        ("MEASURE", 0),
        ("LOAD", 1, 1),
        ("X", 1),
        ("MEASURE", 1),
        ("HALT",),
    ]
    print("output bits:", vm.run(prog))
