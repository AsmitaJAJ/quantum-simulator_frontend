import React, { useState } from 'react';
import styled from 'styled-components';
import './App.css';
import GitNav from './GithubNav';
import icon from './assets/icon.gif';
import qkd from './assets/qkd.png'
import { Link } from 'react-router-dom';

const App = () => {
  return (
    <div className="landing-page">
      {/* Navigation */}
      <nav className="navbar">
        <div className="container">
          <div className="logo">Quantum Simulator</div>
          <ul className="nav-links">
            <li><a href="#home" className='menu__link'>Home</a></li>
            <li><a href="#features" className='menu__link'>Features</a></li>
            <li><a href="https://anuzka115.github.io/quantum-simulator/" className='menu__link'>Documentation</a></li>
            <GitNav/>
          </ul>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <h1>Quantum Simulator</h1>
            <p className="subtitle">
              
              Implement a combination of core quantum mechanics, networking protocols, and real-world constraints. 
              Visualise and simulate protocols before deploying.
            </p>
            <StyledWrapper>
      <button>
        Read More
      </button>
    </StyledWrapper>
          </div>
          <div className="hero-image">
            <div className="quantum-visualization">
                <img src={icon} height={250} width={500} alt="landing-page.gif" />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features">
        <div className="container">
          <h2>Key Features</h2>
          <div className="features-grid">
            <div className="feature-card">
              <Link to="qkd"><div className="feature-icon"><img src={qkd} height={100} width={100} alt="Logo" /> <h3>Quantum Key Distribution</h3></div></Link>
              <p>Simulate QKD protocols with customizable parameters.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon"></div>
              <h3>Placeholder</h3>
              <p>Lorem ipsum, dolor sit amet consectetur adipisicing elit. </p>
            </div><div className="feature-card">
              <div className="feature-icon"></div>
              <h3>Placeholder</h3>
              <p>Lorem ipsum, dolor sit amet consectetur adipisicing elit. </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div></div>
      </footer>
    </div>
  );
};
const StyledWrapper = styled.div`
  button {
    width: fit-content;
    min-width: 100px;
    height: 45px;
    padding: 8px;
    border-radius: 5px;
    border: 2.5px solid #E0E1E4;
    box-shadow: 0px 0px 20px -20px;
    cursor: pointer;
    background-color: white;
    transition: all 0.2s ease-in-out 0ms;
    user-select: none;
    font-family: 'Poppins', sans-serif;
  }

  button:hover {
    background-color: #F2F2F2;
    box-shadow: 0px 0px 20px -18px;
  }

  button:active {
    transform: scale(0.95);
  }`;

export default App;