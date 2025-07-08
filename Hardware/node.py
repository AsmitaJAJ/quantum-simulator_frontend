import sys
import os
import numpy as np

# Ensure parent directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Hardware.state import QuantumState
from Hardware.gates import H
import numpy as np
class Node:
    def __init__(self, node_id, env):
        self.node_id=node_id
        self.ports={} #port_id: port_name
        self.components={} #component_name: component_instance (basically all components should be classes)
        self.connections={} #sender_port_id: (target_node_id, target_port_id,  channel_object)
        self.env=env
        self.sent_log = []   # sending time of pulses, (send_time, sender_port_id, data)
        self.recv_log = []   # receiving time of pulses

    def assign_port(self, port_id, port_name):
        self.ports[port_id]=port_name
        
    def add_component(self, comp_name, comp_obj):
        self.components[comp_name]=comp_obj
        
    def connect_nodes(self, sender_port_id, receiver_port_id, receiver_node_id, channel_obj):
        self.connections[sender_port_id]=(receiver_node_id, receiver_port_id, channel_obj)
        
    def send(self, sender_port_id,  data):
        if sender_port_id not in self.connections:
            raise Exception(f"Port: {sender_port_id} not connected")
        receiver_node_id, receiver_port_id, channel = self.connections[sender_port_id]
        send_time = self.env.now
        self.sent_log.append((send_time, sender_port_id, data))

        result=channel.transmit(data)
        
        if result is None:
            #print(f"Pulse lost during transmission on channel {channel.name}")
            return
        received_data, delay = result
        
        def delayed_delivery():
            yield self.env.timeout(delay) #advances time by this delay value, if it is 0, then bob receives as soon as alice sends
            
            receiver_node_id.receive(received_data, receiver_port_id)

        self.env.process(delayed_delivery())


        
    def receive(self, data, receiver_port_id):
        recv_time = self.env.now
        self.recv_log.append((recv_time, receiver_port_id, data))
        '''if hasattr(data, 'quantum_state'):
            print(f"[{self.node_id}] Received pulse on port '{receiver_port_id}':")
            print(f"  - Wavelength: {data.wavelength} m")
            print(f"  - Duration: {data.duration} s")
            print(f"  - Amplitude: {data.amplitude}")
            print(f"  - Phase: {data.phase}")
            print(f"  - Quantum State: {data.quantum_state}")
        else:
            print(f"[{self.node_id}] Received classical data on port '{receiver_port_id}': {data}")'''
    def receive_entangled_qubit(self, global_state, qubit_index, pair_id):
        self.components[pair_id] = global_state # Store shared global state
        self.qubit_index = qubit_index
        self.pair_id = pair_id
    
    def measure_entangled_qubit(self, basis='Z'):
        qstate = self.components[self.pair_id]

    # Apply local basis change if needed (e.g., Hadamard for X basis)
        if basis == 'X':
        
            I = np.eye(2, dtype=complex)
            U = np.kron(H, I) if self.qubit_index == 0 else np.kron(I, H)
            qstate.apply_gate(U)

    # Build full-space projectors here (for this node’s qubit)
        ket_0 = np.array([1, 0], dtype=complex)
        ket_1 = np.array([0, 1], dtype=complex)
        P0 = np.outer(ket_0, ket_0.conj())
        P1 = np.outer(ket_1, ket_1.conj())
        I = np.eye(2, dtype=complex)

        if self.qubit_index == 0:
            projectors = [np.kron(P0, I), np.kron(P1, I)]
        else:
            projectors = [np.kron(I, P0), np.kron(I, P1)]

        outcome = qstate.measure(projectors=projectors, shots=1)
        return outcome


