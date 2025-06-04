import netsquid as ns
import numpy as np
from netsquid.components import QuantumChannel, Message
from netsquid.nodes import Node, Network, Connection   
from netsquid.protocols import NodeProtocol
from netsquid.qubits import create_qubits, assign_qstate, ketstates, operate, measure, operators as ops
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.qubits.ketstates import s0, s1
from netsquid.qubits.operators import Operator
from numpy.random import poisson
import random

N = 100  
mu = 1
L = 10  
plus = (s0 + s1) / np.sqrt(2)
minus = (s0 - s1) / np.sqrt(2)

def Rz(theta):
    mat = np.array([
        [np.exp(-1j*theta/2), 0],
        [0, np.exp(1j*theta/2)]
    ])
    return Operator("Rz", mat)

class QubitConnection(Connection):
    def __init__(self, length_km):
        super().__init__("DPS_QubitConnection")
        qchannel = QuantumChannel("QChannel", length=length_km, delay=5,
                                  models={"quantum_noise_model": DepolarNoiseModel(1e-6)})
        self.add_subcomponent(qchannel, forward_input=[("A", "send")], forward_output=[("B", "recv")])
        self.add_ports(["A", "B"])


class AliceProtocol(NodeProtocol):
    def __init__(self, node, num_bits):
        super().__init__(node)
        self.num_bits = num_bits
        self.phases = np.random.choice([0, np.pi], size=num_bits + 1) 
        self.key = []   
    def run(self):
        #print(f"\nAlice's phase choices:")
        for i, phase in enumerate(self.phases):
            ptxt = "0" if phase == 0 else "π"
            #print(f"Pulse {i:2d}: {ptxt}")
        for i in range(self.num_bits):
            delta_phi = (self.phases[i + 1] - self.phases[i]) % (2 * np.pi)
            bit = 0 if delta_phi == 0 else 1
            self.key.append(bit)
        for i in range(self.num_bits+1):
            photon = np.random.poisson(mu)
            if photon == 1:
                qubit = create_qubits(1)[0]
                assign_qstate(qubit, plus)  
                operate(qubit, Rz(self.phases[i]))
                msg = Message([qubit])
                msg.meta["is_vacuum"] = False
                self.node.ports["qout"].tx_output(msg)
                #print(f"Alice: Pulse {i} sent photon")                
            else:
                qubit = create_qubits(1)[0]
                msg = Message([qubit])
                msg.meta["is_vacuum"] = True
                self.node.ports["qout"].tx_output(msg)
                #print(f"Alice: Pulse {i} sent vacuum")
            yield self.await_timer(1) 
        #print("Alice Sifted Key",self.key)

