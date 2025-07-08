import numpy as np
import sys
import os
from collections import Counter

# Ensure parent directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Hardware.gates import H, CX
from Hardware.state import QuantumState
from Hardware.node import Node
from utils.entanglement_manage import EntanglementManager

# === Dummy Environment ===
class DummyEnv:
    def __init__(self):
        self.now = 0  # Placeholder for SimPy

env = DummyEnv()

# === Create Nodes ===
alice = Node("Alice", env)
bob = Node("Bob", env)

# === Create Entanglement Manager ===
manager = EntanglementManager()

# === Both Nodes Measure in Z Basis (should always be perfectly correlated) ===
num_trials = 1000
results = []

for _ in range(num_trials):
    # 1. Create fresh entangled pair each round
    pair_id, bell_state = manager.create_bell_pair(alice, bob, bell_type='00')  # You need to return both pair_id and state

    # 2. Update each node's active pair_id for this round
    alice.pair_id = pair_id
    bob.pair_id = pair_id

    # 3. Alice and Bob measure
    a_outcome = alice.measure_entangled_qubit(basis='Z')
    b_outcome = bob.measure_entangled_qubit(basis='Z')

    results.append((a_outcome, b_outcome))

# === Analyze Correlation ===
counts = Counter(results)

print("\n=== Measurement Results (Z basis) ===")
for outcome, count in counts.items():
    print(f"Alice: {outcome[0]}, Bob: {outcome[1]} → {count} times")

correlated = counts.get((0, 0), 0) + counts.get((1, 1), 0)
print(f"\nCorrelation: {correlated / num_trials:.2%} expected ~100% for Φ⁺ state.")


print("\nExample Bell state amplitudes (last round):")
print(np.round(bell_state, 3))
print("Alice state id:", id(alice.components[pair_id]))
print("Bob state id:", id(bob.components[pair_id]))
