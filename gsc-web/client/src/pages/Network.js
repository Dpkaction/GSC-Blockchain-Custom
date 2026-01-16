import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Network as NetworkIcon, 
  Wifi, 
  WifiOff, 
  Users, 
  Globe,
  Activity,
  Server,
  Zap,
  Clock,
  TrendingUp
} from 'lucide-react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useBlockchain } from '../contexts/BlockchainContext';

const Network = () => {
  const { isConnected, lastMessage } = useWebSocket();
  const { blockchainStats, mempool } = useBlockchain();
  const [networkStats, setNetworkStats] = useState({
    connectedPeers: 1,
    totalNodes: 4,
    networkHashRate: 0,
    avgBlockTime: 120,
    networkUptime: 0
  });

  useEffect(() => {
    // Simulate network statistics
    const interval = setInterval(() => {
      setNetworkStats(prev => ({
        ...prev,
        connectedPeers: Math.floor(Math.random() * 3) + 1,
        networkHashRate: Math.floor(Math.random() * 1000) + 500,
        networkUptime: prev.networkUptime + 1
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const seedNodes = [
    { name: 'seed1.gsccoin.network', status: 'online', latency: 45 },
    { name: 'seed2.gsccoin.network', status: 'online', latency: 67 },
    { name: 'seed3.gsccoin.network', status: 'offline', latency: 0 },
    { name: 'seed4.gsccoin.network', status: 'online', latency: 123 }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="page-container"
    >
      <div className="page-header">
        <h1 className="page-title">Network Status</h1>
        <p className="page-subtitle">
          Monitor GSC Coin network health and connectivity
        </p>
      </div>

      {/* Connection Status */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="connection-banner"
        style={{
          background: isConnected ? 'var(--gradient-success)' : 'var(--gradient-secondary)',
          padding: '1.5rem 2rem',
          borderRadius: '12px',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}
      >
        {isConnected ? <Wifi size={32} /> : <WifiOff size={32} />}
        <div>
          <h3 style={{ margin: 0, fontSize: '1.3rem' }}>
            {isConnected ? 'Connected to GSC Network' : 'Network Disconnected'}
          </h3>
          <p style={{ margin: 0, opacity: 0.9, fontSize: '1rem' }}>
            {isConnected 
              ? 'Real-time synchronization with blockchain network'
              : 'Attempting to reconnect to network nodes'
            }
          </p>
        </div>
      </motion.div>

      {/* Network Statistics */}
      <div className="stats-grid">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="stat-card"
        >
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            marginBottom: '1rem'
          }}>
            <Users size={24} style={{ color: 'var(--primary-color)' }} />
            <span style={{ 
              fontSize: '0.8rem', 
              color: isConnected ? 'var(--success-color)' : 'var(--error-color)',
              fontWeight: '600'
            }}>
              {isConnected ? 'Online' : 'Offline'}
            </span>
          </div>
          <div className="stat-value" style={{ color: 'var(--primary-color)' }}>
            {networkStats.connectedPeers}/{networkStats.totalNodes}
          </div>
          <div className="stat-label">Connected Peers</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="stat-card"
        >
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            marginBottom: '1rem'
          }}>
            <Zap size={24} style={{ color: 'var(--warning-color)' }} />
            <TrendingUp size={16} style={{ color: 'var(--success-color)' }} />
          </div>
          <div className="stat-value" style={{ color: 'var(--warning-color)' }}>
            {networkStats.networkHashRate.toLocaleString()}
          </div>
          <div className="stat-label">Network Hash Rate (H/s)</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="stat-card"
        >
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            marginBottom: '1rem'
          }}>
            <Clock size={24} style={{ color: 'var(--success-color)' }} />
            <span style={{ 
              fontSize: '0.8rem', 
              color: 'var(--success-color)',
              fontWeight: '600'
            }}>
              Target: 2min
            </span>
          </div>
          <div className="stat-value" style={{ color: 'var(--success-color)' }}>
            {networkStats.avgBlockTime}s
          </div>
          <div className="stat-label">Avg Block Time</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="stat-card"
        >
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            marginBottom: '1rem'
          }}>
            <Activity size={24} style={{ color: 'var(--accent-color)' }} />
            <span style={{ 
              fontSize: '0.8rem', 
              color: 'var(--success-color)',
              fontWeight: '600'
            }}>
              Live
            </span>
          </div>
          <div className="stat-value" style={{ color: 'var(--accent-color)' }}>
            {formatUptime(networkStats.networkUptime)}
          </div>
          <div className="stat-label">Network Uptime</div>
        </motion.div>
      </div>

      <div className="grid grid-2">
        {/* Seed Nodes */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="card"
        >
          <div className="card-header">
            <h3 className="card-title">Seed Nodes</h3>
            <Server className="card-icon" />
          </div>

          <div className="seed-nodes-list">
            {seedNodes.map((node, index) => (
              <motion.div
                key={node.name}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 + index * 0.1 }}
                className="seed-node-item"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '1rem',
                  background: 'var(--secondary-bg)',
                  borderRadius: '8px',
                  marginBottom: '0.5rem',
                  border: `1px solid ${node.status === 'online' ? 'var(--success-color)' : 'var(--error-color)'}`
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div 
                    style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: node.status === 'online' ? 'var(--success-color)' : 'var(--error-color)',
                      animation: node.status === 'online' ? 'pulse 2s infinite' : 'none'
                    }}
                  />
                  <div>
                    <div style={{ 
                      fontWeight: '600', 
                      color: 'var(--text-primary)',
                      marginBottom: '0.25rem'
                    }}>
                      {node.name}
                    </div>
                    <div style={{ 
                      fontSize: '0.8rem', 
                      color: 'var(--text-secondary)' 
                    }}>
                      {node.status === 'online' ? `${node.latency}ms latency` : 'Offline'}
                    </div>
                  </div>
                </div>
                <div style={{
                  padding: '0.25rem 0.75rem',
                  borderRadius: '12px',
                  fontSize: '0.8rem',
                  fontWeight: '600',
                  background: node.status === 'online' 
                    ? 'rgba(0, 255, 136, 0.1)' 
                    : 'rgba(255, 71, 87, 0.1)',
                  color: node.status === 'online' ? 'var(--success-color)' : 'var(--error-color)'
                }}>
                  {node.status.toUpperCase()}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Network Activity */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.8 }}
          className="card"
        >
          <div className="card-header">
            <h3 className="card-title">Network Activity</h3>
            <Globe className="card-icon" />
          </div>

          <div className="network-activity">
            <div className="activity-item" style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '1rem',
              background: 'var(--secondary-bg)',
              borderRadius: '8px',
              marginBottom: '1rem'
            }}>
              <div>
                <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                  Mempool Transactions
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Pending transactions waiting for mining
                </div>
              </div>
              <div style={{ 
                fontSize: '1.5rem', 
                fontWeight: '700',
                color: 'var(--warning-color)'
              }}>
                {mempool.length}
              </div>
            </div>

            <div className="activity-item" style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '1rem',
              background: 'var(--secondary-bg)',
              borderRadius: '8px',
              marginBottom: '1rem'
            }}>
              <div>
                <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                  Total Blocks
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Blocks mined on the network
                </div>
              </div>
              <div style={{ 
                fontSize: '1.5rem', 
                fontWeight: '700',
                color: 'var(--primary-color)'
              }}>
                {blockchainStats?.totalBlocks || 0}
              </div>
            </div>

            <div className="activity-item" style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '1rem',
              background: 'var(--secondary-bg)',
              borderRadius: '8px',
              marginBottom: '1rem'
            }}>
              <div>
                <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                  Mining Difficulty
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Fixed difficulty (4 leading zeros)
                </div>
              </div>
              <div style={{ 
                fontSize: '1.5rem', 
                fontWeight: '700',
                color: 'var(--accent-color)'
              }}>
                {blockchainStats?.difficulty || 5}
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Network Information */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.0 }}
        className="card"
        style={{ marginTop: '2rem' }}
      >
        <div className="card-header">
          <h3 className="card-title">Network Information</h3>
          <NetworkIcon className="card-icon" />
        </div>

        <div className="grid grid-3">
          <div className="network-info-section">
            <h4 style={{ 
              color: 'var(--primary-color)', 
              marginBottom: '1rem',
              fontSize: '1.1rem'
            }}>
              Protocol
            </h4>
            <div className="info-list">
              <div className="info-item">
                <span>Version:</span>
                <span>GSC v1.0.0</span>
              </div>
              <div className="info-item">
                <span>Network ID:</span>
                <span>1 (Mainnet)</span>
              </div>
              <div className="info-item">
                <span>Port:</span>
                <span>8333</span>
              </div>
            </div>
          </div>

          <div className="network-info-section">
            <h4 style={{ 
              color: 'var(--success-color)', 
              marginBottom: '1rem',
              fontSize: '1.1rem'
            }}>
              Consensus
            </h4>
            <div className="info-list">
              <div className="info-item">
                <span>Algorithm:</span>
                <span>Proof of Work</span>
              </div>
              <div className="info-item">
                <span>Hash Function:</span>
                <span>SHA-256</span>
              </div>
              <div className="info-item">
                <span>Block Time:</span>
                <span>2 minutes</span>
              </div>
            </div>
          </div>

          <div className="network-info-section">
            <h4 style={{ 
              color: 'var(--warning-color)', 
              marginBottom: '1rem',
              fontSize: '1.1rem'
            }}>
              Economics
            </h4>
            <div className="info-list">
              <div className="info-item">
                <span>Block Reward:</span>
                <span>50 GSC</span>
              </div>
              <div className="info-item">
                <span>Halving:</span>
                <span>4 years</span>
              </div>
              <div className="info-item">
                <span>Max Supply:</span>
                <span>21.75T GSC</span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      <style jsx>{`
        .info-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        
        .info-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 0;
          border-bottom: 1px solid var(--border-color);
          font-size: 0.9rem;
        }
        
        .info-item span:first-child {
          color: var(--text-secondary);
        }
        
        .info-item span:last-child {
          color: var(--text-primary);
          font-weight: 600;
        }
      `}</style>
    </motion.div>
  );
};

export default Network;
