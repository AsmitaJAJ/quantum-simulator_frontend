import simpy
import numpy as np

from node import Node
from channel import QuantumChannel
from lasers import Laser
from state import QuantumState

env = simpy.Environment()

node_A = Node("A", env)
node_B = Node("B", env)

node_A.assign_port("port1", "to_B")
node_B.assign_port("port2", "from_A")


laser = Laser(wavelength=1550e-9, amplitude=1.0)
node_A.add_component("laser", laser)

channel = QuantumChannel(name="A->B", length_meters=20, attenuation_db_per_m=0.2, depol_prob=0.1)

node_A.connect_nodes("port1", "port2", node_B, channel)

plus_state = QuantumState(1 / np.sqrt(2) * np.array([1, 1]))
pulse = laser.emit_pulse(duration=1e-9, phase=0.0, quantum_state=plus_state)

node_A.send("port1", pulse)

env.run(until=1e-6)  # Run for 1 microsecond
