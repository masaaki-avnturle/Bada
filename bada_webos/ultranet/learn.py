"""ultranet.learn -- "neural XOR learning" feature for the Bada Web OS ultranetwork.

A tiny, dependency-free feed-forward neural network that LEARNS the XOR function
via backpropagation. Architecture:

    2 inputs  ->  `hidden` sigmoid units  ->  1 sigmoid output

Only the Python standard library is used (`math`, `random`). No numpy.
"""

import math
import random


def _sigmoid(x: float) -> float:
    """Numerically-stable logistic sigmoid, returns a value in (0, 1)."""
    # Guard against overflow in exp() for large-magnitude inputs.
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _dsigmoid_from_output(y: float) -> float:
    """Derivative of sigmoid expressed in terms of its output value y = sigmoid(x)."""
    return y * (1.0 - y)


class XORNet:
    """A 2-`hidden`-1 neural network that learns XOR by backpropagation."""

    # The four rows of the XOR truth table: ((input_a, input_b), target).
    _DATA = [
        ((0.0, 0.0), 0.0),
        ((0.0, 1.0), 1.0),
        ((1.0, 0.0), 1.0),
        ((1.0, 1.0), 0.0),
    ]

    def __init__(self, hidden: int = 4, lr: float = 0.5, seed: int = 7):
        self.hidden = hidden
        self.lr = lr
        self._rng = random.Random(seed)

        # Weight init in [-1, 1] keeps activations in the sigmoid's responsive
        # region and breaks symmetry so units learn different features.
        def w():
            return self._rng.uniform(-1.0, 1.0)

        # Input -> hidden weights: w1[h][i] for hidden unit h, input i (i in {0,1}).
        self.w1 = [[w() for _ in range(2)] for _ in range(hidden)]
        # Hidden bias terms.
        self.b1 = [w() for _ in range(hidden)]

        # Hidden -> output weights: w2[h] for hidden unit h.
        self.w2 = [w() for _ in range(hidden)]
        # Output bias.
        self.b2 = w()

    # ------------------------------------------------------------------ #
    # Forward pass
    # ------------------------------------------------------------------ #
    def _forward(self, a: float, b: float):
        """Return (hidden_outputs, output) for inputs a, b."""
        inputs = (a, b)
        hidden_out = []
        for h in range(self.hidden):
            net = self.b1[h]
            net += self.w1[h][0] * inputs[0]
            net += self.w1[h][1] * inputs[1]
            hidden_out.append(_sigmoid(net))

        net_out = self.b2
        for h in range(self.hidden):
            net_out += self.w2[h] * hidden_out[h]
        output = _sigmoid(net_out)
        return hidden_out, output

    def predict(self, a: float, b: float) -> float:
        """Forward pass; returns the network output in 0..1."""
        _, output = self._forward(a, b)
        return output

    # ------------------------------------------------------------------ #
    # Training
    # ------------------------------------------------------------------ #
    def train(self, epochs: int = 5000) -> float:
        """Train on the 4 XOR rows for `epochs` epochs; return final MSE loss."""
        loss = 0.0
        for _ in range(epochs):
            loss = 0.0
            for (a, b), target in self._DATA:
                inputs = (a, b)
                hidden_out, output = self._forward(a, b)

                # ---- Output layer error / gradient ----
                error = output - target          # d(0.5*err^2)/d(output) = error
                loss += error * error            # accumulate squared error
                delta_out = error * _dsigmoid_from_output(output)

                # ---- Hidden layer deltas (backprop) ----
                delta_hidden = []
                for h in range(self.hidden):
                    dh = delta_out * self.w2[h] * _dsigmoid_from_output(hidden_out[h])
                    delta_hidden.append(dh)

                # ---- Update output weights & bias ----
                for h in range(self.hidden):
                    self.w2[h] -= self.lr * delta_out * hidden_out[h]
                self.b2 -= self.lr * delta_out

                # ---- Update input->hidden weights & biases ----
                for h in range(self.hidden):
                    self.w1[h][0] -= self.lr * delta_hidden[h] * inputs[0]
                    self.w1[h][1] -= self.lr * delta_hidden[h] * inputs[1]
                    self.b1[h] -= self.lr * delta_hidden[h]

            # Mean squared error across the 4 rows.
            loss /= len(self._DATA)
        return loss

    # ------------------------------------------------------------------ #
    # Evaluation helpers
    # ------------------------------------------------------------------ #
    def truth_table(self) -> dict:
        """Return {(a, b): rounded_prediction} for the 4 XOR input rows."""
        table = {}
        for (a, b), _ in self._DATA:
            table[(int(a), int(b))] = int(round(self.predict(a, b)))
        return table

    def accuracy(self) -> float:
        """Fraction of the 4 rows classified correctly (threshold 0.5)."""
        correct = 0
        for (a, b), target in self._DATA:
            predicted = 1 if self.predict(a, b) >= 0.5 else 0
            if predicted == int(target):
                correct += 1
        return correct / len(self._DATA)


if __name__ == "__main__":
    net = XORNet(hidden=4, lr=0.5, seed=7)
    final_loss = net.train(epochs=5000)

    print("Neural XOR learning -- ultranet.learn")
    print("-" * 38)
    print("Truth table (a, b) -> prediction:")
    for (a, b), pred in sorted(net.truth_table().items()):
        print(f"  XOR({a}, {b}) = {pred}")
    print(f"Final MSE loss: {final_loss:.6f}")
    print(f"Accuracy:       {net.accuracy():.2f}")

    assert net.accuracy() == 1.0, "XORNet failed to learn XOR (accuracy < 1.0)"
    assert final_loss < 0.02, f"Final loss too high: {final_loss}"
    print("OK: network learned XOR (accuracy == 1.0, loss < 0.02)")
