from lasers import Laser 
from node import Node
from channel import QuantumChannel
import simpy
import numpy as np
import random
#try to replicate Tokyo paper: 90 km, 0.5db/km loss, expected QBER:2.7%]
class Alice(Node):
    def __init__(self, node_id, env, num_pulses):
        super().__init__(node_id, env) #calls the constructor of the parent class
        self.num_pulses=num_pulses
        self.sent_pulse=[]
        self.actual_key=[]
    def get_alice_bits(self):
        self.actual_key = []
        for i in range(len(self.sent_pulse) - 1):
            phase_diff = (self.sent_pulse[i+1] - self.sent_pulse[i]) % (2 * np.pi)
            bit = 0 if np.isclose(phase_diff, 0.0) else 1
            self.actual_key.append(bit)
        return self.actual_key

            
        
    def run(self, port_id):
        laser=Laser(wavelength=1550e-9, amplitude=1.0)
        self.add_component("laser", laser)
        
        for _ in range(self.num_pulses+1):
            phase = np.random.choice([0, np.pi])
            pulse = laser.emit_pulse(duration=70e-12, phase=phase, quantum_state=None)  # 1 ns pulse, weak coherent
            pulse.mean_photon_number = 0.2
            self.send(port_id, pulse) 
            self.sent_pulse.append(phase)
            #print("Photon no: ", pulse.sample_photon_arrivals())
            yield self.env.timeout(1e-9) #wait for 2ns after the pulse



class Bob(Node):
    def __init__(self, node_id, env):
        super().__init__(node_id, env)
        self.received_pulses = []
        self.bits=[]

    def receive(self, pulse, receiver_port_id):
        if pulse is not None:
            self.received_pulses.append(pulse)
            print(f"[{self.node_id}] Received pulse on port '{receiver_port_id}' with phase: {pulse.phase:.2f} rad")

       
        if len(self.received_pulses) >= 2:
            last = self.received_pulses[-2]
            current = self.received_pulses[-1]
            phase_diff = (current.phase - last.phase) % (2 * np.pi)
            bit = 0 if np.isclose(phase_diff, 0.0) else 1
            #print(f"  -> Interference result: phase_diff = {phase_diff:.2f} rad → bit = {bit}")
            self.bits.append(bit)
            
            
if __name__ == "__main__":
    env = simpy.Environment()

    # Instantiate nodes
    alice = Alice("Alice", env, num_pulses=10000)
    bob = Bob("Bob", env)

    # Assign ports
    alice.assign_port("qport", "quantum_out")
    bob.assign_port("qport", "quantum_in")

    # Connect via Quantum Channel
    channel = QuantumChannel("Channel_Alice_Bob", length_meters=150, attenuation_db_per_m=0.0002, depol_prob=0.0)

    alice.connect_nodes("qport", "qport", bob, channel)

    # Start Alice's process
    env.process(alice.run("qport"))

    env.run(until=1e-6)
    alice_keys=alice.get_alice_bits()
    print("Alice bits: ", str(alice_keys))
    print("Bob key:",str(bob.bits))
    
    min_len = min(len(alice_keys), len(bob.bits))

    sample_size = int(0.3 * min_len)
    sample_indices = random.sample(range(min_len), sample_size)


    errors = sum(
    1 for i in sample_indices
    if alice_keys[i] != bob.bits[i]
    )

    qber = errors / sample_size if sample_size > 0 else 0
    print(qber) 

        
            
            
    
        