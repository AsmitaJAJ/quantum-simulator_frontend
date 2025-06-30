
import numpy as np

H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)

CX = np.array([
    [1, 0, 0, 0],  
    [0, 1, 0, 0],  
    [0, 0, 0, 1],  
    [0, 0, 1, 0],  
], dtype=complex)