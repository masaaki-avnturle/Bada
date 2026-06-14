"""ultranet.net -- signal-routing primitives for the Bada Web OS ultranetwork.

Two primitives are provided:

  * GravityPort       -- a gate whose opening is governed by a gravitational
                         potential. Signals strong enough to reach "escape
                         velocity" pass (attenuated by 1/(1+mass)); weaker
                         signals are trapped in the well and return 0.

  * BridgeRepeaterNet -- nodes connected by undirected bridges (edges). A signal
                         injected at a source propagates hop-by-hop, attenuating
                         on every bridge. Repeater nodes re-amplify the signal
                         they forward; GravityPorts may trap signals that have
                         decayed too far. The STRONGEST path to each node wins.

Standard library only (`math`, `random`). No numpy.
"""

import heapq


class GravityPort:
    """A gate governed by a gravitational potential.

    A signal must exceed `threshold` (the escape velocity of the well) to pass.
    Signals that do pass are attenuated by 1/(1+mass), modelling the energy lost
    climbing out of the gravity well. Weaker signals are trapped and yield 0.
    """

    def __init__(self, mass: float = 1.0, threshold: float = 0.5):
        self.mass = mass
        self.threshold = threshold

    def gate(self, signal: float) -> float:
        """Return the gated signal: attenuated if it escapes, else 0 (trapped)."""
        if signal <= self.threshold:
            return 0.0
        return signal / (1.0 + self.mass)


class Node:
    """A network node.

    Holds its name, the last signal value it received, whether it acts as a
    repeater, and (if so) the gain it applies when re-amplifying signals.
    """

    def __init__(self, name: str):
        self.name = name
        self.received = 0.0          # strongest signal value received so far
        self.is_repeater = False     # does this node re-amplify forwarded signals?
        self.repeater_gain = 1.0     # multiplier applied when forwarding
        self.port = None             # optional GravityPort guarding this node

    def __repr__(self):
        return f"Node({self.name!r}, received={self.received})"


class BridgeRepeaterNet:
    """A graph of nodes connected by bridges along which signals propagate.

    Each bridge hop multiplies the signal by `hop_attenuation`. A repeater node
    multiplies the signal by its gain when forwarding it onward. A node's
    GravityPort (if present) may trap a too-weak signal, zeroing it and blocking
    further propagation through that node. The strongest path to each node is
    used.
    """

    def __init__(self, hop_attenuation: float = 0.6):
        self.hop_attenuation = hop_attenuation
        self.nodes = {}              # name -> Node
        self.edges = {}              # name -> set of neighbour names

    # ------------------------------------------------------------------ #
    # Graph construction
    # ------------------------------------------------------------------ #
    def add_node(self, name: str, repeater_gain: float = 1.0,
                 port: "GravityPort" = None) -> Node:
        """Add (or fetch) a node. A gain != 1.0 marks it as a repeater."""
        node = self.nodes.get(name)
        if node is None:
            node = Node(name)
            self.nodes[name] = node
            self.edges[name] = set()
        if repeater_gain != 1.0:
            node.is_repeater = True
            node.repeater_gain = repeater_gain
        node.port = port
        return node

    def bridge(self, a: str, b: str) -> None:
        """Create an undirected bridge (edge) between nodes a and b."""
        for name in (a, b):
            if name not in self.nodes:
                self.add_node(name)
        self.edges[a].add(b)
        self.edges[b].add(a)

    def set_repeater(self, name: str, gain: float) -> None:
        """Configure an existing node as a repeater with the given gain."""
        node = self.nodes[name]
        node.is_repeater = True
        node.repeater_gain = gain

    # ------------------------------------------------------------------ #
    # Propagation
    # ------------------------------------------------------------------ #
    def propagate(self, source: str, payload: float = 1.0) -> dict:
        """Spread `payload` from `source`; return {node_name: signal_received}.

        Uses a max-strength (Dijkstra-like) search: a priority queue always
        expands the node currently reachable with the strongest signal, so the
        first time we settle a node we have found its strongest path.

        Rules:
          * The source receives `payload` directly.
          * Crossing a bridge multiplies the signal by `hop_attenuation`.
          * A repeater node multiplies by its gain WHEN IT FORWARDS onward.
          * A node's GravityPort gates the signal as it arrives; a trapped
            (zeroed) signal is recorded as 0 and is not forwarded.
        """
        if source not in self.nodes:
            return {}

        # Reset received values for a clean run.
        for node in self.nodes.values():
            node.received = 0.0

        # Determine the effective signal a node "holds" after its port gates it.
        def gated(name: str, incoming: float) -> float:
            node = self.nodes[name]
            if node.port is not None:
                return node.port.gate(incoming)
            return incoming

        # Strength at which each node is settled (after gating).
        settled = {}

        # Max-heap via negated strength. Entry: (-strength_held, name).
        src_held = gated(source, payload)
        heap = [(-src_held, source)]

        while heap:
            neg_strength, name = heapq.heappop(heap)
            strength = -neg_strength

            if name in settled:
                continue  # already settled with an equal-or-stronger signal
            settled[name] = strength
            self.nodes[name].received = strength

            # A trapped/zero signal cannot be forwarded further.
            if strength <= 0.0:
                continue

            # Strength leaving this node: repeaters amplify before forwarding.
            node = self.nodes[name]
            outgoing = strength * node.repeater_gain if node.is_repeater else strength

            for neighbour in self.edges[name]:
                if neighbour in settled:
                    continue
                arriving = outgoing * self.hop_attenuation
                held = gated(neighbour, arriving)
                if held > 0.0:
                    heapq.heappush(heap, (-held, neighbour))

        return {name: node.received for name, node in self.nodes.items()}

    def reachable(self, source: str, payload: float = 1.0) -> set:
        """Return the set of node names that receive a signal strictly > 0."""
        strengths = self.propagate(source, payload)
        return {name for name, s in strengths.items() if s > 0.0}


