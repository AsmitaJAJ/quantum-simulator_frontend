import sys
import os
import simpy
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Hardware.node import Node
from Hardware.lasers import Laser
from Hardware.channel import QuantumChannel

from Hardware.state import QuantumState
from Hardware.gates import H, X

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

'''
class Alice(Node):
    def __init__(self, node_id, env, num_bits):
        super().__init__(node_id, env)
        self.num_bits=num_bits
        self.env=env
        self.node_id=node_id
        self.alice_key=[] #a
        self.alice_basis=[]#b
        self.sent_basis_log={}
        
    def run(self, port_id):
        laser = Laser(wavelength=1550e-9, amplitude=1.0)
        self.add_component("laser", laser)
        self.alice_key=np.random.randint(2, size=self.num_bits)
        self.alice_basis=np.random.randint(2, size=self.num_bits)
        
        ket_0=np.array([1, 0], dtype=complex) #ket 0
        init_State=QuantumState(ket_0)
        
        #I can add logic here to have a ditionary with sent time from node.sent_log (send_time, sender_port_id, data) corresponding to each basis
        for i in range(self.num_bits):
            init_State=QuantumState(ket_0)
            if self.alice_key[i]==1:
                init_State=init_State.apply_gate(X)
            if self.alice_basis[i]==1:
                init_State=init_State.apply_gate(H)
            
            pulse = laser.emit_pulse(duration=70e-12, phase=0, quantum_state=init_State)
            self.send(port_id, pulse)
            last_log = self.sent_log[-1]
            send_time = last_log[0]
            self.sent_basis_log[send_time] = self.alice_basis[i]
            yield self.env.timeout(1e-9)


class Bob(Node):
    def __init__(self, node_id, env):
        super().__init__(node_id, env)
        self.node_id = node_id
        self.env = env
        self.bob_basis = []
        self.measured_key = []

    def receive(self, pulse, receiver_port_id):
        super().receive(pulse, receiver_port_id)

        # Decide basis randomly
        basis = np.random.randint(2)
        self.bob_basis.append(basis)

        if basis == 1:
            pulse.quantum_state = pulse.quantum_state.apply_gate(H)

        measured_bit = pulse.quantum_state.measure()
        self.measured_key.append(measured_bit)



def quantize_time(t, resolution=1e-9):
    return round(t / resolution) * resolution

if __name__ == "__main__":
    env = simpy.Environment()
    num_pulses = 1000

   
    alice = Alice("Alice", env, num_pulses)
    bob = Bob("Bob", env)

   
    alice.assign_port("qport", "quantum_out")
    bob.assign_port("qport", "quantum_in")

   
    channel = QuantumChannel(
        name="Channel_Alice_Bob",
        length_meters=10,
        attenuation_db_per_m=0.0003,
        depol_prob=0.0
    )
    alice.connect_nodes("qport", "qport", bob, channel)

   
    env.process(alice.run("qport"))
    env.run(until=(num_pulses + 10) * 1e-6)

    # Step 1: Build Alice's basis-bit map
    alice_key_dict = {}
    for i, send_time in enumerate(alice.sent_basis_log):
        qtime = quantize_time(send_time)
        bit = alice.alice_key[i]
        basis = alice.alice_basis[i]
        alice_key_dict[qtime] = (bit, basis)

    # Step 2: Build Bob's received basis/bit map
    delay = channel.compute_delay()
    bob_key_dict = {}
    for i, (recv_time, _, _) in enumerate(bob.recv_log):
        qtime = quantize_time(recv_time - delay)
        bit = bob.measured_key[i]
        basis = bob.bob_basis[i]
        bob_key_dict[qtime] = (bit, basis)

    common_times = set(alice_key_dict) & set(bob_key_dict)
    matched_bits = []
    errors = 0

    for t in common_times:
        a_bit, a_basis = alice_key_dict[t]
        b_bit, b_basis = bob_key_dict[t]
        if a_basis == b_basis:
            matched_bits.append((a_bit, b_bit))
            if a_bit != b_bit:
                errors += 1

   
    if matched_bits:
        qber = errors / len(matched_bits)
    else:
        qber = 0

    sim_time = (num_pulses + 10) * 1e-6
    key_rate = len(matched_bits) / sim_time

    print("Total pulses sent     :", len(alice.alice_key))
    print("Pulses received by Bob:", len(bob.recv_log))
    print("Matched key bits      :", len(matched_bits))
    print("Errors                :", errors)
    print("QBER                  :", qber)
    print(f"Raw key rate          : {key_rate:.2f} bits/sec")'''

