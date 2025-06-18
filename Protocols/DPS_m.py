import sys
import os
import simpy
import numpy as np
import random

# Ensure parent directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import simpy
import numpy as np
from Hardware.node import Node
from Hardware.lasers import Laser
from Hardware.channel import QuantumChannel

class Alice(Node):
    def __init__(self, node_id, env, num_pulses):
        super().__init__(node_id, env)
        self.num_pulses = num_pulses
        self.sent_pulses = []  # list of (pulse, timestamp)
        self.actual_key = []

    def get_alice_bits(self):
        self.actual_key = []


        for i in range(len(self.sent_log) - 1):
            t1, _, p1 = self.sent_log[i]
            t2, _, p2 = self.sent_log[i + 1]

            if t1 is None or t2 is None:
                continue

            time_diff = abs(t2-t1)
            if abs(time_diff - 1e-9) < 1e-12:  # Allow for numerical tolerance
                phase_diff = (p2.phase - p1.phase) % (2 * np.pi)
                bit = 0 if abs(phase_diff) < 1e-6 or abs(phase_diff - 2 * np.pi) < 1e-6 else 1
                self.actual_key.append((t1, bit))

        return self.actual_key

    def run(self, port_id):
        laser = Laser(wavelength=1550e-9, amplitude=1.0)
        self.add_component("laser", laser)

        for i in range(self.num_pulses + 1):
            phase = np.random.choice([0, np.pi])
            pulse = laser.emit_pulse(duration=70e-12, phase=phase)
            pulse.mean_photon_number = 0.2
            pulse.pulse_id = i
            
            self.sent_pulses.append(pulse)
            self.send(port_id, pulse)
            yield self.env.timeout(1e-9)


class Bob(Node):
    def __init__(self, node_id, env):
        super().__init__(node_id, env)
        self.received_pulses = {}  # pulse_id → (phase, timestamp)
        self.bits = []  # (timestamp, bit)

    def receive(self, pulse, receiver_port_id):
        
        super().receive(pulse, receiver_port_id) #because we're overriding receive, but still want base behaviour
        
        if pulse is not None and pulse.pulse_id is not None:
            recv_time = self.env.now
            self.received_pulses[pulse.pulse_id] = (pulse.phase, recv_time)

           
            pulse_map = {p.pulse_id: (t, p) for t, _, p in self.recv_log if hasattr(p, 'pulse_id')}
            pid = pulse.pulse_id

            if (pid - 1) in pulse_map:
                prev_time, prev_pulse = pulse_map[pid - 1]
                phase_diff = (pulse.phase - prev_pulse.phase) % (2 * np.pi)
                bit = 0 if abs(phase_diff) < 1e-6 or abs(phase_diff - 2 * np.pi) < 1e-6 else 1
                self.bits.append((prev_time, bit))



if __name__ == "__main__":
    env = simpy.Environment()
    num_pulses = 1000

    alice = Alice("Alice", env, num_pulses)
    bob = Bob("Bob", env)

    # Port and channel setup
    alice.assign_port("qport", "quantum_out")
    bob.assign_port("qport", "quantum_in")

    channel = QuantumChannel(
        name="Channel_Alice_Bob",
        length_meters=10,
        attenuation_db_per_m=0.0003,
        depol_prob=0.0
    )
    alice.connect_nodes("qport", "qport", bob, channel)

    env.process(alice.run("qport")) #registers the genrator object(given by yield..) returned by alice.run() as a simpy process
    env.run(until=(num_pulses + 10) * 1e-6)

  
    print("Alice pulses sent: ", len(alice.sent_pulses))
    print("Bob pulses received: ", len(bob.received_pulses))
    def quantize_time(t, resolution=1e-12):  
        return round(t / resolution) * resolution


    alice_key_dict = {
    quantize_time(t): b for t, b in alice.get_alice_bits()
    }
    delay=channel.compute_delay()
    bob_key_dict = {
    quantize_time(t - delay): b for t, b in bob.bits
    }



    print("Alice bits: ", len(alice_key_dict))
    print("Bob bits: ", len(bob_key_dict))

    # Matching timestamps from both
    common_times = set(alice_key_dict.keys()) & set(bob_key_dict.keys())
 
    errors = sum(1 for t in common_times if alice_key_dict[t] != bob_key_dict[t])
    qber = errors / len(common_times) if common_times else 0
    print("QBER: ", qber)
