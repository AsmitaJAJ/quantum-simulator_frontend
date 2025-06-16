import numpy as np
from pulse import Pulse
from state import QuantumState

class SinglePhotonSource:
    """
    SPS with polarization error and mixedness (depolarization) support.
    """
    def _init_(self, 
                 wavelength=1550e-9,
                 duration=1e-9,
                 phase=0.0,
                 quantum_state=None,
                 eta_src=0.8,
                 p_multi=None,
                 sigma_t=50e-12,
                 sigma_lambda=0.2e-9,
                 p_bg=1e-6,
                 g2_target=None,
                 track_statistics=False,
                 p_polarization_error=0.0,  # New: probability of polarization error
                 p_depolarize=0.0           # New: probability of depolarization
                 ):
        self.wavelength = wavelength
        self.duration = duration
        self.phase = phase

        # Store the initial quantum state (should be a pure state)
        self.init_quantum_state = quantum_state if quantum_state else QuantumState(np.array([0, 1]))
        self.eta_src = eta_src
        self.sigma_t = sigma_t
        self.sigma_lambda = sigma_lambda
        self.p_bg = p_bg

       
        if g2_target is not None:
            self.p_multi = g2_target * (self.eta_src ** 2) / 2
        else:
            self.p_multi = p_multi if p_multi is not None else 1e-4

        self.track_statistics = track_statistics
        self._n_trials = 0
        self._n1 = 0
        self._n2 = 0

        # --- Error model parameters
        self.p_polarization_error = p_polarization_error
        self.p_depolarize = p_depolarize

    def _apply_polarization_error(self, qstate):
        """
        With probability p_polarization_error, apply a random polarization rotation (bit flip).
        """
        if np.random.rand() < self.p_polarization_error:
            # Pauli X (bit-flip) for polarization: |H> <-> |V>
            X = np.array([[0, 1], [1, 0]])
            qstate.apply_gate(X)
        return qstate

    def _apply_depolarization(self, qstate):
        """
        With probability p_depolarize, depolarize the state.
        """
        if np.random.rand() < self.p_depolarize:
            qstate.depolarize()  # As defined in your QuantumState class: rho = I/2
        return qstate

    def emit_pulse(self, trigger_time=0.0):
        info = {
            'trigger_time': trigger_time,
            'emitted': False,
            'n_photons': 0,
            'photon_times': [],
            'wavelengths': [],
            'is_background': False,
            'is_multiphoton': False,
            'g2_0_empirical': None,
            'is_polarization_error': False,
            'is_depolarized': False,
            'purity': None,
        }

        # Emission logic (same as before)
        if np.random.rand() < self.p_bg:
            n_photons = 1
            is_background = True
        elif np.random.rand() < self.p_multi:
            n_photons = 2
            is_background = False
        elif np.random.rand() < self.eta_src:
            n_photons = 1
            is_background = False
        else:
            if self.track_statistics:
                self._n_trials += 1
            return None, info

        info['emitted'] = True
        info['n_photons'] = n_photons
        info['is_background'] = is_background
        info['is_multiphoton'] = n_photons > 1

        # --- Track statistics for empirical g2(0) ---
        if self.track_statistics:
            self._n_trials += 1
            if n_photons == 1:
                self._n1 += 1
            elif n_photons == 2:
                self._n2 += 1

        photon_times = []
        wavelengths = []

        # --- Photon state and errors ---
        for i in range(n_photons):
            jitter = np.random.normal(0, self.sigma_t)
            photon_time = trigger_time + self.duration / 2 + jitter
            lambda_shift = np.random.normal(0, self.sigma_lambda)
            lambda_actual = self.wavelength + lambda_shift

            photon_times.append(photon_time)
            wavelengths.append(lambda_actual)

        # Prepare quantum state (copy to avoid modifying original)
        photon_qstate = QuantumState(self.init_quantum_state.ket.copy())

        # Apply polarization error
        before_polarization = photon_qstate.ket.copy()
        photon_qstate = self._apply_polarization_error(photon_qstate)
        if not np.allclose(before_polarization, photon_qstate.ket):
            info['is_polarization_error'] = True

        # Apply depolarization (mixedness)
        before_depolarization = photon_qstate.rho.copy()
        photon_qstate = self._apply_depolarization(photon_qstate)
        if not np.allclose(before_depolarization, photon_qstate.rho):
            info['is_depolarized'] = True

        # Purity: Tr(rho^2)
        purity = np.real(np.trace(photon_qstate.rho @ photon_qstate.rho))
        info['purity'] = purity

        # For simulation: build a pulse (representing single-photon or multiphoton state)
        pulse = Pulse(
            wavelength=wavelengths[0],
            duration=self.duration,
            amplitude=1.0,
            phase=self.phase,
            quantum_state=photon_qstate,
        )
        pulse.mean_photon_number = n_photons

        info['photon_times'] = photon_times
        info['wavelengths'] = wavelengths

        # Compute and report current empirical g2(0) if tracking
        if self.track_statistics and self._n_trials > 0:
            mean_n = (self._n1 + 2 * self._n2) / self._n_trials
            mean_n2 = (self._n1 + 4 * self._n2) / self._n_trials
            g2_empirical = mean_n2 / (mean_n ** 2) if mean_n > 0 else 0
            info['g2_0_empirical'] = g2_empirical

        return pulse, info

    def get_g2_0_empirical(self):
        if self._n_trials == 0:
            return None
        mean_n = (self._n1 + 2 * self._n2) / self._n_trials
        mean_n2 = (self._n1 + 4 * self._n2) / self._n_trials
        return mean_n2 / (mean_n ** 2) if mean_n > 0 else 0