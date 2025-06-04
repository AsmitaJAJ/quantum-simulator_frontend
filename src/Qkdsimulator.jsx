import React, { useState } from 'react';
import alice from './assets/alice.png';
import bob from './assets/bob.png';
import './Qkdsimulator.css';
import './Loader.jsx';
import Loader from './Loader.jsx';
import run from './assets/run.png';
import code from './assets/code.png';

const QBER = 0;
const sifted_key = 'null';
const Qkdsimulator = () => {
  const [protocol, setProtocol] = useState('DPS');
  const [distance, setDistance] = useState(10);
  const [showAlice, setShowAlice] = useState(false);
  const [showBob, setShowBob] = useState(false);
  const [showCodePanel, setShowCodePanel] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [noiseModel, setModels] = useState('FibreLoss');

  const protocols = ['DPS', 'COW'];
  const errorModels = ['FibreLoss', 'DepolarNoise', 'T1T2Noise']

  const handleRunSimulation = () => {
    setIsRunning(true);
    // Simulation logic would go here
    setTimeout(() => setIsRunning(false), 2000);
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

# --- Parameters ---
N = 100000  # Number of bits/pulses 
mu = 0.2  # Mean photon number per pulse (simulated, not used directly)
L = 10  # Distance in km (for quantum channel)
# |+> = (|0> + |1>) / sqrt(2)
plus = (s0 + s1) / np.sqrt(2)

# |-> = (|0> - |1>) / sqrt(2)
minus = (s0 - s1) / np.sqrt(2)

def Rz(theta):
    # Returns a NetSquid Operator for a phase rotation by theta
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
        # Random phase (0 or π) for each pulse
        self.phases = np.random.choice([0, np.pi], size=num_bits + 1)  # DPS uses N+1 phases

    def run(self):
        print(f"\nAlice's phase choices:")
        for i, phase in enumerate(self.phases):
            ptxt = "0" if phase == 0 else "π"
            print(f"Pulse {i:2d}: {ptxt}")

        for i in range(self.num_bits+1):
            photon = np.random.poisson(mu)
            if photon == 1:
                qubit = create_qubits(1)[0]
                assign_qstate(qubit, plus)
                operate(qubit, Rz(self.phases[i]))
                msg = Message([qubit])
                msg.meta["is_vacuum"] = False
                self.node.ports["qout"].tx_output(msg)
                print(f"Alice: Pulse {i} sent photon")
            else:
                qubit = create_qubits(1)[0]
                msg = Message([qubit])
                msg.meta["is_vacuum"] = True
                self.node.ports["qout"].tx_output(msg)
                print(f"Alice: Pulse {i} sent vacuum")
            yield self.await_timer(1)  # Always yield at each step

class BobProtocol(NodeProtocol):
    def __init__(self, node, num_bits):
        super().__init__(node)
        self.num_bits = num_bits
        self.received_qubits = [None] * (num_bits + 1)  # To store all N+1 pulses

    def run(self):
        print("\nBob's detection events (with vacuum/meta logic):")
        for i in range(self.num_bits + 1):  # Receive all N+1 pulses
            yield self.await_port_input(self.node.ports["qin"])
            msg = self.node.ports["qin"].rx_input()  # msg is a Message object
            is_vacuum = msg.meta.get("is_vacuum", True)
            qubits = msg.items

            if is_vacuum or not qubits:
                print(f"  Pulse {i:2d}: Vacuum (dummy qubit)")
                self.received_qubits[i] = None
            else:
                print(f"  Pulse {i:2d}: Photon received")
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
                print(f"    Interference pulses {i},{i+1}: {bit}")
                bob_raw_key.append(bit)
            else:
                print(f"    Interference pulses {i},{i+1}: skipped (missing photon)")

        print("\nBob's sifted raw key:", bob_raw_key)
        print(f"Key length: {len(bob_raw_key)}")

# --- Setup Network ---
def setup_network():
    network = Network("DPS_QKD_Network")
    alice = Node("Alice", port_names=["qout"])
    bob = Node("Bob", port_names=["qin"])
    conn = QubitConnection(length_km=L)
    network.add_nodes([alice, bob])
    network.add_connection(alice, bob, connection=conn, label="quantum", port_name_node1="qout", port_name_node2="qin")
    return alice, bob

# --- Run the simulation ---
def run():
    ns.set_qstate_formalism(ns.QFormalism.KET)
    ns.sim_reset()
    alice, bob = setup_network()
    alice_protocol = AliceProtocol(alice, N)
    bob_protocol = BobProtocol(bob, N)
    alice_protocol.start()
    bob_protocol.start()
    ns.sim_run()

if __name__ == "__main__":
    run()

`,
COW: `import netsquid as ns
from netsquid.nodes import Node, DirectConnection
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.nodes import DirectConnection
from netsquid.protocols import Protocol
from netsquid.qubits import create_qubits, assign_qstate, ketstates, measure

import numpy as np
# can have as user inputs: mu, length, noise model, num_bits
class Alice(Protocol):
    def __init__(self, node, num_bits, delay=1, decoy_prob=0.1):
        super().__init__()
        self.actual_key = []
        self.sent_sequence=[]
        self.num_bits=num_bits
        self.decoy_prob=decoy_prob
        self.node=node
        self.delay=delay
        self.send_times_decoy=[]
    def run(self):
        mu=0.1
        for _ in range(self.num_bits):
            photon = np.random.poisson(mu)
            self.actual_key.append(photon) #for the poisson distribution of coherent states
        
        for i in range(self.num_bits):
            rand_val = np.random.rand()
     
            if rand_val < self.decoy_prob:
                # Send pulse at both early and late bins (decoy)
                pulse1, = create_qubits(1)
                pulse2, = create_qubits(1)
                ns.qubits.assign_qstate([pulse1],ketstates.s1)
                ns.qubits.assign_qstate([pulse2],ketstates.s1)

                self.node.ports["qout"].tx_output(pulse1)
                early_send_time=ns.sim_time()
                self.send_times_decoy.append(early_send_time)# Early
                yield self.await_timer(self.delay)
                self.node.ports["qout"].tx_output(pulse2)  # Late
                late_send_time=ns.sim_time()
                self.send_times_decoy.append(late_send_time)

                self.sent_sequence.append("D")
                
            else:
                pulse, = create_qubits(1)
                ns.qubits.assign_qstate([pulse],ketstates.s1)

                bit = self.actual_key[i]
                offset=0.1
                if bit == 1:
                    # Early pulse (bit 1)
                    yield self.await_timer(offset)  # wait a little before sending early pulse
                    self.node.ports["qout"].tx_output(pulse)
                    yield self.await_timer(2 * self.delay - offset)
                    self.sent_sequence.append(1)
                else:
                    # Late pulse (bit 0)
                    yield self.await_timer(self.delay+offset)
                    self.node.ports["qout"].tx_output(pulse)
                    yield self.await_timer(self.delay - offset)
                    self.sent_sequence.append(0)
        print("Alice: about to send decoy times:", self.send_times_decoy)
        self.node.ports["cout"].tx_output(Message(self.send_times_decoy))
        print("Alice: done sending.")

                #yield self.await_timer(self.delay)

            
class Bob(Protocol):
    def __init__(self, node, exp_pulses, dm2_thresh,f, delay=1, alice_protocol=None):
        super().__init__()
        self.node=node
        self.exp_pulses=exp_pulses
        self.dm2_thresh=dm2_thresh 
        self.f=f
        self.delay=delay
        self.recv_bits=[]
        self.recv_dict={}
        self.dm1_count=0
        self.dm_2_count=0
        self.total_received = 0
        self.sifted_key=[]
        self.alice_protocol = alice_protocol
        
    def simulate_intereference(self, pulse1, pulse2):
        res1, _ = measure(pulse1, observable=ns.X)
        res2, _ = measure(pulse2, observable=ns.X)
        res=res1^res2
        if res==1:
            return "DM1"
        else: return "DM2"
        
    def run(self):
        while self.total_received<self.exp_pulses:
            yield self.await_port_input(self.node.ports["qin"])
            msg=self.node.ports["qin"].rx_input()
           
            
            
            if np.random.rand()<self.f: #go to the monitoring line with a probability of f(generally 10%)
                        if len(msg.items)==2:
                            pulse1=msg.items[0]
                            pulse2=msg.items[1]
                            interfered=self.simulate_intereference(pulse1, pulse2)
                            if interfered=="DM1":
                                self.dm1_count+=1
                            else:
                                self.dm_2_count+=1
                            print("Deflected to monitoring line")
                        
            
                #go to dataline
            else:
                arrival_time = ns.sim_time()
                print(arrival_time)
                time_bin_pos = arrival_time % (2 * self.delay) #here each time bin is self.delay time
                if time_bin_pos<self.delay:
                    bit=1
                    self.recv_bits.append(1)
                else:
                    bit=0
                    self.recv_bits.append(0)
                self.recv_dict[arrival_time] = bit
            self.total_received += 1
        print("Bob: waiting to receive decoy times from Alice...")
        yield self.await_port_input(self.node.ports["cin"])
        print("Bob: received decoy times")

        
        msg = self.node.ports["cin"].rx_input()
        alice_decoy_times = msg.items
        epsilon = 0.1
        print("length of Alice dcoy times", len(msg.items))
        print("Message items:", msg.items)
        print("Type of msg.items[0]:", type(msg.items[0]))

        for recv_time, bit in self.recv_dict.items():
            if any(abs(recv_time - t) == 0 for t in alice_decoy_times):
                pass
   
            else:

                self.sifted_key.append(bit)
        print("Sifted key", self.sifted_key)


        

                
                
                
    

def run_cow_protocol(num_pulses=100, delay=1, depolar_rate=0.01):
    alice = Node("Alice", port_names=["qout", "cout"])
    bob = Node("Bob", port_names=["qin", "cin"])

# Create a quantum channel with optional depolarizing noise
    noise_model = DepolarNoiseModel(depolar_rate, time_independent=True)
    
    cchannel = QuantumChannel("cChannel_Alice_Bob",
                          length=10, #in km
                          models={"quantum_noise_model": noise_model})
    
    
    Classical_channel=ClassicalChannel("Channel_sift")
    quantum_connection = DirectConnection("conn_q_Alice_Bob", channel_AtoB=cchannel)
    classical_connection = DirectConnection("conn_c_Alice_Bob", channel_AtoB=Classical_channel)

    alice.connect_to(bob, connection=quantum_connection, local_port_name="qout", remote_port_name="qin")
    alice.connect_to(bob, connection=classical_connection, local_port_name="cout", remote_port_name="cin")




    alice_entity = Alice(alice, num_pulses, delay)
    bob_protocol = Bob(bob, exp_pulses=num_pulses, dm2_thresh=3, f=0.1, delay=delay, alice_protocol=alice_entity)

    
    alice_entity.start()
    bob_protocol.start()


    ns.sim_run()    
    print("Recv bits in main:", bob_protocol.recv_bits)
    print("Actual sequence sent: ", alice_entity.sent_sequence)
    print("Actual key: ", alice_entity.actual_key)
    #print("Sifted key:", bob_protocol.sifted_key)
    print("Classical channels and connections:")
    print(alice.ports)
    print(bob.ports)
   
''' count=0
    bit_indices = [i for i, val in enumerate(alice_entity.sent_sequence) if val != "D"]
    if(bob_protocol.dm_2_count>bob_protocol.dm2_thresh):
        print("Eavesdropper present. Abort!!!")

    for idx in bit_indices:
        if bob_protocol.recv_bits[idx] != alice_entity.actual_key[idx]:
            count += 1

    qber = count / len(bit_indices)
    
    for i in range(len(bob_protocol.recv_bits)):
        if(bob_protocol.recv_bits[i]!=alice_entity.actual_key[i]):
                count+=1
    qber=count/len(bob_protocol.recv_bits)
    print("QBER", qber)
    print("QBER", qber)
    return qber'''
run_cow_protocol()
`
  };

const protocolInfo ={
  DPS:``,
  COW:``
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


        <div className="control-group">
          <button 
            className="control-btn run-btn"
            onClick={handleRunSimulation}
            disabled={isRunning}
          >
            <img src={run} height={20} width={20} alt="run" />
            {isRunning ? 'Running...' : 'run'}
          </button>
        </div>

        <div className="control-group">
          <button 
            className="control-btn code-btn" 
            onClick={() => setShowCodePanel(!showCodePanel)}
          >
            <img src={code} height={20} width={20} alt="code" />
            view code
          </button>
        </div>
      </div>

      <div className="simulation-area">
  {(showAlice || showBob) && (
    <div className="quantum-channel">
      {/* First line: Alice, Connection/Animation, Bob */}
      <div className="quantum-line">
        {showAlice && (
          <div className="entity">
            <img src={alice} height={76} width={78} alt="alice" />
          </div>
        )}
        
        {showAlice && showBob && (
          <div className="connection-container">
            {!isRunning ? (
              <div className="connection-line" style={{ width: `${distance * 5}px` }}></div>
            ) : (
              <Loader />
            )}
          </div>
        )}
        
        {showBob && (
          <div className="entity">
            <img src={bob} height={76} width={78} alt="bob" />
          </div>
        )}
      </div>
      
      {/* Second line: QBER and Sifted Key (only during simulation) */}
      {showAlice && showBob && isRunning && (
        <div className="results-container">
          <div className="result-item">
            <p>The QBER is {QBER}%</p>
          </div>
          <div className="result-item">
            <p>The Sifted key is {sifted_key}</p>
          </div>
        </div>
      )}
    </div>
  )}
</div>
      <div><p>                        </p></div>
      <div className='simulation-area'>

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