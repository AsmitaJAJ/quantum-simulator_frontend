import React, { useState } from 'react';
import alice from './assets/alice.svg';
import bob from './assets/bob.svg';
import './Qkdsimulator.css';
import './Loader.jsx';
import Loader from './Loader.jsx';
import run from './assets/svgviewer-output.svg';
import code from './assets/code.png';



const Qkdsimulator = () => {
  const [qber, setQber] = useState(null);
  const [aliceKey, setAliceKey] = useState([]);
  const [bobKey, setBobKey] = useState([]);
  const [protocol, setProtocol] = useState('DPS');
  const [distance, setDistance] = useState(10);
  const [showAlice, setShowAlice] = useState(false);
  const [showBob, setShowBob] = useState(false);
  const [showCodePanel, setShowCodePanel] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [noiseModel, setModels] = useState('FibreLoss');

  const protocols = ['DPS', 'COW'];
  const errorModels = ['FibreLoss', 'DepolarNoise', 'T1T2Noise']

  const handleRunSimulation = async () => {
  setIsRunning(true);
  try {
    const response = await fetch('http://localhost:5000/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        num_pulses: 50,
        delay: 1,
        channel_length: distance,
        protocol: protocol  // Send selected protocol to backend
      }),
    });

    if (!response.ok) {
      throw new Error('Simulation failed');
    }

    const data = await response.json();
    setQber(data.qber);
    setAliceKey(data.alice_key);
    setBobKey(data.bob_key);
  } catch (error) {
    console.error('Error running simulation:', error);
  } finally {
    // Keep "Running..." for an extra 5 seconds (5000ms) after completion
    setTimeout(() => setIsRunning(false), 2000);
  }
};
  

  const protocolCodes = {
    DPS: `import netsquid as ns
import numpy as np
from netsquid.components import QuantumChannel, Message
from netsquid.nodes import Node, Network, Connection   
from netsquid.protocols import NodeProtocol
from netsquid.qubits import create_qubits, assign_qstate, ketstates, operate, measure, operators as ops
from netsquid.components.qsource import QSource, SourceStatus
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.qubits.ketstates import s0, s1
from netsquid.qubits.operators import Operator
from numpy.random import poisson
import random

N = 100  
mu = 1
L = 10  
plus = (s0 + s1) / np.sqrt(2)
minus = (s0 - s1) / np.sqrt(2)

def Rz(theta):
    mat = np.array([
        [np.exp(-1j*theta/2), 0],
        [0, np.exp(1j*theta/2)]
    ])
    return Operator("Rz", mat)

class QubitConnection(Connection):
    def __init__(self, length_km):
        super().__init__("DPS_QubitConnection")
        qchannel = QuantumChannel("QChannel", length=length_km, delay=5,
                                  models={"quantum_noise_model": DepolarNoiseModel(1e-6)})
        self.add_subcomponent(qchannel, forward_input=[("A", "send")], forward_output=[("B", "recv")])
        self.add_ports(["A", "B"])


class AliceProtocol(NodeProtocol):
    def __init__(self, node, num_bits):
        super().__init__(node)
        self.num_bits = num_bits
        self.phases = np.random.choice([0, np.pi], size=num_bits + 1) 
        self.key = []   
    def run(self):
        #print(f"\nAlice's phase choices:")
        for i, phase in enumerate(self.phases):
            ptxt = "0" if phase == 0 else "π"
            #print(f"Pulse {i:2d}: {ptxt}")
        for i in range(self.num_bits):
            delta_phi = (self.phases[i + 1] - self.phases[i]) % (2 * np.pi)
            bit = 0 if delta_phi == 0 else 1
            self.key.append(bit)
        for i in range(self.num_bits+1):
            photon = np.random.poisson(mu)
            if photon == 1:
                qubit = create_qubits(1)[0]
                assign_qstate(qubit, plus)  
                operate(qubit, Rz(self.phases[i]))
                msg = Message([qubit])
                msg.meta["is_vacuum"] = False
                self.node.ports["qout"].tx_output(msg)
                #print(f"Alice: Pulse {i} sent photon")                
            else:
                qubit = create_qubits(1)[0]
                msg = Message([qubit])
                msg.meta["is_vacuum"] = True
                self.node.ports["qout"].tx_output(msg)
                #print(f"Alice: Pulse {i} sent vacuum")
            yield self.await_timer(1) 
        #print("Alice Sifted Key",self.key)

class BobProtocol(NodeProtocol):
    def __init__(self, node, num_bits, alice_protocol=None):
        super().__init__(node)
        self.num_bits = num_bits
        self.alice_protocol = alice_protocol  # Store reference to AliceProtocol
        self.received_qubits = [None] * (num_bits + 1)  # To store all N+1 pulses
        self.key = []

    def run(self):
        #print("\nBob's detection events (with vacuum/meta logic):")
        for i in range(self.num_bits + 1):  # Receive all N+1 pulses
            yield self.await_port_input(self.node.ports["qin"])
            msg = self.node.ports["qin"].rx_input()  # msg is a Message object
            is_vacuum = msg.meta.get("is_vacuum", True)
            qubits = msg.items

            if is_vacuum or not qubits:
                #print(f"  Pulse {i:2d}: Vacuum (dummy qubit)")
                self.received_qubits[i] = None
            else:
                #print(f"  Pulse {i:2d}: Photon received")
                self.received_qubits[i] = qubits[0]

        # DPS: Interferometric measurement between adjacent pulses
        bob_raw_key = []
        for i in range(self.num_bits):
            q1 = self.received_qubits[i]
            q2 = self.received_qubits[i + 1]
            if (q1 is not None) and (q2 is not None):
                res1, _ = measure(q1, observable=ns.X)
                res2, _ = measure(q2, observable=ns.X)
                bit = res1 ^ res2  # XOR of X-basis results gives phase diff
                #print(f"    Interference pulses {i},{i+1}: {bit}")
                bob_raw_key.append(bit)
            else:
                pass
                #print(f"    Interference pulses {i},{i+1}: skipped (missing photon)")

        # Compute detection indices and sifted key indices
        detection_indices = [i for i, q in enumerate(self.received_qubits) if q is not None]
        sifted_indices = [i for i in range(self.num_bits) if self.received_qubits[i] is not None and self.received_qubits[i+1] is not None]
        alice_key = self.alice_protocol.key if self.alice_protocol else []
        alice_sifted_key = [alice_key[i] for i in sifted_indices if i < len(alice_key)] if alice_key else []
        sifted_key_length = len(bob_raw_key)
        mismatches = sum(a != b for a, b in zip(alice_sifted_key, bob_raw_key)) if sifted_key_length > 0 and len(alice_sifted_key) == sifted_key_length else 0
        qber = mismatches / sifted_key_length if sifted_key_length > 0 and len(alice_sifted_key) == sifted_key_length else float('nan')
        detection_count = len(detection_indices)
        detection_rate = detection_count / (self.num_bits + 1) if self.num_bits + 1 > 0 else 0
        simulation_time = ns.sim_time()  # in ns
        key_rate = sifted_key_length / (simulation_time * 1e-9) if simulation_time > 0 else 0  # bits/s

        # Print results
        #print("\n=== DPS QKD Simulation Results ===")
        #print(f"Total pulses sent: {self.num_bits + 1}")
        #print(f"Pulses with photon detections (indices): {detection_indices[:10]}{'...' if len(detection_indices) > 10 else ''}")
        #print(f"Number of photon detections: {detection_count}")
        #print(f"Sifted key pairs (pulse indices): {sifted_indices[:10]}{'...' if len(sifted_indices) > 10 else ''}")
        #print(f"Alice's sifted key: {alice_sifted_key[:10]}{'...' if len(alice_sifted_key) > 10 else ''}")
        #print(f"Bob's sifted key:   {bob_raw_key[:10]}{'...' if len(bob_raw_key) > 10 else ''}")
        #print(f"Sifted key length: {sifted_key_length} bits")
        #print(f"Quantum Bit Error Rate (QBER): {qber:.4f}{' (undefined due to missing alice_key)' if not alice_key else ''}")
        #print(f"Detection rate: {detection_rate:.4f} (fraction of pulses with photons)")
        #print(f"Key rate: {key_rate:.2f} bits/s")
        #print(f"Simulation time: {simulation_time:.2f} ns")
        #print("=================================")



def run_dps_protocol(length=10):
    def setup_network():
        network = Network("DPS_QKD_Network")
        alice = Node("Alice", port_names=["qout"])
        bob = Node("Bob", port_names=["qin"])
        conn = QubitConnection(length_km=length)
        network.add_nodes([alice, bob])
        network.add_connection(alice, bob, connection=conn, label="quantum", port_name_node1="qout", port_name_node2="qin")
        return alice, bob

    ns.set_qstate_formalism(ns.QFormalism.KET)
    ns.sim_reset()

    alice, bob = setup_network()
    alice_protocol = AliceProtocol(alice, N)
    bob_protocol = BobProtocol(bob, N, alice_protocol)  # Reference to AliceProtocol
    alice_protocol.start()
    bob_protocol.start()
    ns.sim_run()

    # Reconstruct Alice's and Bob's sifted keys
    alice_key = alice_protocol.key
    received_qubits = bob_protocol.received_qubits

    sifted_indices = [i for i in range(N) if received_qubits[i] is not None and received_qubits[i + 1] is not None]
    alice_sifted_key = [alice_key[i] for i in sifted_indices if i < len(alice_key)]
    bob_sifted_key = []

    for i in sifted_indices:
        q1 = received_qubits[i]
        q2 = received_qubits[i + 1]
        res1, _ = measure(q1, observable=ns.X)
        res2, _ = measure(q2, observable=ns.X)
        bit = res1 ^ res2
        bob_sifted_key.append(bit)

    errors = sum(a != b for a, b in zip(alice_sifted_key, bob_sifted_key))
    qber = errors / len(alice_sifted_key) if alice_sifted_key else float('nan')

    return qber, alice_sifted_key, bob_sifted_key
`,
COW: `import netsquid as ns
from netsquid.nodes import Node, DirectConnection
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.protocols import Protocol
from netsquid.qubits import create_qubits, assign_qstate, ketstates, measure
import random
import numpy as np


class Alice(Protocol):
    def __init__(self, node, num_bits, delay=1, decoy_prob=0.1):
        super().__init__()
        self.actual_key = []
        self.sent_sequence = []
        self.num_bits = num_bits
        self.decoy_prob = decoy_prob
        self.node = node
        self.delay = delay
        self.decoy_indices = []
        self.sifted_key_alice = []

    def run(self):
        mu = 0.1
        for _ in range(self.num_bits):
            photon = np.random.poisson(mu)
            self.actual_key.append(photon)

        for i in range(self.num_bits):
            rand_val = np.random.rand()
            if rand_val < self.decoy_prob:
                pulse1, = create_qubits(1)
                pulse2, = create_qubits(1)
                assign_qstate([pulse1], ketstates.s1)
                assign_qstate([pulse2], ketstates.s1)

                self.node.ports["qout"].tx_output(pulse1)
                yield self.await_timer(self.delay)
                self.node.ports["qout"].tx_output(pulse2)
                yield self.await_timer(self.delay)

                self.sent_sequence.append("D")
                self.decoy_indices.append(i)
            else:
                pulse, = create_qubits(1)
                assign_qstate([pulse], ketstates.s1)

                bit = self.actual_key[i]
                offset = 0.1
                if bit == 1:
                    yield self.await_timer(offset)
                    self.node.ports["qout"].tx_output(pulse)
                    yield self.await_timer(2 * self.delay - offset)
                    self.sent_sequence.append(1)
                else:
                    yield self.await_timer(self.delay + offset)
                    self.node.ports["qout"].tx_output(pulse)
                    yield self.await_timer(self.delay - offset)
                    self.sent_sequence.append(0)

                self.sifted_key_alice.append(bit)

        self.node.ports["cout"].tx_output(Message(self.decoy_indices))


class Bob(Protocol):
    def __init__(self, node, exp_pulses, dm2_thresh, f, delay=1, alice_protocol=None):
        super().__init__()
        self.node = node
        self.exp_pulses = exp_pulses
        self.dm2_thresh = dm2_thresh
        self.f = f
        self.delay = delay
        self.recv_bits = []
        self.dm1_count = 0
        self.dm_2_count = 0
        self.total_received = 0
        self.sifted_key = []
        self.alice_protocol = alice_protocol

    def run(self):
        while self.total_received < self.exp_pulses:
            yield self.await_port_input(self.node.ports["qin"])
            msg = self.node.ports["qin"].rx_input()

            if np.random.rand() < self.f:
                if len(msg.items) == 2:
                    pulse1 = msg.items[0]
                    pulse2 = msg.items[1]
                    res1, _ = measure(pulse1, observable=ns.X)
                    res2, _ = measure(pulse2, observable=ns.X)
                    if res1 ^ res2:
                        self.dm1_count += 1
                    else:
                        self.dm_2_count += 1
            else:
                arrival_time = ns.sim_time()
                time_bin_pos = arrival_time % (2 * self.delay)
                bit = 1 if time_bin_pos < self.delay else 0
                self.recv_bits.append(bit)

            self.total_received += 1

        yield self.await_port_input(self.node.ports["cin"])
        msg = self.node.ports["cin"].rx_input()
        decoy_indices = msg.items

        for i, bit in enumerate(self.recv_bits):
            if i not in decoy_indices:
                self.sifted_key.append(bit)


def run_cow_protocol(num_pulses=100, delay=1, depolar_rate=0.01, length=1, noise_model="DepolarNoiseModel"):
    alice = Node("Alice", port_names=["qout", "cout"])
    bob = Node("Bob", port_names=["qin", "cin"])

    noise_model = DepolarNoiseModel(depolar_rate, time_independent=True)

    cchannel = QuantumChannel("cChannel_Alice_Bob", length=length, models={"quantum_noise_model": noise_model})
    Classical_channel = ClassicalChannel("Channel_sift")

    quantum_connection = DirectConnection("conn_q_Alice_Bob", channel_AtoB=cchannel)
    classical_connection = DirectConnection("conn_c_Alice_Bob", channel_AtoB=Classical_channel)

    alice.connect_to(bob, connection=quantum_connection, local_port_name="qout", remote_port_name="qin")
    alice.connect_to(bob, connection=classical_connection, local_port_name="cout", remote_port_name="cin")

    alice_entity = Alice(alice, num_pulses, delay)
    bob_protocol = Bob(bob, exp_pulses=num_pulses, dm2_thresh=3, f=0.0, delay=delay, alice_protocol=alice_entity)

    alice_entity.start()
    bob_protocol.start()

    ns.sim_run()

    min_len = min(len(alice_entity.sifted_key_alice), len(bob_protocol.sifted_key))
    sample_size = int(0.3 * min_len)
    sample_indices = random.sample(range(min_len), sample_size)

    errors = sum(
        1 for i in sample_indices
        if alice_entity.sifted_key_alice[i] != bob_protocol.sifted_key[i]
    )

    qber = errors / sample_size if sample_size > 0 else 0
    print("QBER:", qber)
    print("Alice's Sifted Key:", alice_entity.sifted_key_alice)
    print("Bob's Sifted Key:", bob_protocol.sifted_key)

    return qber, alice_entity.sifted_key_alice, bob_protocol.sifted_key


if __name__ == '__main__':
    run_cow_protocol()

`
  };

