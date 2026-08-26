"""
mobius_disk.py — 擬似メビウス回路ハードディスク (Simulated Möbius-Circuit Disk)
==============================================================================

仮想ハードディスクを「メビウスの帯」の位相でモデル化する。通常のディスクは
セクタ列 [0, 1, ..., N-1] を持ち、末尾から先頭へ「表のまま」ループする。
メビウス・ディスクは 1 周すると **表裏が反転** する（帯を半回転ひねって
つないだ位相）。本モジュールはその反転をビット極性（+1 / -1）として電子的に
シミュレートし、上位の電子制御装置 (controller.py) が読み書きに使う。

⚠️ これは物理的な磁気ディスクでも実回路でもなく、ソフトウェア上の
   位相モデル（シミュレーション／アート）です。標準ライブラリのみで動作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Sector:
    value: int = 0       # 8bit セル値 (0-255)
    polarity: int = 1    # +1=表, -1=裏（メビウス面）


class MobiusDisk:
    """
    メビウス位相のセクタ・リング。

    ヘッドがリング境界を N 回横切るごとに面（polarity）が反転する。
    つまり 2N セクタ進んで初めて元の面・元の位置に戻る（メビウスの二重被覆）。
    """

    def __init__(self, sectors: int = 64) -> None:
        if sectors < 2:
            raise ValueError("sectors must be >= 2")
        self.n = sectors
        self.disk: List[Sector] = [Sector() for _ in range(sectors)]
        self.head = 0          # 現在のセクタ位置
        self.face = 1          # 現在ヘッドが見ている面 (+1/-1)
        self.laps = 0          # 境界横断回数

    # ---- ヘッド移動（メビウス反転を含む） -------------------------------- #
    def seek(self, delta: int) -> None:
        """相対移動。境界を跨ぐたびに面を反転させる。"""
        pos = self.head
        face = self.face
        step = 1 if delta >= 0 else -1
        for _ in range(abs(delta)):
            pos += step
            if pos >= self.n:
                pos = 0
                face = -face          # メビウス半ひねり：面反転
                self.laps += 1
            elif pos < 0:
                pos = self.n - 1
                face = -face
                self.laps += 1
        self.head = pos
        self.face = face

    # ---- 読み書き（面の極性を値に畳み込む） ------------------------------ #
    def write(self, value: int) -> None:
        s = self.disk[self.head]
        s.value = value & 0xFF
        s.polarity = self.face

    def read(self) -> int:
        """
        面が裏(-1)のときはビット反転して返す（メビウス面での符号反転）。
        表に戻れば元の値が読める＝二重被覆で一意性が回復する。
        """
        s = self.disk[self.head]
        if self.face * s.polarity < 0:
            return (~s.value) & 0xFF
        return s.value

    # ---- 位相の健全性 ---------------------------------------------------- #
    def is_orientable_return(self) -> bool:
        """
        メビウス位相の特徴: 2N ステップで面が元に戻る。
        1N ステップでは面が反転している（＝向き付け不可能）。
        """
        return self.laps % 2 == 0

    def snapshot(self) -> Tuple[int, int, int]:
        return (self.head, self.face, self.laps)


if __name__ == "__main__":
    d = MobiusDisk(sectors=8)
    d.write(0b10101010)
    print("write @0:", bin(0b10101010))
    d.seek(8)   # ちょうど1周 → 面が反転して裏側
    print("after 1 lap  face=", d.face, "read(inverted)=", bin(d.read()))
    d.seek(8)   # もう1周 → 表に復帰（メビウス二重被覆）
    print("after 2 laps face=", d.face, "read(restored)=", bin(d.read()))
