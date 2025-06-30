import numpy as np
from scipy.constants import h, c  # Planck's constant and speed of light

class Pulse:
    def __init__(self, wavelength: float, duration: float, amplitude: float,
                 phase= 0.0, shape: callable = None, quantum_state=None,polarization=None):
        
        self.wavelength = wavelength
        self.duration = duration
        self.amplitude = amplitude
        self.phase = phase
        self.shape = shape if shape else self.default_shape

        self.energy = self.calculate_energy()
        self.mean_photon_number = self.energy / self.photon_energy()
        self.quantum_state = quantum_state
        self.timestamp=None
        # Polarization (in degrees, for PBS etc.), e.g. 0=H, 90=V, 45=D, 135=A
        self.polarization = polarization

    def photon_energy(self) -> float:
        """Returns energy of a single photon at the pulse's wavelength."""
        return h * c / self.wavelength #E=hc/λ

    def calculate_energy(self) -> float:
        """Calculates total pulse energy using amplitude and shape."""
        time_axis = np.linspace(0, self.duration, 1000)
        shape_vals = self.shape(time_axis)
        normalized_shape = shape_vals / np.trapz(shape_vals, time_axis)
        intensity = (self.amplitude ** 2) * normalized_shape
        return np.trapz(intensity, time_axis)

    def default_shape(self, t): #is a function that can be called within the argument of this class
        """Gaussian temporal profile centered in the pulse duration."""
        t0 = self.duration / 2
        sigma = self.duration / 6
        return np.exp(-0.5 * ((t - t0) / sigma) ** 2)

    def sample_photon_arrivals(self):
        """Simulate actual photon arrivals from a weak coherent state."""
        if self.mean_photon_number <= 0:
            return []

        n_photons = np.random.poisson(self.mean_photon_number)
        #print(n_photons)

        if n_photons == 0:
            return []  # no detection event

        
        return [self] * n_photons

        # Get CDF of shape
        time_axis = np.linspace(0, self.duration, 1000)
        shape_vals = self.shape(time_axis)
        norm_shape = shape_vals / np.trapz(shape_vals, time_axis)
        cdf = np.cumsum(norm_shape)
        cdf /= cdf[-1]

        arrival_times = np.interp(np.random.rand(n_photons), cdf, time_axis)
        return list(arrival_times)
