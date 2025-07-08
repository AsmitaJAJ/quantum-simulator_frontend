# Quantum Simulator

The Quantum Simulator is an educational and experimental tool designed to simulate quantum key distribution (QKD) protocols with realistic noise and error models. Developed by **Team Hiesenberg + Quantastic** at IISER Bhopal, the simulator offers both a backend simulation engine and a user-friendly interface for interactive exploration.

## Project Overview

This project aims to bridge the gap between theoretical QKD concepts and practical implementation by allowing users to:

- Simulate various QKD protocols under realistic conditions
- Introduce and visualize noise, loss, and imperfections
- Explore secure key exchange across network topologies

## Features

- **Custom Simulation Engine**  
  Built from scratch, supporting multiple QKD protocols with adjustable error models and parameters.

- **Interactive UI**  
  Allows users to:
  - Select the number of nodes in the QKD network
  - Choose network topology (e.g., linear, mesh)
  - Pick cities on the map of India to form nodes
  - Assign QKD protocols to edges (e.g., BB84, B92)

- **Real-Time Visualization**  
  View key simulation metrics such as:
  - Quantum Bit Error Rate (QBER)
  - Key rate
  - Sender's last sent bits
  - Receiver's last received bits

## Use Cases

The simulator can be used for:

- Demonstrating QKD to students and researchers
- Exploring protocol performance under realistic conditions
- Testing the effects of different topologies and parameters

## Running Locally

1. **Install Python dependencies** (for the backend):
   ```
   pip install flask flask-cors simpy
   ```

2. **Start the backend server:**
    ```
    python app.py
    ```

3. **Install frontend dependencies:**
    ```
    npm install    ```

4. **Run the frontend:**
    ```
    npm run dev
    ```