if __name__ == "__main__":
    print("Signal routing -- ultranet.net")
    print("-" * 38)

    # Baseline: a plain chain A-B-C-D-E with NO repeater.
    baseline = BridgeRepeaterNet(hop_attenuation=0.6)
    for n in ("A", "B", "C", "D", "E"):
        baseline.add_node(n)
    baseline.bridge("A", "B")
    baseline.bridge("B", "C")
    baseline.bridge("C", "D")
    baseline.bridge("D", "E")
    base_strengths = baseline.propagate("A", payload=1.0)

    # Same chain, but C is a repeater with gain 2.0.
    net = BridgeRepeaterNet(hop_attenuation=0.6)
    for n in ("A", "B", "C", "D", "E"):
        net.add_node(n)
    net.bridge("A", "B")
    net.bridge("B", "C")
    net.bridge("C", "D")
    net.bridge("D", "E")
    net.set_repeater("C", gain=2.0)
    boosted = net.propagate("A", payload=1.0)

    print("Chain A-B-C-D-E, propagate from A (payload=1.0)")
    print(f"{'node':>5} | {'baseline':>10} | {'with C repeater (x2)':>22}")
    for n in ("A", "B", "C", "D", "E"):
        print(f"{n:>5} | {base_strengths[n]:>10.4f} | {boosted[n]:>22.4f}")

    print(f"\nReachable from A: {sorted(net.reachable('A'))}")

    # Demonstrate the repeater boosts downstream strength.
    assert boosted["D"] > base_strengths["D"], "repeater did not boost node D"
    assert boosted["E"] > base_strengths["E"], "repeater did not boost node E"
    print("OK: repeater C boosts downstream strength at D and E.")

    # Demonstrate a GravityPort trapping a weak signal.
    trap_net = BridgeRepeaterNet(hop_attenuation=0.6)
    trap_net.add_node("A")
    trap_net.add_node("B")
    # Port on B with a high escape threshold traps the attenuated signal.
    trap_net.add_node("C", port=GravityPort(mass=1.0, threshold=0.9))
    trap_net.bridge("A", "B")
    trap_net.bridge("B", "C")
    trapped = trap_net.propagate("A", payload=1.0)
    print(f"\nGravityPort demo (threshold 0.9 at C): {trapped}")
    print(f"Reachable from A: {sorted(trap_net.reachable('A'))}")
    assert trapped["C"] == 0.0, "GravityPort failed to trap the weak signal at C"
    print("OK: GravityPort trapped the weak signal at C.")
