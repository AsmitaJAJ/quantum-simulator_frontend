import netsquid as ns
from netsquid.nodes import Node, DirectConnection
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.protocols import Protocol
from netsquid.qubits import create_qubits, assign_qstate, ketstates, measure
import random
import numpy as np


class Alice(Protocol):
    def __init__(self, node, num_bits, delay=1, decoy_prob=0.1):
        super().__init__()
        self.actual_key = []
        self.sent_sequence = []
        self.num_bits = num_bits
        self.decoy_prob = decoy_prob
        self.node = node
        self.delay = delay
        self.decoy_indices = []
        self.sifted_key_alice = []

    def run(self):
        mu = 0.1
        for _ in range(self.num_bits):
            photon = np.random.poisson(mu)
            self.actual_key.append(photon)

        for i in range(self.num_bits):
            rand_val = np.random.rand()
            if rand_val < self.decoy_prob:
                pulse1, = create_qubits(1)
                pulse2, = create_qubits(1)
                assign_qstate([pulse1], ketstates.s1)
                assign_qstate([pulse2], ketstates.s1)

                self.node.ports["qout"].tx_output(pulse1)
                yield self.await_timer(self.delay)
                self.node.ports["qout"].tx_output(pulse2)
                yield self.await_timer(self.delay)

                self.sent_sequence.append("D")
                self.decoy_indices.append(i)
            else:
                pulse, = create_qubits(1)
                assign_qstate([pulse], ketstates.s1)

                bit = self.actual_key[i]
                offset = 0.1
                if bit == 1:
                    yield self.await_timer(offset)
                    self.node.ports["qout"].tx_output(pulse)
                    yield self.await_timer(2 * self.delay - offset)
                    self.sent_sequence.append(1)
                else:
                    yield self.await_timer(self.delay + offset)
                    self.node.ports["qout"].tx_output(pulse)
                    yield self.await_timer(self.delay - offset)
                    self.sent_sequence.append(0)

                self.sifted_key_alice.append(bit)

        self.node.ports["cout"].tx_output(Message(self.decoy_indices))


class Bob(Protocol):
    def __init__(self, node, exp_pulses, dm2_thresh, f, delay=1, alice_protocol=None):
        super().__init__()
        self.node = node
        self.exp_pulses = exp_pulses
        self.dm2_thresh = dm2_thresh
        self.f = f
        self.delay = delay
        self.recv_bits = []
        self.dm1_count = 0
        self.dm_2_count = 0
        self.total_received = 0
        self.sifted_key = []
        self.alice_protocol = alice_protocol

    def run(self):
        while self.total_received < self.exp_pulses:
            yield self.await_port_input(self.node.ports["qin"])
            msg = self.node.ports["qin"].rx_input()

            if np.random.rand() < self.f:
                if len(msg.items) == 2:
                    pulse1 = msg.items[0]
                    pulse2 = msg.items[1]
                    res1, _ = measure(pulse1, observable=ns.X)
                    res2, _ = measure(pulse2, observable=ns.X)
                    if res1 ^ res2:
                        self.dm1_count += 1
                    else:
                        self.dm_2_count += 1
            else:
                arrival_time = ns.sim_time()
                time_bin_pos = arrival_time % (2 * self.delay)
                bit = 1 if time_bin_pos < self.delay else 0
                self.recv_bits.append(bit)

            self.total_received += 1

        yield self.await_port_input(self.node.ports["cin"])
        msg = self.node.ports["cin"].rx_input()
        decoy_indices = msg.items

        for i, bit in enumerate(self.recv_bits):
            if i not in decoy_indices:
                self.sifted_key.append(bit)


def run_cow_protocol(num_pulses=100, delay=1, depolar_rate=0.01, length=1, noise_model="DepolarNoiseModel"):
    alice = Node("Alice", port_names=["qout", "cout"])
    bob = Node("Bob", port_names=["qin", "cin"])

    noise_model = DepolarNoiseModel(depolar_rate, time_independent=True)

    cchannel = QuantumChannel("cChannel_Alice_Bob", length=length, models={"quantum_noise_model": noise_model})
    Classical_channel = ClassicalChannel("Channel_sift")

    quantum_connection = DirectConnection("conn_q_Alice_Bob", channel_AtoB=cchannel)
    classical_connection = DirectConnection("conn_c_Alice_Bob", channel_AtoB=Classical_channel)

    alice.connect_to(bob, connection=quantum_connection, local_port_name="qout", remote_port_name="qin")
    alice.connect_to(bob, connection=classical_connection, local_port_name="cout", remote_port_name="cin")

    alice_entity = Alice(alice, num_pulses, delay)
    bob_protocol = Bob(bob, exp_pulses=num_pulses, dm2_thresh=3, f=0.0, delay=delay, alice_protocol=alice_entity)

    alice_entity.start()
    bob_protocol.start()

    ns.sim_run()

    min_len = min(len(alice_entity.sifted_key_alice), len(bob_protocol.sifted_key))
    sample_size = int(0.3 * min_len)
    sample_indices = random.sample(range(min_len), sample_size)

    errors = sum(
        1 for i in sample_indices
        if alice_entity.sifted_key_alice[i] != bob_protocol.sifted_key[i]
    )

    qber = errors / sample_size if sample_size > 0 else 0
    print("QBER:", qber)
    print("Alice's Sifted Key:", alice_entity.sifted_key_alice)
    print("Bob's Sifted Key:", bob_protocol.sifted_key)

    return qber, alice_entity.sifted_key_alice, bob_protocol.sifted_key


if __name__ == '__main__':
    run_cow_protocol()
