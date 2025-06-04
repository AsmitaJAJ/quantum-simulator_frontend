import netsquid as ns
from netsquid.nodes import Node, DirectConnection
from netsquid.qubits import create_qubits, assign_qstate
from netsquid.components import QuantumErrorModel, ClassicalChannel, QSource
from netsquid.components.models.qerrormodels import DepolarNoiseModel
from netsquid.nodes import DirectConnection
from netsquid.protocols import Protocol
import numpy as np
class Alice(Protocol):
    
    def __init__(self, node, num_pulses, delay=1):
        super().__init__()
        self.node=node
        self.actual_key=[]
        
        self.num_pulses=num_pulses
       
        self.phases = np.random.choice([0, np.pi], size=num_pulses)
        
        
        for i in range(len(self.phases)):
            if(i>0):
                ph_d=abs(self.phases[i] - self.phases[i-1] % (2 * np.pi))
                bit = int(ph_d / np.pi)
                self.actual_key.append(bit)
                
        
        self.delay=delay
    def run(self):
        
        for i in range(self.num_pulses):
            
        
            self.node.ports["qout"].tx_output(self.phases[i])
            yield self.await_timer(self.delay)
class Bob(Protocol):
    def __init__(self, node):
        super().__init__()
        self.node=node
        self.received_bits=[]
        self.buf=[]
        
        
    def run(self):
        while True:
            yield self.await_port_input(self.node.ports["qin"])
            msg = self.node.ports["qin"].rx_input()
            phs = msg.items[0]
            self.buf.append(phs)
            #print("Buffer: ",self.buf)
            if(len(self.buf)>=2):
                phi_prev=self.buf[-2]
                phi_cur=self.buf[-1]
                phase_diff = (phi_cur - phi_prev) % (2 * np.pi)
                bit = int(phase_diff / np.pi)  # 0 if same, 1 if π phase difference
                self.received_bits.append(bit)
                #print(self.received_bits)
                
        
            

def run_dps_protocol(num_pulses=10, delay=1, depolar_rate=0.01):
    alice = Node("Alice", port_names=["qout"])
    bob = Node("Bob", port_names=["qin"])

# Create a quantum channel with optional depolarizing noise
    noise_model = DepolarNoiseModel(depolar_rate, time_independent=True)
    cchannel = ClassicalChannel("cChannel_Alice_Bob",
                          length=10, #in km
                          models={"quantum_noise_model": noise_model})
    connection = DirectConnection("conn[Alice->Bob]", channel_AtoB=cchannel)

    alice.connect_to(bob, connection=connection,
                 local_port_name="qout",
                 remote_port_name="qin")
    alice_entity = Alice(alice, num_pulses, delay)
    bob_protocol = Bob(bob)
    
    alice_entity.start()
    bob_protocol.start()
 

    ns.sim_run()    
    print("Recv bits in main:", bob_protocol.received_bits)
   
    count=0
    for i in range(len(bob_protocol.received_bits)):
        if(bob_protocol.received_bits[i]!=alice_entity.actual_key[i]):
                count+=1
    qber=count/len(bob_protocol.received_bits)
    print("QBER", qber)
    return qber
    print("QBER", qber)
run_dps_protocol()