POL_ERR_STD = 1.0            # degrees → perfect polarization preservation
BOB_HWP_ERR_STD = 0.0        # degrees → Bob's HWP set exactly
PBS_ANGLE_JITTER_STD = 0.0   # degrees → no misalignment in PBS
PBS_EXTINCTION_DB = 60.0     # dB → nearly perfect PBS (realistic ideal)
DARK_COUNT_RATE = 10          # Hz → no dark counts at SNSPD
SNSPD_EFFICIENCY = 0.9       # perfect detection efficiency (100%)
SNSPD_JITTER = 40e-12          # seconds → perfect timing resolution

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
        self.sent_bits = {}    # pulse_id: bit
        self.sent_bases = {}   # pulse_id: basis
        self.sent_pulses = []  # optional: store pulses
        for i in range(self.num_pulses):
            hwp_angle = np.random.choice([0, 45, -22.5, 22.5])
            basis = alice_hwp_basis_map[hwp_angle]
            bit = alice_hwp_bit_map[hwp_angle]

            self.hwp_angles.append(hwp_angle)
            self.bases.append(basis)
            self.bits.append(bit)

            pulse = Pulse(wavelength=1550e-9, duration=70e-12, amplitude=1.0, polarization=0.0)
            pulse.mean_photon_number = 10
            pulse.pulse_id = i  # ✅ attach unique pulse ID
            hwp = HalfWavePlate(theta_deg=hwp_angle)
            pulse = hwp.apply(pulse)

            self.after_hwp_pols.append(pulse.polarization)
            self.pulses.append(pulse)

            # ✅ Log ID-to-bit mapping
            self.sent_bits[i] = bit
            self.sent_bases[i] = basis
            self.sent_pulses.append(pulse)

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
        self.recv_log = []  # List of tuples: (recv_time, basis, detected_bit, click_status)
        self.received_ids = []
        self.received_bits = {}
        self.received_bases = {}

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
            if click:
                pulse_id = data.pulse_id
                self.received_ids.append(pulse_id)
                self.received_bases[pulse_id] = basis
                self.received_bits[pulse_id] = 0
                self.clicks.append('H')
            else:
                self.clicks.append('None')
        elif port == 'V':
            click, _ = self.snspd_V.detect(data, self.env.now)
            if click:
                pulse_id = data.pulse_id
                self.received_ids.append(pulse_id)
                self.received_bases[pulse_id] = basis
                self.received_bits[pulse_id] = 1
                self.clicks.append('V')
            else:
                self.clicks.append('None')
        else:
            self.clicks.append('None')


        # Select Bob's basis
      
if __name__ == "__main__":
    #       np.random.seed(42)
    env = simpy.Environment()

    alice = Alice('Alice', env, num_pulses=1000000)
    bob   = Bob('Bob', env)

    # realistic channel depolarization
    
    qc = QuantumChannel(
        name="QChan",
        length_meters=90_000    ,
        attenuation_db_per_m=0.2/1000,
        depol_prob=0.1,   
        pol_err_std=POL_ERR_STD  # <---- add this!
    )


    alice.connect_nodes('q', 'q', bob, qc)
    env.process(alice.run('q'))

    # run long enough for all pulses
    total_time = alice.num_pulses * 1e-9 + 5e-9
    env.run(until=total_time)

    # only loop over pulses that both parties actually processed
    n = min(len(alice.bits), len(bob.bits), len(bob.clicks))
    sifted_alice = []
    sifted_bob = []

    # Intersection of pulse_ids Bob detected and Alice sent
    common_ids = set(bob.received_ids) & set(alice.sent_bits.keys())

    for pid in common_ids:
        if alice.sent_bases[pid] == bob.received_bases[pid]:
            sifted_alice.append(alice.sent_bits[pid])
            sifted_bob.append(bob.received_bits[pid])

    

    #print(f"Alice sifted key: {sifted_alice}")
    #print(f"Bob   sifted key: {sifted_bob}")
    print(f"Sifted key length: {len(sifted_alice)}")

    if sifted_alice:
        errors = sum(a != b for a, b in zip(sifted_alice, sifted_bob))
        qber   = errors / len(sifted_alice)
        print(f"QBER on sifted key: {qber:.2%}")
    else:
        print("No sifted bits to compute QBER.")