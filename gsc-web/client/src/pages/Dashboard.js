import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  Blocks, 
  Users, 
  Zap, 
  Clock, 
  DollarSign,
  Activity,
  Hammer
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useBlockchain } from '../contexts/BlockchainContext';
import { useWebSocket } from '../contexts/WebSocketContext';

const Dashboard = () => {
  const { blockchainStats, recentBlocks } = useBlockchain();
  const { isConnected } = useWebSocket();
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    // Generate sample chart data based on recent blocks
    if (recentBlocks.length > 0) {
      const data = recentBlocks.slice(-10).map((block, index) => ({
        block: block.index,
        transactions: block.transactions.length,
        difficulty: block.difficulty,
        time: new Date(block.timestamp).toLocaleTimeString()
      }));
      setChartData(data.reverse());
    }
  }, [recentBlocks]);

  const stats = [
    {
      title: 'Total Blocks',
      value: blockchainStats?.totalBlocks || 0,
      icon: Blocks,
      color: 'var(--primary-color)',
      change: '+2.5%'
    },
    {
      title: 'Mempool Size',
      value: blockchainStats?.mempoolSize || 0,
      icon: Clock,
      color: 'var(--warning-color)',
      change: `${blockchainStats?.mempoolSize || 0} pending`
    },
    {
      title: 'Current Supply',
      value: `${((blockchainStats?.currentSupply || 0) / 1000000).toFixed(2)}M`,
      icon: DollarSign,
      color: 'var(--success-color)',
      change: 'GSC'
    },
    {
      title: 'Mining Difficulty',
      value: blockchainStats?.difficulty || 5,
      icon: Hammer,
      color: 'var(--accent-color)',
      change: 'Fixed'
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="page-container"
    >
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Real-time overview of the GSC Coin blockchain network
        </p>
      </div>

      {/* Network Status */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="network-status-banner"
        style={{
          background: isConnected ? 'var(--gradient-success)' : 'var(--gradient-secondary)',
          padding: '1rem 2rem',
          borderRadius: '12px',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}
      >
        <Activity size={24} />
        <div>
          <h3 style={{ margin: 0, fontSize: '1.1rem' }}>
            {isConnected ? 'Network Connected' : 'Network Disconnected'}
          </h3>
          <p style={{ margin: 0, opacity: 0.9, fontSize: '0.9rem' }}>
            {isConnected 
              ? 'Real-time blockchain synchronization active'
              : 'Attempting to reconnect to blockchain network'
            }
          </p>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="stats-grid">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.1 }}
              className="stat-card"
              whileHover={{ scale: 1.02 }}
            >
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                marginBottom: '1rem'
              }}>
                <Icon size={24} style={{ color: stat.color }} />
                <span style={{ 
                  fontSize: '0.8rem', 
                  color: 'var(--success-color)',
                  fontWeight: '600'
                }}>
                  {stat.change}
                </span>
              </div>
              <div className="stat-value" style={{ color: stat.color }}>
                {stat.value.toLocaleString()}
              </div>
              <div className="stat-label">{stat.title}</div>
            </motion.div>
          );
        })}
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-2">
        {/* Blockchain Activity Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <div className="card-header">
            <h3 className="card-title">Blockchain Activity</h3>
            <TrendingUp className="card-icon" />
          </div>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis 
                  dataKey="block" 
                  stroke="var(--text-secondary)"
                  fontSize={12}
                />
                <YAxis 
                  stroke="var(--text-secondary)"
                  fontSize={12}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'var(--card-bg)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="transactions" 
                  stroke="var(--primary-color)" 
                  strokeWidth={3}
                  dot={{ fill: 'var(--primary-color)', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: 'var(--primary-color)', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Recent Blocks */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="card"
        >
          <div className="card-header">
            <h3 className="card-title">Recent Blocks</h3>
            <Blocks className="card-icon" />
          </div>
          <div className="recent-blocks-list">
            {recentBlocks.slice(0, 5).map((block, index) => (
              <motion.div
                key={block.index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                className="block-item"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '1rem',
                  background: 'var(--secondary-bg)',
                  borderRadius: '8px',
                  marginBottom: '0.5rem',
                  border: '1px solid var(--border-color)'
                }}
              >
                <div>
                  <div style={{ 
                    fontWeight: '600', 
                    color: 'var(--primary-color)',
                    marginBottom: '0.25rem'
                  }}>
                    Block #{block.index}
                  </div>
                  <div style={{ 
                    fontSize: '0.9rem', 
                    color: 'var(--text-secondary)' 
                  }}>
                    {block.transactions.length} transactions
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ 
                    fontSize: '0.8rem', 
                    color: 'var(--text-muted)' 
                  }}>
                    {new Date(block.timestamp).toLocaleTimeString()}
                  </div>
                  <div style={{ 
                    fontSize: '0.8rem', 
                    color: 'var(--success-color)',
                    fontWeight: '600'
                  }}>
                    {block.hash.substring(0, 8)}...
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Network Information */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="card"
        style={{ marginTop: '2rem' }}
      >
        <div className="card-header">
          <h3 className="card-title">Network Information</h3>
          <Users className="card-icon" />
        </div>
        <div className="grid grid-3">
          <div className="network-info-item">
            <div style={{ 
              fontSize: '1.5rem', 
              fontWeight: '700', 
              color: 'var(--primary-color)',
              marginBottom: '0.5rem'
            }}>
              2 minutes
            </div>
            <div style={{ color: 'var(--text-secondary)' }}>Block Time</div>
          </div>
          <div className="network-info-item">
            <div style={{ 
              fontSize: '1.5rem', 
              fontWeight: '700', 
              color: 'var(--success-color)',
              marginBottom: '0.5rem'
            }}>
              50 GSC
            </div>
            <div style={{ color: 'var(--text-secondary)' }}>Block Reward</div>
          </div>
          <div className="network-info-item">
            <div style={{ 
              fontSize: '1.5rem', 
              fontWeight: '700', 
              color: 'var(--warning-color)',
              marginBottom: '0.5rem'
            }}>
              21.75T
            </div>
            <div style={{ color: 'var(--text-secondary)' }}>Max Supply</div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default Dashboard;
