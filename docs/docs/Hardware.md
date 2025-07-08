# Hardware Module

This module contains implementations of core physical components used in QKD setups. Each file represents a modeled device with its behavior defined through classes and methods.

## 1. Hardware

### [`lasers.py`](./lasers.py) (uses [`pulse.py`](./pulse.py))

The lasers.py module models a laser source capable of emitting light pulses. In the context of QKD, it simulates the emission of optical pulses used to encode and transmit quantum information. The generated pulses can carry polarization or phase-encoded quantum states, serving as carriers in the QKD protocol.

**Class:**

* `Laser(wavelength: float, amplitude: float)`

**Functions:**

* `emit_pulse(duration: float, phase: float, quantum_state: None | QuantumState)`
  Returns an instance of the `Pulse` class.

---

### [`pulse.py`](./pulse.py)

A pulse represents a discrete transmission of quantum information in the form of electromagnetic energy. In QKD, pulses carry encoded quantum states (e.g., polarization) and are the physical medium used to transmit bits securely.

**Class:**

* `Pulse(wavelength: float, duration: float, amplitude: float, phase: float, shape: callable, quantum_state: QuantumState, polarisation)`

**Functions:**

* `photon_energy()`
  Returns the energy of a single photon (`E = hc / λ`).
* `calculate_energy()`
  Returns the energy of the entire wave.
* `default_shape(t)`
  Returns the default shape of the wave (Gaussian).
* `sample_photon_arrivals()`
  Returns a list of `Pulse` instances, each representing a photon. The number of photons is Poisson-distributed based on the mean photon number (Weak Coherent Pulses).

**Note:** The polarization and quantum state can be defined independently. The simulator does not enforce consistency between the two.

---

### [`MZI.py`](./MZI.py) (uses [`pulse.py`](./pulse.py), [`snspd.py`](./snspd.py))

The Mach-Zehnder Interferometer (MZI) is an optical device used to measure phase shifts in quantum signals. In QKD simulations, it allows for interference-based measurements that are crucial for certain protocols (e.g., phase-encoded QKD). By comparing the phase of incoming pulses, the MZI helps determine bit values based on interference outcomes.

**Class:**

* `MachZehnderInterferometer(snspd0: SNSPD, snspd1: SNSPD, visibility: float, phase_noise_std: float)`

**Functions:**

* `measure(pulse_prev: Pulse, pulse_next: Pulse, current_time: simpy time)`
  Returns:

  * `0` if detector 0 is activated (phase difference = 0)
  * `1` if detector 1 is activated (phase difference = π)
  * Additional metadata in a dictionary

---

### [`snspd.py`](./snspd.py)

The Superconducting Nanowire Single-Photon Detector (SNSPD) is a highly sensitive photon detector used in QKD systems. It detects the arrival of individual photons with high efficiency and low noise, making it ideal for secure quantum communication where precise detection is critical.

**Class:**

* `SNSPD(efficiency: float, dark_count_rate: Hz, dead_time, timing_jitter, efficiency_spectrum)`

**Functions:**

* `detect(pulse, current_time: float, detection_window)`
  Returns a tuple:

  * `True/False` (was a detection registered)
  * Info dictionary:

    * `dark_count: bool`
    * `detected: bool`
    * `detection_time`

---

### [`sps.py`](./sps.py)

The Single Photon Source (SPS) module models the emission of individual photons used in quantum communication. It simulates realistic imperfections such as polarization errors and depolarization effects, which are essential for evaluating the robustness of QKD protocols in practical conditions.

**Class:**

* `SPS`

**Functions:**

* `_apply_polarization_error(qstate: QuantumState)`
  Applies a bit flip due to polarization error.
* `_apply_depolarization(qstate)`
  Depolarizes the quantum state.
* `emit_pulse(trigger_time: float)`
  Returns a pulse and an info dictionary.
* `get_g2_0_empirical()`
  Returns the second-order correlation function (empirical).

---

### [`HWP.py`](./HWP.py)

The Half-Wave Plate (HWP) is an optical device that rotates the polarization of light. In QKD simulations, it is used to implement polarization encoding by altering the state of incoming photons. The model includes imperfections such as angle errors and depolarization to simulate realistic scenarios.

**Class:**

* `HalfWavePlate(theta_deg, angle_error_std: radians, depol_prob: float)`

---

### [`PBS.py`](./PBS.py)

The Polarizing Beam Splitter (PBS) is an optical component used to separate incoming light based on its polarization. In QKD simulations, it helps route photons according to their polarization state, enabling polarization-based encoding and measurement. The implementation includes realistic imperfections such as extinction ratio and angular jitter.

**Class:**

* `PolarizingBeamSplitter(extinction_ratio_db, angle_jitter_std)`

---

## 2. Quantum State

### [`state.py`](./state.py)

The `state.py` module defines the quantum state representation used throughout the simulation. It includes tools for defining, manipulating, and measuring single-qubit quantum states represented by vectors or density matrices.

**Class:**

* `QuantumState(ket: np.ndarray, rho: np.ndarray)`

**Functions:**

* `apply_gate(unitary_matrix)`
  Applies a single-qubit unitary transformation.
* `depolarize()`
  Depolarizes the state completely.
* `measure(projectors, shots)`
  Simulates measurement and state collapse. Returns a dictionary of basis state occurrences.

---

### [`gates.py`](./gates.py)

The `gates.py` module contains standard quantum gates (e.g., Pauli, Hadamard) represented as matrices. These gates can be applied to `QuantumState` objects. Users can also define custom gates and add them to this module.

Contains predefined gates and their matrices. Users can define and add custom gates here.

---

## 3. Node and Channel

### [`node.py`](./node.py)

The `node.py` module defines the abstraction for network nodes in the QKD system. Each node acts as a sender or receiver of quantum or classical data and can be configured with hardware components and communication ports.

**Class:**

* `Node(node_id, env: simpy.Environment)`

**Functions:**

* `assign_port(port_id, port_name)`
* `add_component(comp_name, comp_obj)`
* `connect_nodes(sender_port_id, receiver_port_id, receiver_node_id, channel_obj)`
* `send(sender_port_id, data)`
* `receive(data, receiver_port_id)`
  The `receive` method is used to model simulation delay and is overridden in protocol-specific implementations.

---

### [`channel.py`](./channel.py)

The `channel.py` module simulates the communication medium between nodes. It models both quantum and classical channels with parameters such as distance-based loss, transmission delay, and noise.

**Class:**

* `OpticalChannel(name, length_meters, attenuation_db_per_m, light_speed=2e8)`

**Functions:**

* `compute_loss()`
* `compute_delay()`

**Subclasses:**

* `QuantumChannel`: Adds depolarizing noise.
* `ClassicalChannel`: Adds delay, no loss.
