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

        # Sort by timestamp
       # self.sent_pulses.sort(key=lambda p: p.timestamp)

        for i in range(len(self.sent_pulses) - 1):
            p1 = self.sent_pulses[i]
            p2 = self.sent_pulses[i + 1]

            if p1.timestamp is None or p2.timestamp is None:
                continue

            time_diff = abs(p2.timestamp - p1.timestamp)
            if abs(time_diff - 1e-9) < 1e-12:  # Allow for numerical tolerance
                phase_diff = (p2.phase - p1.phase) % (2 * np.pi)
                bit = 0 if abs(phase_diff) < 1e-6 or abs(phase_diff - 2 * np.pi) < 1e-6 else 1
                self.actual_key.append((p1.timestamp, bit))

        return self.actual_key

    def run(self, port_id):
        laser = Laser(wavelength=1550e-9, amplitude=1.0)
        self.add_component("laser", laser)

        for i in range(self.num_pulses + 1):
            phase = np.random.choice([0, np.pi])
            pulse = laser.emit_pulse(duration=70e-12, phase=phase)
            pulse.mean_photon_number = 0.2
            pulse.pulse_id = i
            pulse.timestamp = self.env.now  # Store send time locally in protocol, want to implement this via node
            self.sent_pulses.append(pulse)
            self.send(port_id, pulse)
            yield self.env.timeout(1e-9)


class Bob(Node):
    def __init__(self, node_id, env):
        super().__init__(node_id, env)
        self.received_pulses = {}  # pulse_id → (phase, timestamp)
        self.bits = []  # (timestamp, bit)

    def receive(self, pulse, receiver_port_id):
        if pulse is not None:
            pid = pulse.pulse_id
            recv_time = self.env.now  # Reception time
            self.received_pulses[pid] = (pulse.phase, recv_time)

            if (pid - 1) in self.received_pulses:
                prev_phase, prev_time = self.received_pulses[pid - 1]
                phase_diff = (pulse.phase - prev_phase) % (2 * np.pi)
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

    env.process(alice.run("qport")) #registers the genrator object returned by alice.run() as a simpy process
    env.run(until=(num_pulses + 10) * 1e-6)

    # Extract keys
    print("Alice pulses sent: ", len(alice.sent_pulses))
    print("Bob pulses received: ", len(bob.received_pulses))
    def quantize_time(t, resolution=1e-12):  # 1 picosecond
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
   # print("Commmon times: ", len(common_times))
    #print("Alice key: ", alice_key_dict)
    #print("Bob key: ", bob_key_dict)
    
    errors = sum(1 for t in common_times if alice_key_dict[t] != bob_key_dict[t])
    qber = errors / len(common_times) if common_times else 0
    print("QBER: ", qber)
