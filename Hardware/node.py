from .channel import OpticalChannel
class Node:
    def __init__(self, node_id, env):
        self.node_id=node_id
        self.ports={} #port_id: port_name
        self.components={} #component_name: component_instance (basically all components should be classes)
        self.connections={} #sender_port_id: (target_node_id, target_port_id,  channel_object)
        self.env=env
        self.sent_log = []   # sending time of pulses, (send_time, sender_port_id, data)
        self.recv_log = []   # receiving time of pulses

    def assign_port(self, port_id, port_name):
        self.ports[port_id]=port_name
        
    def add_component(self, comp_name, comp_obj):
        self.components[comp_name]=comp_obj
        
    def connect_nodes(self, sender_port_id, receiver_port_id, receiver_node_id, channel_obj):
        self.connections[sender_port_id]=(receiver_node_id, receiver_port_id, channel_obj)
        
    def send(self, sender_port_id,  data):
        if sender_port_id not in self.connections:
            raise Exception(f"Port: {sender_port_id} not connected")
        receiver_node_id, receiver_port_id, channel = self.connections[sender_port_id]
        send_time = self.env.now
        self.sent_log.append((send_time, sender_port_id, data))

        result=channel.transmit(data)
        
        if result is None:
            print(f"Pulse lost during transmission on channel {channel.name}")
            return
        received_data, delay = result
        
        def delayed_delivery():
            yield self.env.timeout(delay) #advances time by this delay value, if it is 0, then bob receives as soon as alice sends
            
            receiver_node_id.receive(received_data, receiver_port_id)

        self.env.process(delayed_delivery())


        
    def receive(self, data, receiver_port_id):
        recv_time = self.env.now
        self.recv_log.append((recv_time, receiver_port_id, data))
        if hasattr(data, 'quantum_state'):
            print(f"[{self.node_id}] Received pulse on port '{receiver_port_id}':")
            print(f"  - Wavelength: {data.wavelength} m")
            print(f"  - Duration: {data.duration} s")
            print(f"  - Amplitude: {data.amplitude}")
            print(f"  - Phase: {data.phase}")
            print(f"  - Quantum State: {data.quantum_state}")
        else:
            print(f"[{self.node_id}] Received classical data on port '{receiver_port_id}': {data}")