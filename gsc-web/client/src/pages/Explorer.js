import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  Blocks, 
  Hash, 
  Clock, 
  User,
  ArrowRight,
  Eye,
  Copy,
  ExternalLink
} from 'lucide-react';
import { useBlockchain } from '../contexts/BlockchainContext';
import toast from 'react-hot-toast';

const Explorer = () => {
  const { recentBlocks, getBlock, getTransaction } = useBlockchain();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setSearchResult(null);

    try {
      // Try to search as block index first
      if (/^\d+$/.test(searchQuery)) {
        const block = await getBlock(parseInt(searchQuery));
        if (block) {
          setSearchResult({ type: 'block', data: block });
          return;
        }
      }

      // Try to search as transaction ID
      const transaction = await getTransaction(searchQuery);
      if (transaction) {
        setSearchResult({ type: 'transaction', data: transaction });
        return;
      }

      toast.error('No results found');
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const truncateHash = (hash, length = 16) => {
    return `${hash.substring(0, length)}...`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="page-container"
    >
      <div className="page-header">
        <h1 className="page-title">Blockchain Explorer</h1>
        <p className="page-subtitle">
          Explore blocks, transactions, and addresses on the GSC network
        </p>
      </div>

      {/* Search Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card"
        style={{ marginBottom: '2rem' }}
      >
        <form onSubmit={handleSearch}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <Search 
                size={20} 
                style={{ 
                  position: 'absolute', 
                  left: '1rem', 
                  top: '50%', 
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)'
                }} 
              />
              <input
                type="text"
                className="form-input"
                placeholder="Search by block number, transaction ID, or address..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ paddingLeft: '3rem' }}
              />
            </div>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>
      </motion.div>

      {/* Search Results */}
      {searchResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
          style={{ marginBottom: '2rem' }}
        >
          <div className="card-header">
            <h3 className="card-title">
              {searchResult.type === 'block' ? 'Block Details' : 'Transaction Details'}
            </h3>
            {searchResult.type === 'block' ? <Blocks className="card-icon" /> : <Hash className="card-icon" />}
          </div>

          {searchResult.type === 'block' ? (
            <div className="block-details">
              <div className="grid grid-2">
                <div>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Block Index</label>
                  <p style={{ fontFamily: 'monospace', color: 'var(--primary-color)' }}>
                    #{searchResult.data.index}
                  </p>
                </div>
                <div>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Timestamp</label>
                  <p style={{ color: 'var(--text-secondary)' }}>
                    {formatTimestamp(searchResult.data.timestamp)}
                  </p>
                </div>
                <div>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Transactions</label>
                  <p style={{ color: 'var(--success-color)' }}>
                    {searchResult.data.transactions.length}
                  </p>
                </div>
                <div>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Difficulty</label>
                  <p style={{ color: 'var(--warning-color)' }}>
                    {searchResult.data.difficulty}
                  </p>
                </div>
              </div>

              <div style={{ marginTop: '1.5rem' }}>
                <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Block Hash</label>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.5rem',
                  marginTop: '0.5rem'
                }}>
                  <code style={{ 
                    flex: 1,
                    padding: '0.5rem',
                    background: 'var(--secondary-bg)',
                    borderRadius: '4px',
                    fontSize: '0.9rem',
                    wordBreak: 'break-all'
                  }}>
                    {searchResult.data.hash}
                  </code>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => copyToClipboard(searchResult.data.hash)}
                  >
                    <Copy size={14} />
                  </button>
                </div>
              </div>

              {/* Transactions in Block */}
              <div style={{ marginTop: '2rem' }}>
                <h4 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>
                  Transactions ({searchResult.data.transactions.length})
                </h4>
                <div className="transactions-list">
                  {searchResult.data.transactions.map((tx, index) => (
                    <div 
                      key={tx.txId || index}
                      style={{
                        padding: '1rem',
                        background: 'var(--secondary-bg)',
                        borderRadius: '8px',
                        marginBottom: '0.5rem',
                        border: '1px solid var(--border-color)'
                      }}
                    >
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        marginBottom: '0.5rem'
                      }}>
                        <span style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>
                          {truncateHash(tx.txId || 'N/A')}
                        </span>
                        <span style={{ 
                          color: 'var(--success-color)', 
                          fontWeight: '600' 
                        }}>
                          {tx.amount} GSC
                        </span>
                      </div>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '1rem',
                        fontSize: '0.8rem',
                        color: 'var(--text-secondary)'
                      }}>
                        <span>{truncateHash(tx.sender, 12)}</span>
                        <ArrowRight size={12} />
                        <span>{truncateHash(tx.receiver, 12)}</span>
                        <span style={{ marginLeft: 'auto' }}>Fee: {tx.fee} GSC</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="transaction-details">
              <div className="grid grid-2">
                <div>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Transaction ID</label>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '0.5rem',
                    marginTop: '0.5rem'
                  }}>
                    <code style={{ 
                      flex: 1,
                      padding: '0.5rem',
                      background: 'var(--secondary-bg)',
                      borderRadius: '4px',
                      fontSize: '0.8rem',
                      wordBreak: 'break-all'
                    }}>
                      {searchResult.data.transaction.txId}
                    </code>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => copyToClipboard(searchResult.data.transaction.txId)}
                    >
                      <Copy size={14} />
                    </button>
                  </div>
                </div>
                <div>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Status</label>
                  <p style={{ 
                    color: searchResult.data.confirmed ? 'var(--success-color)' : 'var(--warning-color)',
                    fontWeight: '600'
                  }}>
                    {searchResult.data.confirmed ? 'Confirmed' : 'Pending'}
                  </p>
                </div>
                <div>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Amount</label>
                  <p style={{ color: 'var(--primary-color)', fontWeight: '600' }}>
                    {searchResult.data.transaction.amount} GSC
                  </p>
                </div>
                <div>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Fee</label>
                  <p style={{ color: 'var(--text-secondary)' }}>
                    {searchResult.data.transaction.fee} GSC
                  </p>
                </div>
              </div>

              <div className="grid grid-2" style={{ marginTop: '1.5rem' }}>
                <div>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>From</label>
                  <code style={{ 
                    display: 'block',
                    padding: '0.5rem',
                    background: 'var(--secondary-bg)',
                    borderRadius: '4px',
                    fontSize: '0.9rem',
                    marginTop: '0.5rem'
                  }}>
                    {searchResult.data.transaction.sender}
                  </code>
                </div>
                <div>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>To</label>
                  <code style={{ 
                    display: 'block',
                    padding: '0.5rem',
                    background: 'var(--secondary-bg)',
                    borderRadius: '4px',
                    fontSize: '0.9rem',
                    marginTop: '0.5rem'
                  }}>
                    {searchResult.data.transaction.receiver}
                  </code>
                </div>
              </div>

              {searchResult.data.confirmed && (
                <div style={{ marginTop: '1.5rem' }}>
                  <label style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Block</label>
                  <p style={{ color: 'var(--primary-color)' }}>
                    #{searchResult.data.blockIndex}
                  </p>
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}

      {/* Recent Blocks */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card"
      >
        <div className="card-header">
          <h3 className="card-title">Recent Blocks</h3>
          <Blocks className="card-icon" />
        </div>

        <div className="blocks-list">
          {recentBlocks.map((block, index) => (
            <motion.div
              key={block.index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + index * 0.1 }}
              className="block-item"
              onClick={() => setSelectedBlock(selectedBlock?.index === block.index ? null : block)}
              style={{
                padding: '1.5rem',
                background: 'var(--secondary-bg)',
                borderRadius: '8px',
                marginBottom: '1rem',
                border: '1px solid var(--border-color)',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
            >
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between' 
              }}>
                <div>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '1rem',
                    marginBottom: '0.5rem'
                  }}>
                    <h4 style={{ 
                      margin: 0,
                      color: 'var(--primary-color)',
                      fontSize: '1.1rem'
                    }}>
                      Block #{block.index}
                    </h4>
                    <span style={{ 
                      padding: '0.25rem 0.75rem',
                      background: 'var(--accent-bg)',
                      borderRadius: '12px',
                      fontSize: '0.8rem',
                      color: 'var(--success-color)'
                    }}>
                      {block.transactions.length} txs
                    </span>
                  </div>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '2rem',
                    fontSize: '0.9rem',
                    color: 'var(--text-secondary)'
                  }}>
                    <span>
                      <Clock size={14} style={{ marginRight: '0.5rem' }} />
                      {formatTimestamp(block.timestamp)}
                    </span>
                    <span>
                      <Hash size={14} style={{ marginRight: '0.5rem' }} />
                      {truncateHash(block.hash)}
                    </span>
                  </div>
                </div>
                <Eye size={20} style={{ color: 'var(--text-muted)' }} />
              </div>

              {/* Expanded Block Details */}
              {selectedBlock?.index === block.index && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  style={{ 
                    marginTop: '1rem',
                    paddingTop: '1rem',
                    borderTop: '1px solid var(--border-color)'
                  }}
                >
                  <div className="grid grid-2" style={{ marginBottom: '1rem' }}>
                    <div>
                      <strong>Difficulty:</strong> {block.difficulty}
                    </div>
                    <div>
                      <strong>Nonce:</strong> {block.nonce}
                    </div>
                    <div>
                      <strong>Miner:</strong> {truncateHash(block.miner || 'Unknown')}
                    </div>
                    <div>
                      <strong>Reward:</strong> {block.reward || 0} GSC
                    </div>
                  </div>

                  <div>
                    <strong>Full Hash:</strong>
                    <code style={{ 
                      display: 'block',
                      padding: '0.5rem',
                      background: 'var(--primary-bg)',
                      borderRadius: '4px',
                      fontSize: '0.8rem',
                      marginTop: '0.5rem',
                      wordBreak: 'break-all'
                    }}>
                      {block.hash}
                    </code>
                  </div>

                  <div style={{ marginTop: '1rem' }}>
                    <strong>Transactions:</strong>
                    <div style={{ marginTop: '0.5rem' }}>
                      {block.transactions.slice(0, 3).map((tx, txIndex) => (
                        <div 
                          key={txIndex}
                          style={{
                            padding: '0.5rem',
                            background: 'var(--primary-bg)',
                            borderRadius: '4px',
                            marginBottom: '0.25rem',
                            fontSize: '0.8rem'
                          }}
                        >
                          {truncateHash(tx.sender, 8)} → {truncateHash(tx.receiver, 8)}: {tx.amount} GSC
                        </div>
                      ))}
                      {block.transactions.length > 3 && (
                        <div style={{ 
                          fontSize: '0.8rem', 
                          color: 'var(--text-muted)',
                          textAlign: 'center',
                          padding: '0.5rem'
                        }}>
                          +{block.transactions.length - 3} more transactions
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default Explorer;
