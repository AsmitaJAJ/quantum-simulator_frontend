# All simulated protocols

## BB84 Protocol
## Overview

The **BB84 protocol** is a prepare-and-measure quantum key distribution (QKD) scheme based on encoding information into the polarization states of single photons.

This simulation models BB84 using realistic quantum hardware components including:
- Half-wave plates (HWPs)
- Polarizing beam splitters (PBS)
- Superconducting nanowire single-photon detectors (SNSPDs)
- A quantum channel with configurable noise and attenuation

---

## Protocol Summary


1. **Preparation (Alice)**

    - Randomly chooses a bit (0 or 1) and an encoding basis (X or Z)
    - Applies a half-wave plate to encode the polarization accordingly
    - Sends a weak coherent pulse through a noisy quantum channel

2. **Measurement (Bob)**

    - Randomly selects a measurement basis (X or Z)
    - Applies a half-wave plate and splits the polarization using a PBS
    - Detects the photon via an SNSPD to determine the bit value

3. **Post-Processing**

    - Alice and Bob publicly compare bases
    - Keep only the bits where both used the same basis (sifted key)
    - Compute Quantum Bit Error Rate (QBER)
    - Apply error correction and privacy amplification (asymptotic key rate)


---

## Simulation Parameters

| Parameter                     | Description                                 | Default Value |
|------------------------------|---------------------------------------------|----------------|
| `POL_ERR_STD`                | Polarization noise in channel (deg)         | `1.0`          |
| `BOB_HWP_ERR_STD`            | HWP angle error at Bob (deg)                | `0.0`          |
| `PBS_ANGLE_JITTER_STD`       | Misalignment noise in PBS                   | `0.0`          |
| `PBS_EXTINCTION_DB`          | Extinction ratio of PBS (dB)                | `60.0`         |
| `DARK_COUNT_RATE`            | SNSPD dark count rate (Hz)                  | `10`           |
| `SNSPD_EFFICIENCY`           | SNSPD efficiency                            | `0.9`          |
| `SNSPD_JITTER`               | SNSPD timing jitter (s)                     | `40e-12`       |
| `pulse.mean_photon_number`   | Photon number per pulse                     | `10`           |
| `pulse.duration`             | Pulse duration                              | `70e-12`       |
| `pulse.wavelength`           | Pulse wavelength                            | `1550e-9`      |
| `num_pulses`                 | Total number of pulses sent                 | `1,000,000`    |

---
### Class: `Alice`


```python
class Alice(Node):
    def __init__(self, node_id, env, num_pulses):
```  

### Class: `Bob`


```python
class Bob(Node):
    def __init__(self, node_id, env): 
```  

## DPS Protocol

## Overview

The **DPS (Differential Phase Shift)** protocol is a prepare-and-measure quantum key distribution (QKD) scheme that encodes bits using the **phase difference** between consecutive weak coherent pulses.

It offers practical implementation advantages by relying on a simple setup involving:
- Lasers emitting weak pulses
- Mach-Zehnder interferometers (MZIs)
- Superconducting nanowire detectors (SNSPDs)

---

## Protocol Summary

1. **Preparation (Alice)**

    - Uses a laser to emit a train of weak coherent pulses.
    - Randomly applies phase shifts: `0` or `π` to each pulse.
    - Sends pulses one-by-one through a quantum channel.

2. **Measurement (Bob)**

    - Receives consecutive pulses and interferes them using a Mach-Zehnder interferometer.
    - Based on the interference result (constructive or destructive), he infers whether the phase difference is `0` (bit = 0) or `π` (bit = 1).
    - The phase difference is what carries the key bit.

3. **Security Mechanism**

    - Since the key is encoded in the **phase difference**, any eavesdropping attempt (e.g., measuring a single pulse) destroys the coherence and introduces errors.
    - QBER increases significantly (above 10-15%) if Eve tries to intercept.

---

## Simulation Parameters

| Parameter                     | Description                                      | Default Value |
|------------------------------|--------------------------------------------------|---------------|
| `pulse.phase`                | Phase shift applied to each pulse (0 or π)      | Random        |
| `pulse.mean_photon_number`   | Average photons per pulse                        | `0.2`         |
| `pulse.duration`             | Pulse duration                                   | `70e-12`      |
| `pulse.wavelength`           | Pulse wavelength                                 | `1550e-9`     |
| `num_pulses`                 | Total number of pulses sent                      | `1,000,000`   |
| `MZI.visibility`             | Interferometer visibility                        | `0.98`        |
| `phase_noise_std`            | Phase noise in interferometer                    | `0.2`         |
| `SNSPD efficiency`           | Photon detection efficiency                      | `0.9`         |
| `dark count rate`            | Background dark count rate                       | `10 Hz`       |

---

## Class: `Alice`

```python

class Alice(Node):
    def __init__(self, node_id, env, num_pulses):
        ...

```
## Class: `Bob`


