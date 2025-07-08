# Topology Module

This module defines an abstract `Topology` class and specific subclasses for star, ring, and mesh network configurations. It is responsible for building and managing the structure of a quantum network in terms of nodes and optical channels.

## Classes

### `Topology`

Represents a generic network topology for QKD nodes and their connecting channels.

**Constructor:**

```python
Topology(node_specs: dict, channel_specs: dict)
```

* `node_specs`: A dictionary where keys are node IDs and values are dictionaries containing:

  * `type`: Role of the node (e.g., "Sender", "Receiver")
  * `factory`: A callable that returns a node object.
* `channel_specs`: A dictionary where keys are (node\_a, node\_b) tuples and values are callables that return an `OpticalChannel` object.

**Attributes:**

* `self.nodes`: Dictionary mapping node IDs to constructed `Node` instances.
* `self.channels`: Dictionary mapping (node\_a, node\_b) tuples to `OpticalChannel` instances.

**Methods:**

* `buildTopology(env, num_pulses)`

  * Builds the topology by instantiating nodes and connecting them with channels.
  * `env`: SimPy environment.
  * `num_pulses`: Number of pulses the node will handle.

* `get_node(node_id)`

  * Returns the node object corresponding to `node_id`.

* `get_neighbors(node_id)`

  * Returns a list of node IDs that are directly connected to the specified node.

---

### `StarTopology`

A specialization of `Topology` representing a star-shaped network.

**Constructor:**

```python
StarTopology(center_node_id, leaf_node_ids, node_specs, channel_specs)
```

* `center_node_id`: ID of the central node.
* `leaf_node_ids`: List of IDs of peripheral nodes.
* Inherits and initializes from the `Topology` class.

**Attributes:**

* `self.center`: Central node ID.
* `self.leaves`: List of peripheral node IDs.

---

### `RingTopology`

A specialization of `Topology` representing a ring network.

**Constructor:**

```python
RingTopology(node_ids, node_specs, channel_specs)
```

* `node_ids`: List of node IDs in the ring.
* Inherits from the `Topology` class.

**Attributes:**

* `self.ring_nodes`: Node IDs in ring structure.

---

### `MeshTopology`

A specialization of `Topology` representing a fully connected mesh network.

**Constructor:**

```python
MeshTopology(node_ids, node_specs, channel_specs)
```

* `node_ids`: List of node IDs in the mesh.
* Inherits from the `Topology` class.

**Attributes:**

* `self.mesh_nodes`: Node IDs in mesh structure.
