import numpy as np
class PolarizingBeamSplitter:
    """
    Ideal PBS: sends horizontal (0°) to 'H' port, vertical (90°) to 'V' port.
    In practice, also include finite extinction ratio and angle jitter.
    """
    def __init__(self, extinction_ratio_db=30, angle_jitter_std=1.0):
        """
        extinction_ratio_db: how well PBS separates polarizations (higher = better)
        angle_jitter_std: standard deviation in deg, simulates alignment error
        """
        self.extinction_ratio_db = extinction_ratio_db
        self.angle_jitter_std = angle_jitter_std

    def angle_distance(self, a, b):
        """
        Minimal distance between two angles in degrees modulo 180.
        (e.g., 179° is only 1° away from 0°)
        """
        d = abs((a - b) % 180)
        return min(d, 180 - d)

    def split(self, pulse):
        """
        Returns 'H' or 'V' depending on the polarization.
        If polarization is within ±22.5° of H (0°), routes to 'H' port.
        If within ±22.5° of V (90°), routes to 'V' port.
        Otherwise, uses extinction ratio to randomly assign.
        """
        if not hasattr(pulse, "polarization"):
            raise AttributeError("Pulse has no polarization attribute (degrees).")

        pol = (pulse.polarization + np.random.normal(0, self.angle_jitter_std)) % 180

        # Determine nearest axis
        if self.angle_distance(pol, 0) < 22.5:
            main_port = 'H'
            off_port = 'V'
        elif self.angle_distance(pol, 90) < 22.5:
            main_port = 'V'
            off_port = 'H'
        else:
            # Diagonal: use extinction ratio to split
            extinction_prob = 10**(-self.extinction_ratio_db / 10)
            if np.random.rand() < extinction_prob:
                # Leakage to wrong port
                main_port = np.random.choice(['H', 'V'])
            else:
                # Blocked: no output
                return None

        return main_port  # Route to port 'H' or 'V'
