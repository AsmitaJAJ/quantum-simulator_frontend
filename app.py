from flask import Flask, request, jsonify
from flask_cors import CORS
import simpy
from Topology.topology import StarTopology
from Protocols.DPS import node_factory as dps_node_factory, channel_factory as dps_channel_factory, run_dps
from Protocols.COW import node_factory as cow_node_factory, channel_factory as cow_channel_factory, run_cow
from Protocols.BB84 import node_factory as bb84_node_factory, channel_factory as bb84_channel_factory, run_bb84
from Protocols.ProtocolHandler import ProtocolHandler

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- Protocol Registry ---
protocols = {
    "DPS": {
        "node_factory": dps_node_factory,
        "channel_factory": dps_channel_factory,
        "run_function": run_dps,
    },
    "COW": {
        "node_factory": cow_node_factory,
        "channel_factory": cow_channel_factory,
        "run_function": run_cow,
    },
    "BB84": {
        "node_factory": bb84_node_factory,
        "channel_factory": bb84_channel_factory,
        "run_function": run_bb84,
    }
}


@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json()

    cities = data["cities"]              # List of city/node names
    topology = data["topology"]          # "Star", "Ring", or "Mesh"
    edges = data["edges"]                # List of [cityA, cityB]
    protocols_per_edge = data["protocols"]  # Dict { "cityA-cityB": "DPS" }

    results = []

    for edge in edges:
        node_a, node_b = edge["nodes"]
        distance = edge["distance"]
        protocol_name = protocols_per_edge.get(f"{node_a}-{node_b}") or protocols_per_edge.get(f"{node_b}-{node_a}")
        if protocol_name not in protocols:
            return jsonify({"error": f"Unsupported protocol: {protocol_name}"}), 400

        # Setup handler
        proto = protocols[protocol_name]
        handler = ProtocolHandler(protocol_name, proto["node_factory"], proto["channel_factory"], proto["run_function"])

        # SimPy env and config
        env = simpy.Environment()

        config = {
            "env": env,
            "nodes": {
                node_a: {"role": "Sender", "args": {"num_pulses": 1000000}},
                node_b: {"role": "Receiver", "args": {}}
            },
            "channel": {
                "endpoints": (node_a, node_b),
                "args": {"length_meters": distance, "attenuation_db_per_m": 0.0002, "depol_prob": 0.1, "pol_err_std": 1.0}
            },
            "protocol_args": {"num_pulses": 10}
        }

        handler.run(config)

        qber = handler.qber
        asym_key_rate=handler.asym_key_rate
        hardware_stats = {
        "distance_m": distance,
        "attenuation_db_per_m": config["channel"]["args"]["attenuation_db_per_m"],
        "depol_prob": config["channel"]["args"]["depol_prob"],
        "pol_err_std": config["channel"]["args"]["pol_err_std"],
        "pulse_wavelength_nm": 1550  # example: 1550nm typical telecom wavelength
        }
        result = {
        "protocol": protocol_name,
        "link": f"{node_a} <--> {node_b}",
        "qber": round(qber, 4) if qber is not None else None,
        "key_rate": round(asym_key_rate, 4) if asym_key_rate is not None else 0.0,
        "nodes": {},
        "hardware_stats": hardware_stats
}


        for node_name in [node_a, node_b]:
            node = handler.node_objs.get(node_name)
            if not node:
                continue

            last_sent = node.sent_log[-1][0] if node.sent_log else None
            last_recv = node.recv_log[-1][0] if node.recv_log else None

            result["nodes"][node_name] = {
                "last_sent_time": f"{last_sent:.2e}" if last_sent is not None else None,
                "last_recv_time": f"{last_recv:.2e}" if last_recv is not None else None,
            }

        results.append(result)

    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
