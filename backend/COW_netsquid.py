import netsquid as ns
from netsquid.nodes import Node, DirectConnection
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.components import QuantumChannel, ClassicalChannel, Message
from netsquid.nodes import DirectConnection
from netsquid.protocols import Protocol
from netsquid.qubits import create_qubits, assign_qstate, ketstates, measure
import random
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
        self.sifted_key_alice=[]
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
                self.sifted_key_alice.append(bit)
        #print("Alice: about to send decoy times:", self.send_times_decoy)
        self.node.ports["cout"].tx_output(Message(self.send_times_decoy))
        #print("Alice: done sending.")

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
                #print(arrival_time)
                time_bin_pos = arrival_time % (2 * self.delay) #here each time bin is self.delay time
                if time_bin_pos<self.delay:
                    bit=1
                    self.recv_bits.append(1)
                else:
                    bit=0
                    self.recv_bits.append(0)
                self.recv_dict[arrival_time] = bit
            self.total_received += 1
        #print("Bob: waiting to receive decoy times from Alice...")
        yield self.await_port_input(self.node.ports["cin"])
        #print("Bob: received decoy times")

        
        msg = self.node.ports["cin"].rx_input()
        alice_decoy_times = msg.items
        epsilon = 0.1
        #print("length of Alice dcoy times", len(msg.items))
        #print("Message items:", msg.items)
       # print("Type of msg.items[0]:", type(msg.items[0]))

        for recv_time, bit in self.recv_dict.items():
            if any(abs(recv_time - t) == 0 for t in alice_decoy_times):
                pass
   
            else:

                self.sifted_key.append(bit)
        #print("Bob's Sifted key", self.sifted_key)


        

                
                
                
    

def run_cow_protocol(num_pulses=10, delay=1, depolar_rate=0.01, length=1, noise_model="DepolarNoiseModel"):
    alice = Node("Alice", port_names=["qout", "cout"])
    bob = Node("Bob", port_names=["qin", "cin"])

# Create a quantum channel with optional depolarizing noise
    noise_model = DepolarNoiseModel(depolar_rate, time_independent=True)
    
    cchannel = QuantumChannel("cChannel_Alice_Bob",
                          length=length, #in km
                          models={"quantum_noise_model": noise_model})
    
    
    Classical_channel=ClassicalChannel("Channel_sift")
    quantum_connection = DirectConnection("conn_q_Alice_Bob", channel_AtoB=cchannel)
    classical_connection = DirectConnection("conn_c_Alice_Bob", channel_AtoB=Classical_channel)

    alice.connect_to(bob, connection=quantum_connection, local_port_name="qout", remote_port_name="qin")
    alice.connect_to(bob, connection=classical_connection, local_port_name="cout", remote_port_name="cin")




    alice_entity = Alice(alice, num_pulses, delay)
    bob_protocol = Bob(bob, exp_pulses=num_pulses, dm2_thresh=3, f=0.0, delay=delay, alice_protocol=alice_entity)

    
    alice_entity.start()
    bob_protocol.start()


    ns.sim_run() 
    count=0   
    #print("Recv bits in main:", bob_protocol.recv_bits)
    #print("Actual sequence sent: ", alice_entity.sent_sequence)
    min_len = min(len(alice_entity.sifted_key_alice), len(bob_protocol.sifted_key))

# Step 2: Select 20% of indices randomly
    sample_size = int(0.3 * min_len)
    sample_indices = random.sample(range(min_len), sample_size)

# Step 3: Compare selected bits
    errors = sum(
    1 for i in sample_indices
    if alice_entity.sifted_key_alice[i] != bob_protocol.sifted_key[i]
    )

    qber = errors / sample_size if sample_size > 0 else 0
    print(qber)
    return qber, alice_entity.sifted_key_alice, bob_protocol.sifted_key
   

run_cow_protocol()

        
    