class BobProtocol(NodeProtocol):
    def __init__(self, node, num_bits, alice_protocol=None):
        super().__init__(node)
        self.num_bits = num_bits
        self.alice_protocol = alice_protocol  # Store reference to AliceProtocol
        self.received_qubits = [None] * (num_bits + 1)  # To store all N+1 pulses
        self.key = []

    def run(self):
        #print("\nBob's detection events (with vacuum/meta logic):")
        for i in range(self.num_bits + 1):  # Receive all N+1 pulses
            yield self.await_port_input(self.node.ports["qin"])
            msg = self.node.ports["qin"].rx_input()  # msg is a Message object
            is_vacuum = msg.meta.get("is_vacuum", True)
            qubits = msg.items

            if is_vacuum or not qubits:
                #print(f"  Pulse {i:2d}: Vacuum (dummy qubit)")
                self.received_qubits[i] = None
            else:
                #print(f"  Pulse {i:2d}: Photon received")
                self.received_qubits[i] = qubits[0]

        # DPS: Interferometric measurement between adjacent pulses
        bob_raw_key = []
        for i in range(self.num_bits):
            q1 = self.received_qubits[i]
            q2 = self.received_qubits[i + 1]
            if (q1 is not None) and (q2 is not None):
                res1, _ = measure(q1, observable=ns.X)
                res2, _ = measure(q2, observable=ns.X)
                bit = res1 ^ res2  # XOR of X-basis results gives phase diff
                #print(f"    Interference pulses {i},{i+1}: {bit}")
                bob_raw_key.append(bit)
            else:
                pass
                #print(f"    Interference pulses {i},{i+1}: skipped (missing photon)")

        # Compute detection indices and sifted key indices
        detection_indices = [i for i, q in enumerate(self.received_qubits) if q is not None]
        sifted_indices = [i for i in range(self.num_bits) if self.received_qubits[i] is not None and self.received_qubits[i+1] is not None]
        alice_key = self.alice_protocol.key if self.alice_protocol else []
        alice_sifted_key = [alice_key[i] for i in sifted_indices if i < len(alice_key)] if alice_key else []
        sifted_key_length = len(bob_raw_key)
        mismatches = sum(a != b for a, b in zip(alice_sifted_key, bob_raw_key)) if sifted_key_length > 0 and len(alice_sifted_key) == sifted_key_length else 0
        qber = mismatches / sifted_key_length if sifted_key_length > 0 and len(alice_sifted_key) == sifted_key_length else float('nan')
        detection_count = len(detection_indices)
        detection_rate = detection_count / (self.num_bits + 1) if self.num_bits + 1 > 0 else 0
        simulation_time = ns.sim_time()  # in ns
        key_rate = sifted_key_length / (simulation_time * 1e-9) if simulation_time > 0 else 0  # bits/s

        # Print results
        #print("\n=== DPS QKD Simulation Results ===")
        #print(f"Total pulses sent: {self.num_bits + 1}")
        #print(f"Pulses with photon detections (indices): {detection_indices[:10]}{'...' if len(detection_indices) > 10 else ''}")
        #print(f"Number of photon detections: {detection_count}")
        #print(f"Sifted key pairs (pulse indices): {sifted_indices[:10]}{'...' if len(sifted_indices) > 10 else ''}")
        #print(f"Alice's sifted key: {alice_sifted_key[:10]}{'...' if len(alice_sifted_key) > 10 else ''}")
        #print(f"Bob's sifted key:   {bob_raw_key[:10]}{'...' if len(bob_raw_key) > 10 else ''}")
        #print(f"Sifted key length: {sifted_key_length} bits")
        #print(f"Quantum Bit Error Rate (QBER): {qber:.4f}{' (undefined due to missing alice_key)' if not alice_key else ''}")
        #print(f"Detection rate: {detection_rate:.4f} (fraction of pulses with photons)")
        #print(f"Key rate: {key_rate:.2f} bits/s")
        #print(f"Simulation time: {simulation_time:.2f} ns")
        #print("=================================")



def run_dps_protocol(length=10):
    def setup_network():
        network = Network("DPS_QKD_Network")
        alice = Node("Alice", port_names=["qout"])
        bob = Node("Bob", port_names=["qin"])
        conn = QubitConnection(length_km=length)
        network.add_nodes([alice, bob])
        network.add_connection(alice, bob, connection=conn, label="quantum", port_name_node1="qout", port_name_node2="qin")
        return alice, bob

    ns.set_qstate_formalism(ns.QFormalism.KET)
    ns.sim_reset()

    alice, bob = setup_network()
    alice_protocol = AliceProtocol(alice, N)
    bob_protocol = BobProtocol(bob, N, alice_protocol)  # Reference to AliceProtocol
    alice_protocol.start()
    bob_protocol.start()
    ns.sim_run()

    # Reconstruct Alice's and Bob's sifted keys
    alice_key = alice_protocol.key
    received_qubits = bob_protocol.received_qubits

    sifted_indices = [i for i in range(N) if received_qubits[i] is not None and received_qubits[i + 1] is not None]
    alice_sifted_key = [alice_key[i] for i in sifted_indices if i < len(alice_key)]
    bob_sifted_key = []

    for i in sifted_indices:
        q1 = received_qubits[i]
        q2 = received_qubits[i + 1]
        res1, _ = measure(q1, observable=ns.X)
        res2, _ = measure(q2, observable=ns.X)
        bit = res1 ^ res2
        bob_sifted_key.append(bit)

    errors = sum(a != b for a, b in zip(alice_sifted_key, bob_sifted_key))
    qber = errors / len(alice_sifted_key) if alice_sifted_key else float('nan')

    return qber, alice_sifted_key, bob_sifted_key


