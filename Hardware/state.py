import numpy as np
from collections import Counter
class QuantumState:
    def __init__(self, ket: np.ndarray=None, rho: np.ndarray=None):
        if rho is not None:
            self.rho=rho
            self.ket=None
        elif ket is not None:
            self.ket=ket
            self.rho=np.outer(ket, ket.conj())
        else:
            raise ValueError("Either ket or rho must be provided.")
    def apply_gate(self, U: np.ndarray):
        """Applies unitary gate to the state."""
        self.rho = U @ self.rho @ U.conj().T
        self.ket = None
        

    def depolarize(self):
        """Simulate complete depolarization: I/d"""
        d = self.rho.shape[0]
        self.rho = np.eye(d) / d #ρ=I/d
        self.ket = None
        
    def measure(self, projectors: list[np.ndarray], shots=1)->dict:
        '''Here, projectors are used to define the measurement basis'''
        probabilities = [np.real(np.trace(P @ self.rho)) for P in projectors] #pi=Tr(Pi ρ), here rho is the state we're measuring, Pi is the projector of the ith basis and pi is the probability of collapsing in that basis/
        
        probabilities = np.array(probabilities) #it was already an array, but np.array gives vectorized methods(i.e you don't need for loops to apply stuff over all elements)
        probabilities /= probabilities.sum() #normalise
        outcomes = np.random.choice(len(projectors), size=shots, p=probabilities) # p gives the probability distribution over all projectors
        #mimics collapse
        if shots==1:
            outcome=outcomes.item()
            P = projectors[outcome]
            self.rho = (P @ self.rho @ P) / probabilities[outcome] #this for measurement collapse
            self.ket = None  # No longer guaranteed pure

            return outcome
            
        counts = Counter(outcomes)
        return dict(counts)