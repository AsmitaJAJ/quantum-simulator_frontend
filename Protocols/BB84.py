import sys
import os
import simpy
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Hardware.node import Node
from Hardware.channel import QuantumChannel
from Hardware.pulse import Pulse
from Hardware.snspd import SNSPD
from Hardware.PBS import PolarizingBeamSplitter
from Hardware.HWP import HalfWavePlate


# Error parameters (tune as needed)
POL_ERR_STD = 20            # degrees, channel polarization error
BOB_HWP_ERR_STD = 2.0       # degrees, Bob HWP misalignment
PBS_ANGLE_JITTER_STD = 1.0  # degrees, PBS splitting error
PBS_EXTINCTION_DB = 25      # dB, PBS imperfection
DARK_COUNT_RATE = 50        # Hz, SNSPD
SNSPD_EFFICIENCY = 0.85
SNSPD_JITTER = 40e-12       # seconds # <--- Change this value as you wish

# Basis and bit mapping for Alice
alice_hwp_basis_map = {0: 'plus', 45: 'plus', -22.5: 'cross', 22.5: 'cross'}
alice_hwp_bit_map = {0: 0, 45: 1, -22.5: 0, 22.5: 1}

# Basis and bit mapping for Bob
bob_hwp_basis_map = {0: 'plus', 22.5: 'cross'}
bob_hwp_bit_map = {0: 0, 22.5: 1}

class Alice(Node):
    def __init__(self, node_id, env, num_pulses=30):
        super().__init__(node_id, env)
        self.assign_port('q', 'quantum')
        self.num_pulses = num_pulses
        self.pulses = []
        self.hwp_angles = []
        self.bases = []
        self.bits = []
        self.after_hwp_pols = []

    def run(self, port_id):
        for i in range(self.num_pulses):
            hwp_angle = np.random.choice([0, 45, -22.5, 22.5])
            basis = alice_hwp_basis_map[hwp_angle]
            bit = alice_hwp_bit_map[hwp_angle]
            self.hwp_angles.append(hwp_angle)
            self.bases.append(basis)
            self.bits.append(bit)
            # Always start horizontal (0°)
            pulse = Pulse(wavelength=1550e-9, duration=70e-12, amplitude=1.0, polarization=0.0)
            pulse.mean_photon_number = 10
            hwp = HalfWavePlate(theta_deg=hwp_angle)
            pulse = hwp.apply(pulse)
            self.after_hwp_pols.append(pulse.polarization)
            self.pulses.append(pulse)
            self.send(port_id, pulse)
            yield self.env.timeout(1e-9)


class Bob(Node):
    def __init__(self, node_id, env):
        super().__init__(node_id, env)
        self.assign_port('q', 'quantum')
        self.snspd_H = SNSPD(
            efficiency=SNSPD_EFFICIENCY,
            dark_count_rate=DARK_COUNT_RATE,
            dead_time=30e-9,
            timing_jitter=SNSPD_JITTER
        )
        self.snspd_V = SNSPD(
            efficiency=SNSPD_EFFICIENCY,
            dark_count_rate=DARK_COUNT_RATE,
            dead_time=30e-9,
            timing_jitter=SNSPD_JITTER
        )
        self.pbs = PolarizingBeamSplitter(
            extinction_ratio_db=PBS_EXTINCTION_DB,
            angle_jitter_std=PBS_ANGLE_JITTER_STD
        )
        self.basis_angles = []
        self.bases = []
        self.bits = []
        self.clicks = []
        self.det_pols = []

    def receive(self, data, receiver_port_id):
        if receiver_port_id != 'q' or data is None:
            return

        # --- Channel polarization noise ---
        data.polarization = (data.polarization + np.random.normal(0, POL_ERR_STD)) % 180

        # --- Bob's HWP setting with error ---
        hwp_angle_nom = np.random.choice([0, 22.5])
        hwp_angle = hwp_angle_nom + np.random.normal(0, BOB_HWP_ERR_STD)
        basis = bob_hwp_basis_map[hwp_angle_nom]
        bit = bob_hwp_bit_map[hwp_angle_nom]
        self.basis_angles.append(hwp_angle_nom)
        self.bases.append(basis)
        self.bits.append(bit)
        hwp = HalfWavePlate(theta_deg=hwp_angle)
        data = hwp.apply(data)
        self.det_pols.append(data.polarization)

        port = self.pbs.split(data)
        if port == 'H':
            click, _ = self.snspd_H.detect(data, self.env.now)
            self.clicks.append('H' if click else 'None')
        elif port == 'V':
            click, _ = self.snspd_V.detect(data, self.env.now)
            self.clicks.append('V' if click else 'None')
        else:
            self.clicks.append('None')

def run_bb84(alice: Alice, bob: Bob, channel:QuantumChannel, env, num_pulses=1000000, **kwargs):
    np.random.seed(42)
    #env = simpy.Environment()

    #alice = Alice('Alice', env, num_pulses=10000)
    #bob   = Bob('Bob', env)

    # realistic channel depolarization
    #qc = QuantumChannel('QChan',length_meters=1,attenuation_db_per_m=0, depol_prob=0.1)

    alice.connect_nodes('q', 'q', bob, channel)
    env.process(alice.run('q'))

    # run long enough for all pulses
    total_time = num_pulses * 1e-9 + 5e-9
    env.run(until=total_time)

    # only loop over pulses that both parties actually processed
    n = min(len(alice.bits), len(bob.bits), len(bob.clicks))
    sifted_alice = []
    sifted_bob   = []

    for i in range(n):
        # basis‐match check
        if alice.bases[i] != bob.bases[i]:
            continue

        # derive Bob's bit
        det = bob.clicks[i]
        if det == 'H': bob_bit = 0
        elif det == 'V': bob_bit = 1
        else: continue

        sifted_alice.append(alice.bits[i])
        sifted_bob.append(bob_bit)

    print(f"Alice sifted key: {sifted_alice}")
    print(f"Bob   sifted key: {sifted_bob}")
    print(f"Sifted key length: {len(sifted_alice)}")

    if sifted_alice:
        errors = sum(a != b for a, b in zip(sifted_alice, sifted_bob))
        qber   = errors / len(sifted_alice)
        print(f"QBER on sifted key: {qber:.2%}")
        return qber
    else:
        print("No sifted bits to compute QBER.")
   

def node_factory(name, role, env, num_pulses=10_00_000):
    if role == "Sender":
        return Alice(name, env, num_pulses=num_pulses)
    elif role == "Receiver":
        
         return Bob(name, env) #here name=node_id
    else:
        return Node(name, env)


def channel_factory(a, b, length_meters, attenuation_db_per_m, depol_prob):
    return QuantumChannel(
        name=f"{a}_{b}",
        length_meters=length_meters,
        attenuation_db_per_m= attenuation_db_per_m,
        depol_prob=depol_prob
    )




