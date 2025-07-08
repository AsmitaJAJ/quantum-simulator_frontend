import sys
import os
import simpy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Topology.topology import StarTopology
from Protocols.DPS import node_factory as dps_node_factory, channel_factory as dps_channel_factory, run_dps
from Protocols.COW import node_factory as cow_node_factory, channel_factory as cow_channel_factory, run_cow
from Protocols.BB84 import node_factory as bb84_node_factory, channel_factory as bb84_channel_factory, run_bb84
from Protocols.ProtocolHandler import ProtocolHandler  # Your wrapper class

# --- Simulation environments ---
env_dps = simpy.Environment()
env_cow = simpy.Environment()
env_bb84 = simpy.Environment()

# --- Placeholder specs for protocol-agnostic topology ---
node_specs = {
    "Alice":   {"type": "Generic", "factory": lambda *args, **kwargs: None},
    "Bob":     {"type": "Generic", "factory": lambda *args, **kwargs: None},
    "Charlie": {"type": "Generic", "factory": lambda *args, **kwargs: None}
}

channel_specs = {
    ("Alice", "Bob"): None,
    ("Alice", "Charlie"): None
}

# --- Define Star Topology (can be reused for multiple protocols) ---
topo = StarTopology(center_node_id="Alice", leaf_node_ids=["Bob", "Charlie"],
                    node_specs=node_specs, channel_specs={})
topo.buildTopology(env_dps, num_pulses=1000)

# --- Protocol Handlers ---
dps_handler = ProtocolHandler(
    protocol_name="DPS",
    node_factory=dps_node_factory,
    channel_factory=dps_channel_factory,
    run_function=run_dps
)

cow_handler = ProtocolHandler(
    protocol_name="COW",
    node_factory=cow_node_factory,
    channel_factory=cow_channel_factory,
    run_function=run_cow
)

bb84_handler = ProtocolHandler(
    protocol_name="BB84",
    node_factory=bb84_node_factory,
    channel_factory=bb84_channel_factory,
    run_function=run_bb84
)

# --- Protocol Configurations ---
dps_config = {
    "env": env_dps,
    "nodes": {
        "Alice": {"role": "Sender", "args": {"num_pulses": 10}}, #num pulses taken from here
        "Bob":   {"role": "Receiver", "args": {}}
    },
    "channel": {
        "endpoints": ("Alice", "Bob"),
        "args": {"length_meters": 90000, "attenuation_db_per_m": 0.0002, "depol_prob": 0.1}
    },
    "protocol_args": {"num_pulses": 10}
}

cow_config = {
    "env": env_cow,
    "nodes": {
        "Alice":   {"role": "Sender", "args": {"num_pulses": 10, "decoy_prob": 0.1}},
        "Charlie": {"role": "Receiver", "args": {}}
    },
    "channel": {
        "endpoints": ("Alice", "Charlie"),
        "args": {"length_meters": 90000, "attenuation_db_per_m": 0.0002, "depol_prob": 0.1}
    },
    "protocol_args": {"num_pulses": 10}
}

bb84_config = {
    "env": env_bb84,
    "nodes": {
        "Alice": {"role": "Sender", "args": {"num_pulses": 1000000}}, #num pulses from here
        "Bob":   {"role": "Receiver", "args": {}}
    },
    "channel": {
        "endpoints": ("Alice", "Bob"),
        "args": {"length_meters": 90000, "attenuation_db_per_m": 0.0002, "depol_prob": 0.1, "pol_err_std": 1.0}
    },
    "protocol_args": {"num_pulses": 1000000}
}

# --- Run protocols ---
#dps_handler.run(dps_config)
#cow_handler.run(cow_config)
#bb84_handler.run(bb84_config)

# --- Run and Print QBERs ---
# --- Run and Print QBERs + Logs ---
for handler, config in [
    (dps_handler, dps_config),
    (cow_handler, cow_config),
    (bb84_handler, bb84_config)
]:
    handler.run(config)

    protocol_name = handler.protocol_name
    endpoints = config["channel"]["endpoints"]
    qber = handler.qber

    print(f"\n--- Protocol: {protocol_name} ---")
    print(f"Link: {endpoints[0]} <--> {endpoints[1]}")
    print(f"QBER: {qber:.4f}")

    # Print send and receive logs
    for node_name, node_cfg in config["nodes"].items():
        node = handler.node_objs.get(node_name)
        if not node:
            print(f"{node_name} not found in node_map.")
            continue

        last_sent  = node.sent_log[-1][0] if node.sent_log else None
        last_recv  = node.recv_log[-1][0] if node.recv_log else None

        print(f"Node: {node_name}")
        print(f"  Last sent time:  {last_sent:.2e} s" if last_sent is not None else "  No sends recorded.")
        print(f"  Last recv time:  {last_recv:.2e} s" if last_recv is not None else "  No receives recorded.")
