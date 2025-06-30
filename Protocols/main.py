import sys
import os

import simpy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Topology.topology import StarTopology
from Protocols.DPS import node_factory as dps_node, run_dps
from Protocols.COW import node_factory as cow_node , run_cow
from Protocols.DPS import channel_factory as dps_channel
from Protocols.COW import channel_factory as cow_channel

node_specs = {
    "Alice":   {"type": "Sender",   "factory": dps_node},
    "Bob":     {"type": "Receiver", "factory": dps_node},
    "Charlie": {"type": "Receiver", "factory": dps_node}
}

channel_specs = {
    ("Alice", "Bob"): dps_channel,
    ("Alice", "Charlie"): dps_channel
}

topo = StarTopology(
    center_node_id="Alice",
    leaf_node_ids=["Bob", "Charlie"],
    node_specs=node_specs,
    channel_specs=channel_specs
)

env1 = simpy.Environment()
topo.buildTopology(env1, num_pulses=1000)

alice = topo.get_node("Alice")
charlie=topo.get_node("Charlie")
bob = topo.get_node("Bob")
channel = topo.channels[("Alice", "Bob")]
env2=simpy.Environment()
topo.buildTopology(env2, num_pulses=1000)
run_dps(alice, bob, channel, env1, num_pulses=1000)
run_dps(alice, charlie, channel, env2, num_pulses=1000)