"""Omega Self-Evolution Engine.

A runnable distillation of the self-evolution ideas in the Yamaguchi reports
(see ../extracted/Bada1.md and ../extracted/explorerfiles.md) into a working
application:

  * TupleSpace        -- write-once, content-addressed memory
                         ("辞書を書き換えることができない" / no overwrite).
  * manifold_emerge   -- generate candidate "manifolds" (expressions) from a
                         pool of operands x operators (source_array x operator_data).
  * cognitive_system  -- the reload / rebuild / re-create generation loop.
  * entropy           -- the "heat-entropy / zeta-gamma monotonicity" fitness.
  * @reviser          -- the meta-level that rewrites its OWN production rules
                         (operator probabilities + mutation strength) from credit
                         assignment. This is the self-evolution: the engine
                         improves the strategy it uses to improve itself.

Core is pure-stdlib and runs fully offline. An optional LLM mutation hook is
provided but disabled by default.
"""

__version__ = "0.1.0"
