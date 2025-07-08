# Utils Module

This module provides utility functions and components that support key QKD operations such as entanglement generation, key rate analysis, and unit testing.

## 1. `entanglement_manage.py`

Provides tools for generating Bell pairs and distributing them between two quantum nodes.

### Class: `EntanglementManager`

Handles the creation and distribution of entangled quantum states between two nodes.

**Methods:**

* `__init__()`

  * Initializes an empty dictionary of entangled pairs.
* `create_bell_pair(node_a: Node, node_b: Node, bell_type='00')`

  * Creates a Bell state (default Φ⁺) between `node_a` and `node_b`.
  * Applies Hadamard and CNOT to prepare the state.
  * Returns a pair ID and the shared quantum state.

Use case: Used in protocols like E91 to simulate entanglement-based QKD.

---

## 2. `key_rate.py`

Implements formulas for computing the theoretical key generation rate.

### Function: `binary_entropy(q)`

Returns the Shannon binary entropy of probability `q`. If `q` is 0 or 1, returns 0.

### Function: `compute_key_rate(qber, sifted_rate=0.5)`

* Computes the asymptotic key rate for a given QBER (Quantum Bit Error Rate).
* Applies the formula: `key_rate = sifted_rate × max(0, 1 - 2 × H(qber))`

Returns a rounded value to 6 decimal places.

Use case: Estimating secret key yield under noisy channels.

---

## 3. `test.py`

Test script to validate entanglement correlation between two nodes.

### Purpose:

* Verifies that Bell pairs created by `EntanglementManager` result in perfectly correlated measurement outcomes.
* Performs 1000 trials and prints the count of matching outcomes.

### Key Elements:

* Uses a `DummyEnv` class to mock SimPy environment.
* Creates two nodes (`Alice` and `Bob`).
* Creates Bell pairs and measures in the Z-basis.
* Uses Python’s `Counter` to analyze frequency of correlated outcomes.

Use case: Demonstrates entanglement fidelity and correlation statistics for Bell state Φ⁺ in the simulation.
