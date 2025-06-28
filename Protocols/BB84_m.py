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
    print(f"Raw key rate          : {key_rate:.2f} bits/sec")
