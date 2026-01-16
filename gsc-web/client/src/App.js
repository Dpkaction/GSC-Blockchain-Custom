import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import EnhancedWallet from './pages/EnhancedWallet';
import Mining from './pages/Mining';
import Explorer from './pages/Explorer';
import Network from './pages/Network';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { BlockchainProvider } from './contexts/BlockchainContext';
import LoadingScreen from './components/LoadingScreen';
import './App.css';

function App() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate app initialization
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <WebSocketProvider>
      <BlockchainProvider>
        <Router>
          <div className="App">
            <Navbar />
            <main className="main-content">
              <AnimatePresence mode="wait">
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/wallet" element={<EnhancedWallet />} />
                  <Route path="/mining" element={<Mining />} />
                  <Route path="/explorer" element={<Explorer />} />
                  <Route path="/network" element={<Network />} />
                </Routes>
              </AnimatePresence>
            </main>
            <Toaster 
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#1a1a2e',
                  color: '#fff',
                  border: '1px solid #16213e',
                },
              }}
            />
          </div>
        </Router>
      </BlockchainProvider>
    </WebSocketProvider>
  );
}

export default App;
