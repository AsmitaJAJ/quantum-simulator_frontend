
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Hardware.node import Node
from Hardware.channel import OpticalChannel


class Topology:
    def __init__(self, node_specs: dict, channel_specs: dict):
        """
        node_specs: dict mapping node_id -> node_type (e.g., 'Sender', 'Receiver')
        node_factory: function to construct node objects
        channel_factory: function to construct channels between nodes
        """
        self.node_specs = node_specs #node_id: {type: type, factory: node_factory}
        self.channel_specs=channel_specs

        self.nodes = {}      # node_id : Node object
        self.channels = {}   # (node_a, node_b): Channel object

   
    def buildTopology(self, env, num_pulses):
        for node_id, spec in self.node_specs.items(): #dict.items()-> key, val
            role = spec["type"]
            factory = spec["factory"]
            self.nodes[node_id] = factory(node_id, role, env, num_pulses=num_pulses) 
            
        for (a, b), factory in self.channel_specs.items():
            channel = factory(a, b)
            self.channels[(a, b)] = channel
            self.channels[(b, a)] = channel

        
    def get_node(self, node_id):
        return self.nodes[node_id] #returns the specific node object for associated node_id

    def get_neighbors(self, node_id):
        return [b for (a, b) in self.channels if a == node_id]


class StarTopology(Topology):
    def __init__(self, center_node_id, leaf_node_ids, node_specs, channel_specs):
        super().__init__(node_specs, channel_specs)
        self.center = center_node_id
        self.leaves = leaf_node_ids

    


class RingTopology(Topology):
    def __init__(self, node_ids, node_specs, channel_specs):
        super().__init__(node_specs, channel_specs)
        self.ring_nodes = node_ids

    


class MeshTopology(Topology):
    def __init__(self, node_ids, node_specs, channel_specs):
        super().__init__(node_specs, channel_specs)
        self.mesh_nodes = node_ids

    