const protocolInfo ={
  DPS:`This simulation implements the Differential Phase Shift (DPS) QKD protocol, where key bits are encoded in the phase difference (0 or π) between consecutive weak coherent light pulses sent by Alice.

Bob uses an interferometer to measure these phase differences:

    Phase difference 0 → bit 0

    Phase difference π → bit 1

Only single-photon detection events are used to generate the key. Any eavesdropping attempt disturbs the interference pattern and can be detected.

DPS is practical for fiber-optic systems and offers good resistance to certain attacks like photon number splitting.`,
  COW:`This simulation models the Coherent One-Way (COW) QKD protocol, where Alice sends a sequence of coherent light pulses, with bits encoded based on the presence or absence of a pulse in specific time slots.

    Bit 0: pulse in the first time slot

    Bit 1: pulse in the second time slot

    Decoy states (pulses in both slots) are added to detect eavesdropping.

Bob measures the arrival time of pulses to generate the key and uses an interferometer to check coherence between pulses, helping detect any tampering.

COW is simple, efficient, and suitable for long-distance fiber networks due to its robustness and easy implementation.`
}

  return (
    <div className="qkd-simulator">
      <div className="control-panel">
        <div className="control-group">
          <label>select protocol</label>
          <select 
            value={protocol} 
            onChange={(e) => setProtocol(e.target.value)}
          >
            {protocols.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        <div className="alice-bob">
          <button 
            className={`control-btn ${showAlice ? 'active' : ''}`}
            onClick={() => setShowAlice(!showAlice)}
          >
            <img src={alice} height={76} width={78} alt="alice" />
            
            
          </button>
          <button 
            className={`control-btn ${showBob ? 'active' : ''}`}
            onClick={() => setShowBob(!showBob)}
          >
            <img src={bob} height={76} width={78} alt="bob" />

          </button>
        </div>

        <div className="control-group">
          <label>distance (km)</label>
          <input 
            type="number" 
            value={distance}
            onChange={(e) => setDistance(e.target.value)}
            min="1"
            max="100"
          />
        </div>
        <div className="control-group">
          <label>Select Error Model</label>
          <select 
            value={noiseModel} 
            onChange={(e) => setModels(e.target.value)}
          >
            {errorModels.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>


        <div>
          <button 
          className='run-btn'
            onClick={handleRunSimulation}
            disabled={isRunning}
          >
        
            {isRunning ? 'Running...' : 'run'}
          </button>
        </div>

        <div>
          <button  
          className='code-btn'
            onClick={() => setShowCodePanel(!showCodePanel)}>
              code
          </button>
        </div>
      </div>

      <div className="simulation-area">
        <div className='visual-area'>
  {(showAlice || showBob) && (
    <div className="quantum-channel">
      <div className="quantum-line">
        {showAlice && (
          <div className="entity">
            <img src={alice} height={76} width={78} alt="alice" />
          </div>
        )}
        
        {showAlice && showBob && qber!=null&& (
          <div className="connection-container">
            {!isRunning ? (
              <div>
              <Loader/>
              </div>
            ) : (
              <div className="connection-line" style={{ width: `${distance * 5}px` }}></div>            )}
          </div>
        )}
        
        {showBob && (
          <div className="entity">
            <img src={bob} height={76} width={78} alt="bob" />
          </div>
        )}
      </div>
      {showAlice && showBob && qber != null && !isRunning && (
        <div className="results-container">
          <div className="result-item">
            <p>The QBER is {qber}%</p>
          </div>
          <div className="result-item">
          <p>Alice's Sifted Key: {aliceKey ? aliceKey.join(', ') : 'No key yet'}</p>
          <p>Bob's Sifted Key: {bobKey ? bobKey.join(', ') : 'No key yet'}</p>
            
          </div>
          
        </div>
      )}
    </div>
  )}
  </div>
</div>

      <div className='info-area'>
      <div className='heading'><h3>{protocol} Information</h3></div>
      <p className='info'>{protocolInfo[protocol]}</p>
      </div>

      {showCodePanel && (
        <div className="code-panel">
          <div className="code-header">
            <h3>{protocol} Protocol Code</h3>
            <button onClick={() => setShowCodePanel(false)}></button>
          </div>
          <textarea 
            value={protocolCodes[protocol]}
            onChange={(e) => {}}
            readOnly={false}
          />
          <div className="code-actions">
            <button onClick={() => setShowCodePanel(false)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Qkdsimulator;