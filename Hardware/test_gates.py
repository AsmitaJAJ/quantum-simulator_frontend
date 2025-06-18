import numpy as np
from state import QuantumState
from gates import H, X

# Define computational basis states
ket_0 = np.array([1, 0], dtype=complex)
ket_1 = np.array([0, 1], dtype=complex)

# Define measurement projectors in computational basis
P0 = np.outer(ket_0, ket_0.conj())  # |0⟩⟨0|
P1 = np.outer(ket_1, ket_1.conj())  # |1⟩⟨1|
projectors = [P0, P1]

print("=== Test 1: Start in |0⟩, apply Hadamard, then measure ===")
state1 = QuantumState(ket_0)
state1.apply_gate(H)
counts1 = state1.measure(projectors, shots=1000)
print("Expected ~equal counts for 0 and 1:")
print(counts1)

print("\n=== Test 2: Start in |1⟩, apply X (should flip to |0⟩), then measure ===")
state2 = QuantumState(ket_1)
state2.apply_gate(X)
result2 = state2.measure(projectors, shots=1000)
print(f"Expected: 0, Got: {result2}")

print("\n=== Test 3: Start in |0⟩, no gate, measure directly ===")
state3 = QuantumState(ket_0)
result3 = state3.measure(projectors)
print(f"Expected: 0, Got: {result3}")
