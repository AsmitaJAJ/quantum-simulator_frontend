from pulse import Pulse
from state import QuantumState
import numpy as np

class Laser:
    def __init__(self, wavelength: float, amplitude: float):
        self.wavelength = wavelength
        self.amplitude = amplitude

    def emit_pulse(self, duration: float, phase=0.0, quantum_state=None):
        return Pulse(
            wavelength=self.wavelength,
            duration=duration,
            amplitude=self.amplitude,
            phase=phase,
            quantum_state=quantum_state
        )





    
