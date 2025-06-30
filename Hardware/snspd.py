import numpy as np

class SNSPD:
    """
    Simulates a realistic Superconducting Nanowire Single-Photon Detector (SNSPD).
    """
    def __init__(self,
                 efficiency=0.93,          # Quantum efficiency (e.g., 93%)
                 dark_count_rate=0.1,      # Dark counts per second (Hz)
                 dead_time=20e-9,          # Dead time after click (seconds, e.g. 20 ns)
                 timing_jitter=20e-12,     # Timing jitter (seconds, e.g. 20 ps)
                 efficiency_spectrum=None  # Optional: function for wavelength-dependent efficiency
                 ):
        self.efficiency = efficiency
        self.dark_count_rate = dark_count_rate
        self.dead_time = dead_time
        self.timing_jitter = timing_jitter
        self.efficiency_spectrum = efficiency_spectrum
        self.last_detection_time = -np.inf

    def detect(self, pulse, current_time=0.0, detection_window=None):
        
        info = {
            "photon_present": False,
            "detected": False,
            "dark_count": False,
            "dead_time_active": False,
            "detection_time": None,
            "timing_jitter": self.timing_jitter,
            "input_state": None,
            "pulse_properties": None,
        }
        # Dead time check
        if current_time - self.last_detection_time < self.dead_time:
            info["dead_time_active"] = True
            return False, info

        eff = self.efficiency
        if self.efficiency_spectrum and pulse is not None:
            eff = self.efficiency_spectrum(getattr(pulse, "wavelength", None))

        if pulse is not None:
            

            info["photon_present"] = True
            info["input_state"] = getattr(pulse, "quantum_state", None)
            info["pulse_properties"] = {
                "wavelength": getattr(pulse, "wavelength", None),
                "arrival_time": getattr(pulse, "arrival_time", None),
                "mean_photon_number": getattr(pulse, "mean_photon_number", None),
            }
            # Correct: Sample Poisson number of photons
            n_photons = np.random.poisson(getattr(pulse, "mean_photon_number", 0))
            detected = False
            for _ in range(n_photons):
                if np.random.rand() < eff:
                    detected = True
                    break
            if detected:
                det_time = current_time + np.random.normal(0, self.timing_jitter)
                info["detected"] = True
                info["detection_time"] = det_time
                self.last_detection_time = det_time
                return True, info

        if detection_window is None:
            detection_window = getattr(pulse, "duration", 1e-9) if pulse else 1e-9
        p_dark = self.dark_count_rate * detection_window
        if np.random.rand() < p_dark:
            det_time = current_time + np.random.normal(0, self.timing_jitter)
            info["dark_count"] = True
            info["detected"] = True
            info["detection_time"] = det_time
            self.last_detection_time = det_time
            return True, info

        return False, info

