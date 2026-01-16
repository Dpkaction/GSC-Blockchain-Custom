import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Hammer, 
  Play, 
  Square, 
  Zap, 
  Clock, 
  Target,
  TrendingUp,
  Award,
  Activity
} from 'lucide-react';
import { useBlockchain } from '../contexts/BlockchainContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import toast from 'react-hot-toast';

const Mining = () => {
  const { miningStatus, startMining, stopMining, mempool } = useBlockchain();
  const { lastMessage } = useWebSocket();
  const [minerAddress, setMinerAddress] = useState('');
  const [miningStats, setMiningStats] = useState({
    nonce: 0,
    hashRate: 0,
    target: '',
    hash: ''
  });
  const [isLoading, setIsLoading] = useState(false);

  // Load saved miner address
  useEffect(() => {
    const savedAddress = localStorage.getItem('gsc_miner_address');
    if (savedAddress) {
      setMinerAddress(savedAddress);
    }
  }, []);

  // Update mining stats from WebSocket
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'mining_update') {
      setMiningStats(lastMessage.data);
    }
  }, [lastMessage]);

  const handleStartMining = async () => {
    if (!minerAddress) {
      toast.error('Please enter a miner address');
      return;
    }

    setIsLoading(true);
    try {
      const result = await startMining(minerAddress);
      if (result.success) {
        localStorage.setItem('gsc_miner_address', minerAddress);
        toast.success(result.message);
      } else {
        toast.error(result.message);
      }
    } catch (error) {
      toast.error('Failed to start mining');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopMining = async () => {
    setIsLoading(true);
    try {
      const result = await stopMining();
      if (result.success) {
        toast.success('Mining stopped');
        setMiningStats({ nonce: 0, hashRate: 0, target: '', hash: '' });
      } else {
        toast.error(result.message);
      }
    } catch (error) {
      toast.error('Failed to stop mining');
    } finally {
      setIsLoading(false);
    }
  };

  const formatHashRate = (rate) => {
    if (rate >= 1000000) {
      return `${(rate / 1000000).toFixed(2)} MH/s`;
    } else if (rate >= 1000) {
      return `${(rate / 1000).toFixed(2)} KH/s`;
    } else {
      return `${rate.toFixed(0)} H/s`;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="page-container"
    >
      <div className="page-header">
        <h1 className="page-title">Smart Mining</h1>
        <p className="page-subtitle">
          Mine GSC coins efficiently - only mines when transactions are available
        </p>
      </div>

      {/* Mining Status Banner */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="mining-status-banner"
        style={{
          background: miningStatus.isMining 
            ? 'var(--gradient-success)' 
            : mempool.length > 0 
              ? 'var(--gradient-primary)'
              : 'var(--gradient-secondary)',
          padding: '1.5rem 2rem',
          borderRadius: '12px',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}
      >
        <Hammer size={32} />
        <div>
          <h3 style={{ margin: 0, fontSize: '1.3rem' }}>
            {miningStatus.isMining 
              ? 'Mining Active' 
              : mempool.length > 0 
                ? 'Ready to Mine'
                : 'Waiting for Transactions'
            }
          </h3>
          <p style={{ margin: 0, opacity: 0.9, fontSize: '1rem' }}>
            {miningStatus.isMining 
              ? `Mining to: ${miningStatus.minerAddress?.substring(0, 20)}...`
              : mempool.length > 0 
                ? `${mempool.length} transactions ready for mining`
                : 'Smart mining will start automatically when transactions are available'
            }
          </p>
        </div>
      </motion.div>

      <div className="grid grid-2">
        {/* Mining Control */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="card-header">
            <h3 className="card-title">Mining Control</h3>
            <Zap className="card-icon" />
          </div>

          <div className="form-group">
            <label className="form-label">Miner Address</label>
            <input
              type="text"
              className="form-input"
              placeholder="Enter your GSC address to receive mining rewards..."
              value={minerAddress}
              onChange={(e) => setMinerAddress(e.target.value)}
              disabled={miningStatus.isMining}
            />
            <small style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              Mining rewards will be sent to this address
            </small>
          </div>

          <div style={{ 
            display: 'flex', 
            gap: '1rem', 
            marginTop: '1.5rem' 
          }}>
            {!miningStatus.isMining ? (
              <button
                className="btn btn-success btn-lg"
                onClick={handleStartMining}
                disabled={isLoading || !minerAddress}
                style={{ flex: 1 }}
              >
                <Play size={20} />
                {mempool.length > 0 ? 'Start Mining' : 'Start Smart Mining'}
              </button>
            ) : (
              <button
                className="btn btn-danger btn-lg"
                onClick={handleStopMining}
                disabled={isLoading}
                style={{ flex: 1 }}
              >
                <Square size={20} />
                Stop Mining
              </button>
            )}
          </div>

          {/* Mining Info */}
          <div style={{ 
            marginTop: '1.5rem',
            padding: '1rem',
            background: 'var(--secondary-bg)',
            borderRadius: '8px',
            border: '1px solid var(--border-color)'
          }}>
            <h4 style={{ 
              margin: '0 0 1rem 0', 
              color: 'var(--primary-color)',
              fontSize: '1rem'
            }}>
              Smart Mining Features
            </h4>
            <ul style={{ 
              margin: 0, 
              paddingLeft: '1.2rem',
              color: 'var(--text-secondary)',
              fontSize: '0.9rem'
            }}>
              <li>Only mines when transactions are available</li>
              <li>Automatic mining when mempool has transactions</li>
              <li>Fixed difficulty of 5 (4 leading zeros)</li>
              <li>2-minute average block time</li>
              <li>50 GSC block reward (halving every 4 years)</li>
            </ul>
          </div>
        </motion.div>

        {/* Mining Statistics */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <div className="card-header">
            <h3 className="card-title">Mining Statistics</h3>
            <Activity className="card-icon" />
          </div>

          <div className="mining-stats-grid" style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr 1fr', 
            gap: '1rem',
            marginBottom: '1.5rem'
          }}>
            <div className="stat-item" style={{
              padding: '1rem',
              background: 'var(--secondary-bg)',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ 
                fontSize: '1.5rem', 
                fontWeight: '700',
                color: 'var(--primary-color)',
                marginBottom: '0.5rem'
              }}>
                {miningStats.nonce?.toLocaleString() || 0}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Current Nonce
              </div>
            </div>

            <div className="stat-item" style={{
              padding: '1rem',
              background: 'var(--secondary-bg)',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ 
                fontSize: '1.5rem', 
                fontWeight: '700',
                color: 'var(--success-color)',
                marginBottom: '0.5rem'
              }}>
                {formatHashRate(miningStats.hashRate || 0)}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Hash Rate
              </div>
            </div>

            <div className="stat-item" style={{
              padding: '1rem',
              background: 'var(--secondary-bg)',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ 
                fontSize: '1.5rem', 
                fontWeight: '700',
                color: 'var(--warning-color)',
                marginBottom: '0.5rem'
              }}>
                5
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Difficulty
              </div>
            </div>

            <div className="stat-item" style={{
              padding: '1rem',
              background: 'var(--secondary-bg)',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ 
                fontSize: '1.5rem', 
                fontWeight: '700',
                color: 'var(--accent-color)',
                marginBottom: '0.5rem'
              }}>
                {mempool.length}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Pending Txs
              </div>
            </div>
          </div>

          {/* Current Hash */}
          {miningStats.hash && (
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                color: 'var(--text-primary)',
                fontWeight: '600'
              }}>
                Current Hash
              </label>
              <div style={{
                padding: '0.75rem',
                background: 'var(--secondary-bg)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                color: 'var(--text-secondary)',
                wordBreak: 'break-all'
              }}>
                {miningStats.hash}
              </div>
            </div>
          )}

          {/* Target */}
          {miningStats.target && (
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem',
                color: 'var(--text-primary)',
                fontWeight: '600'
              }}>
                Target (4 leading zeros)
              </label>
              <div style={{
                padding: '0.75rem',
                background: 'var(--secondary-bg)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                color: 'var(--success-color)',
                wordBreak: 'break-all'
              }}>
                0000{Array(60).fill('*').join('')}
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* Mining Rewards Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="card"
        style={{ marginTop: '2rem' }}
      >
        <div className="card-header">
          <h3 className="card-title">Mining Rewards & Economics</h3>
          <Award className="card-icon" />
        </div>

        <div className="grid grid-3">
          <div className="reward-info" style={{ textAlign: 'center' }}>
            <div style={{ 
              fontSize: '2rem', 
              fontWeight: '800',
              color: 'var(--success-color)',
              marginBottom: '0.5rem'
            }}>
              50 GSC
            </div>
            <div style={{ 
              color: 'var(--text-secondary)',
              marginBottom: '0.5rem'
            }}>
              Current Block Reward
            </div>
            <small style={{ color: 'var(--text-muted)' }}>
              Plus transaction fees
            </small>
          </div>

          <div className="reward-info" style={{ textAlign: 'center' }}>
            <div style={{ 
              fontSize: '2rem', 
              fontWeight: '800',
              color: 'var(--primary-color)',
              marginBottom: '0.5rem'
            }}>
              4 Years
            </div>
            <div style={{ 
              color: 'var(--text-secondary)',
              marginBottom: '0.5rem'
            }}>
              Halving Interval
            </div>
            <small style={{ color: 'var(--text-muted)' }}>
              1,051,200 blocks
            </small>
          </div>

          <div className="reward-info" style={{ textAlign: 'center' }}>
            <div style={{ 
              fontSize: '2rem', 
              fontWeight: '800',
              color: 'var(--warning-color)',
              marginBottom: '0.5rem'
            }}>
              2 min
            </div>
            <div style={{ 
              color: 'var(--text-secondary)',
              marginBottom: '0.5rem'
            }}>
              Target Block Time
            </div>
            <small style={{ color: 'var(--text-muted)' }}>
              Fixed difficulty
            </small>
          </div>
        </div>

        <div style={{ 
          marginTop: '2rem',
          padding: '1.5rem',
          background: 'var(--accent-bg)',
          borderRadius: '8px',
          border: '1px solid var(--primary-color)'
        }}>
          <h4 style={{ 
            margin: '0 0 1rem 0',
            color: 'var(--primary-color)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <TrendingUp size={20} />
            Smart Mining Advantage
          </h4>
          <p style={{ 
            margin: 0,
            color: 'var(--text-secondary)',
            lineHeight: 1.6
          }}>
            GSC Coin uses intelligent mining that only activates when there are actual transactions to process. 
            This means no wasted computational power on empty blocks, making mining more efficient and 
            environmentally friendly. The network automatically starts mining when transactions are submitted, 
            ensuring fast confirmation times while conserving energy.
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default Mining;