```python

class Bob(Node):
    def __init__(self, node_id, env, mzi):
        ...
```

##  Coherent-One-Way (COW) QKD Protocol

## Overview

The **COW protocol** is a prepare-and-measure quantum key distribution (QKD) scheme using **time-bin encoding** and **weak coherent pulses**. It ensures security through **decoy states** and **interference monitoring**.

---

## Protocol Summary

**Preparation (Alice)**

- Sends pulses in time-bin pairs.  
- **Bit 0**: Pulse in the first bin, vacuum in the second.  
- **Bit 1**: Vacuum in the first bin, pulse in the second.  
- **Decoy state**: Pulses in both bins (used for eavesdropper detection).  

**Transmission**

- Pulses travel through a lossy, noisy quantum channel.  

**Measurement (Bob)**

- 90% of pulses are measured directly to form the key (data line).  
- 10% are routed to an interferometer (monitor line) to detect interference.  

**Post-Processing**

- Sifted key is extracted from correctly timed detections.  
- Decoy statistics and interferometer clicks (`DM2`) are used to verify security.  
- If too many `DM2` detections occur, the protocol is aborted.



---

## Simulation Parameters

| Parameter                 | Description                              | Default |
|--------------------------|------------------------------------------|---------|
| `num_pulses`             | Number of time-bin pairs sent            | 1000    |
| `decoy_prob`             | Probability of sending a decoy state     | 0.1     |
| `pulse.duration`         | Duration of each pulse (s)               | 70e-12  |
| `pulse.mean_photon_number` | Average photon number per pulse         | 0.5     |
| `monitor_ratio`          | Fraction of pulses sent to monitor line  | 0.1     |
| `visibility`             | Interferometer visibility                | 0.98    |
| `phase_noise_std`        | Standard deviation of phase noise        | 0.02    |
| `SNSPD efficiency`       | Detector efficiency                      | 0.9     |
| `SNSPD dark count rate`  | Detector dark count rate (Hz)            | 10      |

---

## Classes

### `class Alice(Node)`

```python
def __init__(self, node_id, env, num_pulses, decoy_prob):
```

### `class Bob(Node)`

```python
def __init__(self, node_id, env, snspd, monitor_ratio=0.1, threshold=5):

```

## E91 Quantum Key Distribution Protocol

## Overview

The **E91 protocol** is an **entanglement-based** quantum key distribution (QKD) scheme. Instead of sending quantum states directly, Alice and Bob share entangled photon pairs and perform local measurements on them. The correlation of their results provides both a shared key and a built-in security check via **Bell’s inequality**.

This simulation uses:
- Entangled photon pairs (|Ψ⁻⟩ state)
- Configurable depolarization, misalignment, and detector flip errors
- Local projective measurements in the x–z plane
- A trusted entanglement manager to distribute entangled pairs

---

## Protocol Summary

**Entanglement Creation**

- A Bell pair in the state |Ψ⁻⟩ is distributed between Alice and Bob.
- State depolarization (Werner noise) is simulated via a tunable parameter `p_depol`.

**Measurement**

- Alice randomly selects from measurement angles: **0, π/4, π/2**  
- Bob randomly selects from: **π/4, π/2, 3π/4**
- Both apply a small Gaussian misalignment to simulate real-world errors.
- Local projective measurements are performed using a custom function `measure_local`.
- Results are stored as ±1, and detector flip errors are injected with probability `p_flip`.

**Key Generation**

- Only measurement rounds where **Alice and Bob used the same nominal basis** are retained.
- Alice and Bob convert ±1 → 0/1.
- Bob flips his bit (due to anticorrelation of |Ψ⁻⟩) to match Alice.
- The resulting bit sequences form the **sifted key**.

**Security Check**

- Measurement rounds with mismatched bases are used to compute the **Bell parameter (S)**.
- A violation of Bell’s inequality (|S| > 2) confirms entanglement and quantum security.

---

## Simulation Parameters

| Parameter       | Description                                | Default Value |
|----------------|--------------------------------------------|---------------|
| `num_pulses`    | Number of entangled pairs generated         | 10,000        |
| `p_depol`       | Depolarization probability (white noise)    | 0.03          |
| `misalign_deg`  | Angle misalignment std. dev (in degrees)    | 1.5           |
| `p_flip`        | Probability of bit-flip due to detector error| 0.01          |
| `clock_rate`    | Entangled pair generation rate              | 10 MHz        |

---

## Class: `Alice`

```python
class Alice(Node):
    def __init__(self, node_id, env, num_pulses, p_depol, misalign_deg, p_flip)

    def run(self, manager, bob):
        # 1. Creates noisy entangled state
        # 2. Measures her half using basis angle φa
        # 3. Records outcome, applies noise and flip
```

## Class: `Bob`
```python
class Bob(Node):
    def __init__(self, node_id, env):
        self.phi_list = []
        self.s_list = []
```