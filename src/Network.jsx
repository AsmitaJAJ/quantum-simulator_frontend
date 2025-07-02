// QuantumTopologySelector.jsx
import axios from 'axios';

import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './network.css';

const cities = ['Mumbai', 'Pune', 'Bangalore', 'Chennai', 'Surat', 'Nagpur'];
const cityCoordinates = {
  Mumbai: [19.076, 72.8777],
  Pune: [18.5204, 73.8567],
  Bangalore: [12.9716, 77.5946],
  Chennai: [13.0827, 80.2707],
  Surat: [21.1702, 72.8311],
  Nagpur: [21.1458, 79.0882]
};

const topologies = ['Star', 'Mesh', 'Ring'];
const protocols = ['BB84', 'DPS', 'COW'];

function haversineDistance(coord1, coord2) {
  const toRad = deg => (deg * Math.PI) / 180;
  const R = 6371; // Radius of Earth in km
  const [lat1, lon1] = coord1;
  const [lat2, lon2] = coord2;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return (R * c).toFixed(2); // in km
}

const generateEdges = (topology, nodes) => {
  const edges = [];
  if (topology === 'Star') {
    for (let i = 1; i < nodes.length; i++) {
      edges.push([nodes[0], nodes[i]]);
    }
  } else if (topology === 'Ring') {
    for (let i = 0; i < nodes.length; i++) {
      edges.push([nodes[i], nodes[(i + 1) % nodes.length]]);
    }
  } else if (topology === 'Mesh') {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        edges.push([nodes[i], nodes[j]]);
      }
    }
  }
  return edges;
};

function Network() {
  const [numNodes, setNumNodes] = useState(2);
  const [topology, setTopology] = useState('Star');
  const [selectedCities, setSelectedCities] = useState(Array(2).fill(''));
  const [protocolsPerEdge, setProtocolsPerEdge] = useState({});
  const [edges, setEdges] = useState([]);
  const [submitted, setSubmitted] = useState(false);
  const [visualize, setVisualize] = useState(false);
  const [simulationResults, setSimulationResults] = useState([]);

  const handleCityChange = (index, value) => {
    const updated = [...selectedCities];
    updated[index] = value;
    setSelectedCities(updated);
    setSubmitted(false);
    setVisualize(false);
  };

  const handleProtocolChange = (edgeKey, value) => {
    setProtocolsPerEdge(prev => ({ ...prev, [edgeKey]: value }));
  };

  const handleGenerateEdges = () => {
    const edgesGenerated = generateEdges(topology, selectedCities);
    setEdges(edgesGenerated);
    setSubmitted(true);
    setVisualize(false);
  };

  const handleRun = () => {
    const payload = {
      cities: selectedCities,
      topology: topology,
      edges: edges,
      protocols: protocolsPerEdge
    };
  
    axios.post("http://localhost:5000/simulate", payload)
      .then(response => {
        setSimulationResults(response.data.results);
        setVisualize(true);
      })
      .catch(error => {
        console.error("Simulation error:", error);
        alert("Simulation failed. Check backend logs.");
      });
  };
  

  const allCitiesSelected = selectedCities.every(city => city);
  const allProtocolsSelected = edges.every(([a, b]) => {
    const key1 = `${a}-${b}`;
    const key2 = `${b}-${a}`;
    return protocolsPerEdge[key1] || protocolsPerEdge[key2];
  });

  return (
    <div className="container1">
      <div className="sidebar1">
        <div className="form-group">
          <label>Select no. nodes</label>
          <select value={numNodes} onChange={e => {
            const val = parseInt(e.target.value);
            setNumNodes(val);
            setSelectedCities(Array(val).fill(''));
            setSubmitted(false);
            setVisualize(false);
          }}>
            {[2, 3, 4, 5, 6].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label>Select topology</label>
          <select value={topology} onChange={e => {
            setTopology(e.target.value);
            setSubmitted(false);
            setVisualize(false);
          }}>
            {topologies.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        {selectedCities.map((_, index) => (
          <div className="form-group" key={index}>
            <label>Select city {index + 1}</label>
            <select
              value={selectedCities[index] || ''}
              onChange={e => handleCityChange(index, e.target.value)}>
              <option value="">--Select City--</option>
              {cities.map(city => <option key={city} value={city}>{city}</option>)}
            </select>
          </div>
        ))}

        {allCitiesSelected && (
          <button className="run-btn" onClick={handleGenerateEdges}>Next: Select Protocols</button>
        )}

        {submitted && (
          <div className="form-group">
            <label>Select protocols for edges</label>
            {edges.map(([a, b]) => {
              const edgeKey = `${a}-${b}`;
              return (
                <div key={edgeKey} className="protocol-select">
                  <span>{a} - {b}</span>
                  <select
                    value={protocolsPerEdge[edgeKey] || ''}
                    onChange={e => handleProtocolChange(edgeKey, e.target.value)}>
                    <option value="">--Protocol--</option>
                    {protocols.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
              );
            })}

            {allProtocolsSelected && (
              <button onClick={handleRun} className="run-btn">Run</button>
            )}
          </div>
        )}
      </div>
      <div className='content-imp'>
      <div className="main1 visualize-container">
        <div className="map-container" style={{ height: '500px', width: '600px' }}>
          <MapContainer
            center={[22.5937, 78.9629]}
            zoom={4}
            minZoom={4}
            maxZoom={6}
            style={{ height: '100%', width: '100%' }}
            scrollWheelZoom={true}
            maxBounds={[[6.5, 67], [38.5, 97]]}
            maxBoundsViscosity={1.0}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {selectedCities.filter(c => cityCoordinates[c]).map((city, idx) => (
              <Marker key={idx} position={cityCoordinates[city]}>
                <Popup>{city}</Popup>
              </Marker>
            ))}
            {edges.map(([cityA, cityB], i) => {
              const coordA = cityCoordinates[cityA];
              const coordB = cityCoordinates[cityB];
              if (coordA && coordB) {
                return <Polyline key={i} positions={[coordA, coordB]} pathOptions={{ color: 'red', weight: 3 }} />;
              }
              return null;
            })}
          </MapContainer>
        </div>
        {visualize && (
  <div className="results right-of-map">
    <h3>Simulation Results</h3>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Link</th>
          <th>Protocol</th>
          <th>QBER</th>
          <th>Sender Last Sent</th>
          <th>Receiver Last Recv</th>
        </tr>
      </thead>
      <tbody>
        {simulationResults.map((res, idx) => {
          const nodes = Object.keys(res.nodes);
          const sender = nodes.find(n => res.nodes[n].last_sent_time);
          const receiver = nodes.find(n => res.nodes[n].last_recv_time);

          return (
            <tr key={idx}>
              <td>{idx + 1}</td>
              <td>{res.link}</td>
              <td>{res.protocol}</td>
              <td>{res.qber}</td>
              <td>{sender ? res.nodes[sender].last_sent_time : "N/A"}</td>
              <td>{receiver ? res.nodes[receiver].last_recv_time : "N/A"}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  </div>
)}

      </div>
      </div>
    </div>
  );
}

export default Network;