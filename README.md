# 🧪 Quantum Simulator

This repository contains the codebase for the **Quantum Simulator** developed as part of a team project by **Team Hiesenberg + Quantastic** at IISER. It features a visual simulator for quantum key distribution (QKD) protocols, with an intuitive GUI and back-end integration using NetSquid.

---

## Team Progress

### Week 1
- Studied **NetSquid** (Network Simulator for Quantum Information using Discrete Events) to understand existing standards and benchmarking tools for quantum simulations.

### Week 2
- Developed the basic GUI using **React + Vite**.
- Simulated **COW-QKD** and **DPS-QKD** protocols using NetSquid.

### Week 3
- Enhanced GUI with **drag-and-drop features**.
- Developed and integrated **quantum channel** logic in the backend with frontend using Flask.

---

## Project Structure

### 🔧 Backend
- Simulation code written in **Python + NetSquid**.
- Includes simulation for:
  - **DPS (Differential Phase Shift)** QKD Protocol
  - **COW (Coherent One-Way)** QKD Protocol
- Outputs:
  - **QBER Rate**
  - **Sifted Keys** for Alice and Bob.

### 🔌 Server Integration
- Uses **Flask** to expose Python simulations to the frontend via API (`server.py`).

### Frontend
- Built with **React + Vite**.
- Main components located under `src/`.
- Available routes:
  - `App.jsx` → Landing Page
  - `Qkd.jsx` → Routes to `Qkdsimulator.jsx` for QKD Protocol interface.

### Styling
- Pure **CSS** for styling.
- **React Router DOM** is used for routing.

---

## Running Locally

### 📦 Prerequisites
- **NetSquid** (Install from [netsquid.org](https://netsquid.org/))  
  > _Note_: NetSquid supports **Python 3.6–3.12 only**. Use a virtual environment if needed.
- **Python** (3.6–3.12)
- **Flask**
- **npm**
- **Vite**

### 🛠️ Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/anuzka115/quantum-simulator.git
   cd quantum-simulator

2. **Start bakend server**
    ```bash
    python server.py

3. **Install Node dependencies and run frontend**
    ```bash
    npm install
    npm run dev

4. **Access the simulator at:**
    http://localhost:5173


##  Next Milestones

- Implement **DPS**, **COW**, and **BB84** QKD protocols in our **own backend**.
- Move away from NetSquid by learning from its **limitations and integration issues**.
- Ensure modular, scalable simulation logic that can be extended to other QKD protocols.
- Benchmark and compare performance of our backend vs NetSquid-based simulations.