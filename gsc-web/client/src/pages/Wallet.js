import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
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
  RefreshCw
} from 'lucide-react';
import QRCode from 'react-qr-code';
import { useBlockchain } from '../contexts/BlockchainContext';
import toast from 'react-hot-toast';

const Wallet = () => {
  const { submitTransaction, getBalance, generateWallet } = useBlockchain();
  const [wallets, setWallets] = useState([]);
  const [activeWallet, setActiveWallet] = useState(null);
  const [balance, setBalance] = useState(0);
  const [showPrivateKey, setShowPrivateKey] = useState(false);
  const [showQR, setShowQR] = useState(false);
  const [sendForm, setSendForm] = useState({
    recipient: '',
    amount: '',
    fee: '0.1'
  });
  const [isLoading, setIsLoading] = useState(false);

  // Load wallets from localStorage
  useEffect(() => {
    const savedWallets = localStorage.getItem('gsc_wallets');
    if (savedWallets) {
      const parsedWallets = JSON.parse(savedWallets);
      setWallets(parsedWallets);
      if (parsedWallets.length > 0 && !activeWallet) {
        setActiveWallet(parsedWallets[0]);
      }
    }
  }, []);

  // Update balance when active wallet changes
  useEffect(() => {
    if (activeWallet) {
      updateBalance();
    }
  }, [activeWallet]);

  const updateBalance = async () => {
    if (activeWallet) {
      const newBalance = await getBalance(activeWallet.address);
      setBalance(newBalance);
    }
  };

  const createNewWallet = async () => {
    setIsLoading(true);
    try {
      const newWallet = await generateWallet();
      if (newWallet) {
        const walletData = {
          ...newWallet,
          name: `Wallet ${wallets.length + 1}`,
          created: Date.now()
        };
        
        const updatedWallets = [...wallets, walletData];
        setWallets(updatedWallets);
        setActiveWallet(walletData);
        localStorage.setItem('gsc_wallets', JSON.stringify(updatedWallets));
        
        toast.success('New wallet created successfully!');
      }
    } catch (error) {
      toast.error('Failed to create wallet');
    } finally {
      setIsLoading(false);
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

    if (!sendForm.recipient || !sendForm.amount) {
      toast.error('Please fill in all required fields');
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
        setTimeout(updateBalance, 2000); // Update balance after 2 seconds
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
        <h1 className="page-title">Wallet</h1>
        <p className="page-subtitle">
          Manage your GSC Coin wallets and transactions
        </p>
      </div>

      <div className="grid grid-2">
        {/* Wallet Overview */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="card-header">
            <h3 className="card-title">My Wallets</h3>
            <button 
              className="btn btn-primary btn-sm"
              onClick={createNewWallet}
              disabled={isLoading}
            >
              <Plus size={16} />
              New Wallet
            </button>
          </div>

          {wallets.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <WalletIcon size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                No wallets found
              </p>
              <button 
                className="btn btn-primary"
                onClick={createNewWallet}
                disabled={isLoading}
              >
                Create Your First Wallet
              </button>
            </div>
          ) : (
            <div className="wallet-list">
              {wallets.map((wallet, index) => (
                <motion.div
                  key={wallet.address}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + index * 0.1 }}
                  className={`wallet-item ${activeWallet?.address === wallet.address ? 'active' : ''}`}
                  onClick={() => setActiveWallet(wallet)}
                  style={{
                    padding: '1rem',
                    background: activeWallet?.address === wallet.address 
                      ? 'var(--accent-bg)' 
                      : 'var(--secondary-bg)',
                    border: `1px solid ${activeWallet?.address === wallet.address 
                      ? 'var(--primary-color)' 
                      : 'var(--border-color)'}`,
                    borderRadius: '8px',
                    marginBottom: '0.5rem',
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
                        fontWeight: '600', 
                        marginBottom: '0.25rem',
                        color: 'var(--text-primary)'
                      }}>
                        {wallet.name}
                      </div>
                      <div style={{ 
                        fontSize: '0.8rem', 
                        color: 'var(--text-muted)',
                        fontFamily: 'monospace'
                      }}>
                        {wallet.address.substring(0, 20)}...
                      </div>
                    </div>
                    <WalletIcon size={20} style={{ color: 'var(--primary-color)' }} />
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
                onClick={updateBalance}
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
                color: 'var(--primary-color)',
                marginBottom: '0.5rem'
              }}>
                {balance.toLocaleString()} GSC
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>
                Available Balance
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

            {/* QR Code */}
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
              <button className="btn btn-primary">
                <ArrowUpRight size={16} />
                Send
              </button>
            </div>
          </motion.div>
        )}
      </div>

      {/* Send Transaction Form */}
      {activeWallet && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="card"
          style={{ marginTop: '2rem' }}
        >
          <div className="card-header">
            <h3 className="card-title">Send GSC Coins</h3>
            <Send className="card-icon" />
          </div>

          <form onSubmit={handleSendTransaction}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">Recipient Address</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Enter GSC address..."
                  value={sendForm.recipient}
                  onChange={(e) => setSendForm({...sendForm, recipient: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Amount (GSC)</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="0.00"
                  step="0.01"
                  min="0.01"
                  value={sendForm.amount}
                  onChange={(e) => setSendForm({...sendForm, amount: e.target.value})}
                  required
                />
              </div>
            </div>
            
            <div className="form-group">
              <label className="form-label">Transaction Fee (GSC)</label>
              <input
                type="number"
                className="form-input"
                step="0.01"
                min="0.1"
                value={sendForm.fee}
                onChange={(e) => setSendForm({...sendForm, fee: e.target.value})}
              />
              <small style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                Minimum fee: 0.1 GSC
              </small>
            </div>

            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              padding: '1rem',
              background: 'var(--secondary-bg)',
              borderRadius: '8px',
              marginBottom: '1.5rem'
            }}>
              <span>Total Cost:</span>
              <span style={{ 
                fontWeight: '600', 
                color: 'var(--primary-color)' 
              }}>
                {(parseFloat(sendForm.amount || 0) + parseFloat(sendForm.fee || 0)).toFixed(2)} GSC
              </span>
            </div>

            <button 
              type="submit" 
              className="btn btn-primary btn-lg"
              disabled={isLoading || !sendForm.recipient || !sendForm.amount}
              style={{ width: '100%' }}
            >
              {isLoading ? 'Sending...' : 'Send Transaction'}
            </button>
          </form>
        </motion.div>
      )}
    </motion.div>
  );
};

export default Wallet;
