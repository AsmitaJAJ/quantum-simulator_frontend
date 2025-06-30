import numpy as np
from .pulse import Pulse    
from .snspd import SNSPD  

class MachZehnderInterferometer:
    def __init__(self, 
                 snspd0=None, snspd1=None,
                 visibility=0.98,      # Interferometer visibility (0..1)  <--- (Represents optical alignment and polarization overlap)
                 phase_noise_std=0.01  # Phase noise (radians)             <--- (Represents random phase shifts in the delay line/fibers)
                ):
        self.visibility = visibility
        self.phase_noise_std = phase_noise_std
        self.snspd0 = snspd0 if snspd0 else SNSPD()
        self.snspd1 = snspd1 if snspd1 else SNSPD()

    def measure(self, pulse_prev, pulse_next, current_time=0.0):
        """
        Simulate measurement of interference between two pulses in DPS.
        Returns: (bit, detection_info)
        """

        # ---- Practical: Phase Difference Calculation ----
        # (This is the real function of the MZI: overlap two pulses and compute their phase difference)
        phase_diff = (getattr(pulse_next, "phase", 0.0) - getattr(pulse_prev, "phase", 0.0))
        phase_diff += np.random.normal(0, self.phase_noise_std)  # Adds random phase drift (thermal/mechanical/vibration noise in lab)

        # ---- Practical: Interference with Finite Visibility ----
        # (Imperfections reduce maximum/minimum contrast. Real hardware never has 100% visibility)
        prob0 = 0.5 * (1 + self.visibility * np.cos(phase_diff))  # Probability photon exits detector 0 port
        prob1 = 1 - prob0                                        # Probability for detector 1

        # ---- Practical: Pulse Splitting at Output Beamsplitter ----
        # (Physically, the output arms of the interferometer get a share of the pulse energy depending on phase difference)
        pulse0 = Pulse(
            wavelength=pulse_prev.wavelength,
            duration=pulse_prev.duration,
            amplitude=pulse_prev.amplitude * np.sqrt(prob0),  # Energy share
            phase=0,
        )
        pulse0.mean_photon_number = prob0 * getattr(pulse_prev, "mean_photon_number", 1)

        pulse1 = Pulse(
            wavelength=pulse_prev.wavelength,
            duration=pulse_prev.duration,
            amplitude=pulse_prev.amplitude * np.sqrt(prob1),
            phase=0,
        )
        pulse1.mean_photon_number = prob1 * getattr(pulse_prev, "mean_photon_number", 1)

        # ---- Practical: Detection by SNSPDs ----
        # (SNSPDs click with probability based on pulse photon number and detector efficiency, plus possible dark counts)
        click0, info0 = self.snspd0.detect(pulse0, current_time)
        click1, info1 = self.snspd1.detect(pulse1, current_time)

        # ---- Practical: Which Detector Clicked? (Key Bit Extraction) ----
        # (In real DPS-QKD, Bob records a bit only when exactly one detector clicks)
        if click0 and not click1:
            return 0, {"snspd0": info0, "snspd1": info1}   # Detector 0 (phase diff ≈ 0) => bit 0
        elif click1 and not click0:
            return 1, {"snspd0": info0, "snspd1": info1}   # Detector 1 (phase diff ≈ π) => bit 1
        else:
            # No click or both clicked (very rare in SNSPDs): discard event
            return None, {"snspd0": info0, "snspd1": info1}
