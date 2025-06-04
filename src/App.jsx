import React, { useState } from 'react';
import './App.css';
import Button from './Button';
import Button1 from './Button1';
import icon from './assets/icon.gif';
import qkd from './assets/qkd.png'
import { Link } from 'react-router-dom';
const QuantumCommunicationSimulator = () => {
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you would typically send the email to your backend
    console.log('Submitted email:', email);
    setSubscribed(true);
    setEmail('');
    setTimeout(() => setSubscribed(false), 3000);
  };

  return (
    <div className="landing-page">
      {/* Navigation */}
      <nav className="navbar">
        <div className="container">
          <div className="logo">Quantum Simulator</div>
          <ul className="nav-links">
            <li><a href="#home">Home</a></li>
            <li><a href="#features">Features</a></li>
            <li><a href="#documentation">Documentation</a></li>
            <li><Button/></li>
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
            <Button1/>
          </div>
          <div className="hero-image">
            <div className="quantum-visualization">
                <img src={icon} height={250} width={500} alt="Logo" />
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
              <Link to="qkd"><div className="feature-icon"><img src={qkd} height={100} width={100} alt="Logo" /> <h3>Quantum Key Distribution</h3></div>
</Link>

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

export default QuantumCommunicationSimulator;