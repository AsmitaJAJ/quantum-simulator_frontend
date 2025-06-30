import numpy as np
class HalfWavePlate:
    """
    Simulates a half-wave plate (HWP) that rotates polarization by 2*theta degrees.
    The HWP is set at an angle theta (degrees), and the incoming polarization (deg) is rotated accordingly.
    Includes a small random angle error (misalignment) and some depolarization (fidelity loss).
    """
    def __init__(self, theta_deg, angle_error_std=0.5, depol_prob=0.01):
        """
        theta_deg: Intended HWP setting in degrees
        angle_error_std: std dev of angle mis-setting (degrees)
        depol_prob: probability the pulse is totally depolarized
        """
        self.theta_deg = theta_deg
        self.angle_error_std = angle_error_std
        self.depol_prob = depol_prob

    def apply(self, pulse):
        if not hasattr(pulse, "polarization"):
            raise AttributeError("Pulse does not have a polarization attribute (degrees).")
        # Simulate misalignment error:
        effective_theta = self.theta_deg + np.random.normal(0, self.angle_error_std)
        # Apply half-wave plate action (rotates polarization by 2*theta)
        old_pol = pulse.polarization
        new_pol = (old_pol + 2*effective_theta) % 180  # 0-179 degrees
        # With depol_prob, make it random (i.e., depolarize)
        if np.random.rand() < self.depol_prob:
            new_pol = np.random.uniform(0, 180)
        pulse.polarization = new_pol
        return pulse
