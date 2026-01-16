import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Wallet as WalletIcon, 
  Send, 
  Download, 
  Copy, 
  QrCode,
  Plus,
  Eye,
  EyeOff,
  ArrowUpRight,
  ArrowDownLeft,
  RefreshCw,
  Import,
  Key,
  Shield,
  Trash2,
  AlertTriangle
} from 'lucide-react';
import QRCode from 'react-qr-code';
import { useBlockchain } from '../contexts/BlockchainContext';
import toast from 'react-hot-toast';

const EnhancedWallet = () => {
  const { 
    submitTransaction, 
    getBalance, 
    createWallet, 
    importWallet, 
    getWallets, 
    getWalletDetails,
    deleteWallet 
  } = useBlockchain();
  
  const [wallets, setWallets] = useState([]);
  const [activeWallet, setActiveWallet] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showMnemonic, setShowMnemonic] = useState(false);
  const [showPrivateKey, setShowPrivateKey] = useState(false);
  const [showQR, setShowQR] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const [createForm, setCreateForm] = useState({ name: '' });
  const [importForm, setImportForm] = useState({ mnemonic: '', name: '' });
  const [sendForm, setSendForm] = useState({
    recipient: '',
    amount: '',
    fee: '0.1'
  });

  // Load wallets on component mount
  useEffect(() => {
    loadWallets();
  }, []);

  const loadWallets = async () => {
    setIsLoading(true);
    try {
      const walletList = await getWallets();
      setWallets(walletList);
      
      // Check if genesis address exists and add it if not
      const genesisAddress = 'GSC1705641e65321ef23ac5fb3d470f39627';
      const hasGenesis = walletList.some(w => w.address === genesisAddress);
      
      if (!hasGenesis) {
        // Create genesis wallet entry for display
        const genesisWallet = {
          id: 'genesis',
          name: 'Genesis Wallet',
          address: genesisAddress,
          balance: 255,
          isGenesis: true,
          created: 1704067200000
        };
        setWallets(prev => [genesisWallet, ...prev]);
      }
      
      if (walletList.length > 0 && !activeWallet) {
        setActiveWallet(walletList[0]);
      }
    } catch (error) {
      toast.error('Failed to load wallets');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateWallet = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const newWallet = await createWallet(createForm.name || 'My Wallet');
      if (newWallet) {
        toast.success('Wallet created successfully!');
        setCreateForm({ name: '' });
        setShowCreateModal(false);
        await loadWallets();
        setActiveWallet(newWallet);
      } else {
        toast.error('Failed to create wallet');
      }
    } catch (error) {
      toast.error('Error creating wallet');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImportWallet = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const imported = await importWallet(importForm.mnemonic, importForm.name || 'Imported Wallet');
      if (imported) {
        toast.success('Wallet imported successfully!');
        setImportForm({ mnemonic: '', name: '' });
        setShowImportModal(false);
        await loadWallets();
        setActiveWallet(imported);
      } else {
        toast.error('Failed to import wallet');
      }
    } catch (error) {
      toast.error('Error importing wallet');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteWallet = async (walletId) => {
    if (window.confirm('Are you sure you want to delete this wallet? This action cannot be undone.')) {
      const result = await deleteWallet(walletId);
      if (result.success) {
        toast.success('Wallet deleted successfully');
        await loadWallets();
        if (activeWallet?.id === walletId) {
          setActiveWallet(null);
        }
      } else {
        toast.error('Failed to delete wallet');
      }
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const handleSendTransaction = async (e) => {
    e.preventDefault();
    if (!activeWallet) {
      toast.error('Please select a wallet');
      return;
    }

    setIsLoading(true);
    try {
      const result = await submitTransaction(
        activeWallet.address,
        sendForm.recipient,
        sendForm.amount,
        sendForm.fee
      );

      if (result.success) {
        toast.success('Transaction submitted successfully!');
        setSendForm({ recipient: '', amount: '', fee: '0.1' });
        await loadWallets();
      } else {
        toast.error(result.message);
      }
    } catch (error) {
      toast.error('Transaction failed');
    } finally {
      setIsLoading(false);
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
        <h1 className="page-title">Enhanced Wallet</h1>
        <p className="page-subtitle">
          Complete wallet management with mnemonic phrases and secure key storage
        </p>
      </div>

      <div className="grid grid-2">
        {/* Wallet List */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="card-header">
            <h3 className="card-title">My Wallets</h3>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => setShowImportModal(true)}
              >
                <Import size={16} />
                Import
              </button>
              <button 
                className="btn btn-primary btn-sm"
                onClick={() => setShowCreateModal(true)}
                disabled={isLoading}
              >
                <Plus size={16} />
                Create
              </button>
            </div>
          </div>

          {wallets.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <WalletIcon size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                No wallets found
              </p>
              <button 
                className="btn btn-primary"
                onClick={() => setShowCreateModal(true)}
              >
                Create Your First Wallet
              </button>
            </div>
          ) : (
            <div className="wallet-list">
              {wallets.map((wallet, index) => (
                <motion.div
                  key={wallet.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + index * 0.1 }}
                  className={`wallet-item ${activeWallet?.id === wallet.id ? 'active' : ''}`}
                  onClick={() => setActiveWallet(wallet)}
                  style={{
                    padding: '1rem',
                    background: activeWallet?.id === wallet.id 
                      ? 'var(--accent-bg)' 
                      : 'var(--secondary-bg)',
                    border: `1px solid ${activeWallet?.id === wallet.id 
                      ? 'var(--primary-color)' 
                      : 'var(--border-color)'}`,
                    borderRadius: '8px',
                    marginBottom: '0.5rem',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    position: 'relative'
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
                        gap: '0.5rem',
                        fontWeight: '600', 
                        marginBottom: '0.25rem',
                        color: 'var(--text-primary)'
                      }}>
                        {wallet.name}
                        {wallet.isGenesis && (
                          <span style={{
                            padding: '0.2rem 0.5rem',
                            background: 'var(--gradient-success)',
                            borderRadius: '12px',
                            fontSize: '0.7rem',
                            fontWeight: '600',
                            color: 'white'
                          }}>
                            GENESIS
                          </span>
                        )}
                      </div>
                      <div style={{ 
                        fontSize: '0.8rem', 
                        color: 'var(--text-muted)',
                        fontFamily: 'monospace'
                      }}>
                        {wallet.address.substring(0, 20)}...
                      </div>
                      <div style={{ 
                        fontSize: '0.9rem', 
                        color: 'var(--success-color)',
                        fontWeight: '600',
                        marginTop: '0.25rem'
                      }}>
                        {wallet.balance} GSC
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <WalletIcon size={20} style={{ color: 'var(--primary-color)' }} />
                      {!wallet.isGenesis && (
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteWallet(wallet.id);
                          }}
                          style={{ padding: '0.25rem' }}
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>

        {/* Wallet Details */}
        {activeWallet && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="card"
          >
            <div className="card-header">
              <h3 className="card-title">{activeWallet.name}</h3>
              <button 
                className="btn btn-secondary btn-sm"
                onClick={loadWallets}
              >
                <RefreshCw size={16} />
                Refresh
              </button>
            </div>

            {/* Balance Display */}
            <div style={{ 
              textAlign: 'center', 
              padding: '2rem 0',
              borderBottom: '1px solid var(--border-color)',
              marginBottom: '1.5rem'
            }}>
              <div style={{ 
                fontSize: '2.5rem', 
                fontWeight: '800',
                color: activeWallet.isGenesis ? 'var(--success-color)' : 'var(--primary-color)',
                marginBottom: '0.5rem'
              }}>
                {activeWallet.balance} GSC
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>
                {activeWallet.isGenesis ? 'Genesis Balance' : 'Available Balance'}
              </div>
            </div>

            {/* Wallet Address */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label className="form-label">Wallet Address</label>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                padding: '0.75rem',
                background: 'var(--secondary-bg)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px'
              }}>
                <input
                  type="text"
                  value={activeWallet.address}
                  readOnly
                  style={{
                    flex: 1,
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-primary)',
                    fontFamily: 'monospace',
                    fontSize: '0.9rem'
                  }}
                />
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => copyToClipboard(activeWallet.address)}
                >
                  <Copy size={14} />
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setShowQR(!showQR)}
                >
                  <QrCode size={14} />
                </button>
              </div>
            </div>

            {/* Mnemonic Phrase (if available) */}
            {activeWallet.mnemonic && !activeWallet.isGenesis && (
              <div style={{ marginBottom: '1.5rem' }}>
                <label className="form-label">
                  <Shield size={16} style={{ marginRight: '0.5rem' }} />
                  Mnemonic Phrase
                </label>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.5rem',
                  padding: '0.75rem',
                  background: 'var(--secondary-bg)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px'
                }}>
                  <input
                    type={showMnemonic ? 'text' : 'password'}
                    value={activeWallet.mnemonic}
                    readOnly
                    style={{
                      flex: 1,
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-primary)',
                      fontSize: '0.9rem'
                    }}
                  />
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setShowMnemonic(!showMnemonic)}
                  >
                    {showMnemonic ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => copyToClipboard(activeWallet.mnemonic)}
                  >
                    <Copy size={14} />
                  </button>
                </div>
                <small style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  Keep your mnemonic phrase safe and never share it with anyone
                </small>
              </div>
            )}

            {/* QR Code */}
            <AnimatePresence>
              {showQR && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  style={{ 
                    textAlign: 'center', 
                    padding: '1rem',
                    background: 'white',
                    borderRadius: '8px',
                    marginBottom: '1.5rem'
                  }}
                >
                  <QRCode value={activeWallet.address} size={150} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Action Buttons */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr 1fr', 
              gap: '1rem' 
            }}>
              <button className="btn btn-success">
                <ArrowDownLeft size={16} />
                Receive
              </button>
              <button 
                className="btn btn-primary"
                disabled={activeWallet.isGenesis}
              >
                <ArrowUpRight size={16} />
                Send
              </button>
            </div>

            {activeWallet.isGenesis && (
              <div style={{
                marginTop: '1rem',
                padding: '1rem',
                background: 'rgba(255, 170, 0, 0.1)',
                border: '1px solid var(--warning-color)',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <AlertTriangle size={16} style={{ color: 'var(--warning-color)' }} />
                <small style={{ color: 'var(--warning-color)' }}>
                  Genesis wallet is read-only. Import with mnemonic to send transactions.
                </small>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Create Wallet Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="modal-overlay"
            onClick={() => setShowCreateModal(false)}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="modal-content"
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'var(--card-bg)',
                borderRadius: '12px',
                padding: '2rem',
                width: '90%',
                maxWidth: '500px',
                border: '1px solid var(--border-color)'
              }}
            >
              <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)' }}>
                Create New Wallet
              </h3>
              
              <form onSubmit={handleCreateWallet}>
                <div className="form-group">
                  <label className="form-label">Wallet Name</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Enter wallet name..."
                    value={createForm.name}
                    onChange={(e) => setCreateForm({...createForm, name: e.target.value})}
                  />
                </div>
                
                <div style={{ 
                  display: 'flex', 
                  gap: '1rem', 
                  justifyContent: 'flex-end',
                  marginTop: '2rem'
                }}>
                  <button 
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowCreateModal(false)}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    className="btn btn-primary"
                    disabled={isLoading}
                  >
                    {isLoading ? 'Creating...' : 'Create Wallet'}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Import Wallet Modal */}
      <AnimatePresence>
        {showImportModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="modal-overlay"
            onClick={() => setShowImportModal(false)}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="modal-content"
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'var(--card-bg)',
                borderRadius: '12px',
                padding: '2rem',
                width: '90%',
                maxWidth: '500px',
                border: '1px solid var(--border-color)'
              }}
            >
              <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)' }}>
                Import Wallet
              </h3>
              
              <form onSubmit={handleImportWallet}>
                <div className="form-group">
                  <label className="form-label">Mnemonic Phrase</label>
                  <textarea
                    className="form-input"
                    placeholder="Enter your 12-word mnemonic phrase..."
                    rows="3"
                    value={importForm.mnemonic}
                    onChange={(e) => setImportForm({...importForm, mnemonic: e.target.value})}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label className="form-label">Wallet Name</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Enter wallet name..."
                    value={importForm.name}
                    onChange={(e) => setImportForm({...importForm, name: e.target.value})}
                  />
                </div>
                
                <div style={{ 
                  display: 'flex', 
                  gap: '1rem', 
                  justifyContent: 'flex-end',
                  marginTop: '2rem'
                }}>
                  <button 
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowImportModal(false)}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    className="btn btn-primary"
                    disabled={isLoading || !importForm.mnemonic}
                  >
                    {isLoading ? 'Importing...' : 'Import Wallet'}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default EnhancedWallet;
