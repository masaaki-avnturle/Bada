"""riemann_prover — リーマン予想 / 深リーマン予想の検証エンジン。

未知事前エンジン (bada_ruby/lib/bada/prover) の健全性規約に従う:
  有限・決定可能な主張だけを「検証完了」とし、予想そのものは「未解決」と明示する。
"""

from .zeta import hurwitz_zeta, zeta, theta, hardy_z, dirichlet_l
from .verify import verify_rh_to_height, schoenfeld_check
from .drh import drh_evidence, CHARACTERS
from .certificate import build_certificate, seal, check_seal

__all__ = [
    "hurwitz_zeta", "zeta", "theta", "hardy_z", "dirichlet_l",
    "verify_rh_to_height", "schoenfeld_check", "drh_evidence", "CHARACTERS",
    "build_certificate", "seal", "check_seal",
]
