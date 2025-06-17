'''transmittance=10^(-alpha*L/10), loss=1-transmittance. alpha= attenuation in dB/mm'''

import numpy as np
from .state import QuantumState
class OpticalChannel:
    def __init__(self, name, length_meters, attenuation_db_per_m, light_speed=2e8):
        self.name = name #name of channel
        self.length = length_meters #total length
        self.attenuation = attenuation_db_per_m #alpha, basically
        self.light_speed = light_speed




    def compute_loss(self):
        return 1 - 10 ** (-self.attenuation * self.length / 10)  #refer above comment

    def compute_delay(self):
        return self.length / self.light_speed

'''Inherits from optical channel. But it also has the feature of depolarization of the pulse as an added extra'''
class QuantumChannel(OpticalChannel):
    def __init__(self, name, length_meters, attenuation_db_per_m, depol_prob=0.0, light_speed=2e8):
        super().__init__(name, length_meters, attenuation_db_per_m, light_speed) 
        self.depol_prob = depol_prob

    def transmit(self, pulse):
        loss_prob = self.compute_loss()
        if np.random.random() < loss_prob:
            return None  # Pulse lost
        if pulse.quantum_state and np.random.random() < self.depol_prob:
            pulse.quantum_state.depolarize()
        delay = self.compute_delay()
        return (pulse, delay)
    
'''Also inherits from optical channel. Has no loss faxtor, just delay.''' 
class ClassicalChannel(OpticalChannel):
    def transmit(self, message):
        delay = self.compute_delay()
        return (message, delay)
