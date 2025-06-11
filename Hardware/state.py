import numpy as np

class QuantumState:
    def __init__(self, ket: np.ndarray):
        self.ket = ket  # State vector
        self.rho = np.outer(ket, ket.conj())  # Density matrix

    def apply_gate(self, U: np.ndarray):
        """Applies unitary gate to the state."""
        self.ket = U @ self.ket #@ is for matrix multiplication
        self.rho = np.outer(self.ket, self.ket.conj())

    def depolarize(self):
        """Simulate complete depolarization: I/d"""
        d = len(self.ket)
        self.rho = np.eye(d) / d #ρ=I/d
