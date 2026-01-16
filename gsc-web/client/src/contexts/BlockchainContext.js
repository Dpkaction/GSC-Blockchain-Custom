import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const BlockchainContext = createContext();

export const useBlockchain = () => {
  const context = useContext(BlockchainContext);
  if (!context) {
    throw new Error('useBlockchain must be used within a BlockchainProvider');
  }
  return context;
};

export const BlockchainProvider = ({ children }) => {
  const [blockchainStats, setBlockchainStats] = useState({});
  const [recentBlocks, setRecentBlocks] = useState([]);
  const [mempool, setMempool] = useState([]);
  const [miningStatus, setMiningStatus] = useState({
    isMining: false,
    minerAddress: null,
    stats: {}
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE = process.env.NODE_ENV === 'production' 
    ? 'https://gsc-coin.vercel.app/api'
    : '/api';

  // Fetch blockchain information
  const fetchBlockchainInfo = async () => {
    try {
      const response = await axios.get(`${API_BASE}/blockchain/info`);
      if (response.data.success) {
        setBlockchainStats(response.data.data);
      }
    } catch (err) {
      console.error('Error fetching blockchain info:', err);
      setError(err.message);
    }
  };

  // Fetch recent blocks
  const fetchRecentBlocks = async () => {
    try {
      const response = await axios.get(`${API_BASE}/blockchain/blocks?limit=10`);
      if (response.data.success) {
        setRecentBlocks(response.data.data.blocks);
      }
    } catch (err) {
      console.error('Error fetching blocks:', err);
    }
  };

  // Fetch mempool
  const fetchMempool = async () => {
    try {
      const response = await axios.get(`${API_BASE}/blockchain/mempool`);
      if (response.data.success) {
        setMempool(response.data.data.transactions);
      }
    } catch (err) {
      console.error('Error fetching mempool:', err);
    }
  };

  // Fetch mining status
  const fetchMiningStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/mining/status`);
      if (response.data.success) {
        setMiningStatus(response.data.data);
      }
    } catch (err) {
      console.error('Error fetching mining status:', err);
    }
  };

  // Submit transaction
  const submitTransaction = async (sender, receiver, amount, fee = 0.1) => {
    try {
      const response = await axios.post(`${API_BASE}/blockchain/transactions`, {
        sender,
        receiver,
        amount: parseFloat(amount),
        fee: parseFloat(fee)
      });
      
      if (response.data.success) {
        // Refresh mempool after successful transaction
        await fetchMempool();
        return { success: true, message: 'Transaction submitted successfully' };
      } else {
        return { success: false, message: response.data.error };
      }
    } catch (err) {
      return { 
        success: false, 
        message: err.response?.data?.error || err.message 
      };
    }
  };

  // Start mining
  const startMining = async (minerAddress) => {
    try {
      const response = await axios.post(`${API_BASE}/mining/start`, {
        minerAddress
      });
      
      if (response.data.success) {
        await fetchMiningStatus();
        return { success: true, message: response.data.message };
      } else {
        return { success: false, message: response.data.error };
      }
    } catch (err) {
      return { 
        success: false, 
        message: err.response?.data?.error || err.message 
      };
    }
  };

  // Stop mining
  const stopMining = async () => {
    try {
      const response = await axios.post(`${API_BASE}/mining/stop`);
      
      if (response.data.success) {
        await fetchMiningStatus();
        return { success: true, message: 'Mining stopped' };
      } else {
        return { success: false, message: response.data.error };
      }
    } catch (err) {
      return { 
        success: false, 
        message: err.response?.data?.error || err.message 
      };
    }
  };

  // Get balance for address
  const getBalance = async (address) => {
    try {
      const response = await axios.get(`${API_BASE}/blockchain/balance/${address}`);
      if (response.data.success) {
        return response.data.data.balance;
      }
      return 0;
    } catch (err) {
      console.error('Error fetching balance:', err);
      return 0;
    }
  };

  // Create new wallet with mnemonic
  const createWallet = async (name) => {
    try {
      const response = await axios.post(`${API_BASE}/wallet/create`, { name });
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (err) {
      console.error('Error creating wallet:', err);
      return null;
    }
  };

  // Import wallet from mnemonic
  const importWallet = async (mnemonic, name) => {
    try {
      const response = await axios.post(`${API_BASE}/wallet/import`, { mnemonic, name });
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (err) {
      console.error('Error importing wallet:', err);
      return null;
    }
  };

  // Get all wallets
  const getWallets = async () => {
    try {
      const response = await axios.get(`${API_BASE}/wallet/list`);
      if (response.data.success) {
        return response.data.data;
      }
      return [];
    } catch (err) {
      console.error('Error fetching wallets:', err);
      return [];
    }
  };

  // Get wallet details
  const getWalletDetails = async (id) => {
    try {
      const response = await axios.get(`${API_BASE}/wallet/${id}`);
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (err) {
      console.error('Error fetching wallet details:', err);
      return null;
    }
  };

  // Delete wallet
  const deleteWallet = async (id) => {
    try {
      const response = await axios.delete(`${API_BASE}/wallet/${id}`);
      return response.data;
    } catch (err) {
      console.error('Error deleting wallet:', err);
      return { success: false, message: err.message };
    }
  };

  // Generate wallet address (legacy)
  const generateWallet = async () => {
    try {
      const response = await axios.post(`${API_BASE}/wallet/generate`);
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (err) {
      console.error('Error generating wallet:', err);
      return null;
    }
  };

  // Get block by index
  const getBlock = async (index) => {
    try {
      const response = await axios.get(`${API_BASE}/blockchain/blocks/${index}`);
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (err) {
      console.error('Error fetching block:', err);
      return null;
    }
  };

  // Get transaction by ID
  const getTransaction = async (txId) => {
    try {
      const response = await axios.get(`${API_BASE}/blockchain/transactions/${txId}`);
      if (response.data.success) {
        return response.data.data;
      }
      return null;
    } catch (err) {
      console.error('Error fetching transaction:', err);
      return null;
    }
  };

  // Validate blockchain
  const validateBlockchain = async () => {
    try {
      const response = await axios.get(`${API_BASE}/blockchain/validate`);
      if (response.data.success) {
        return response.data.data;
      }
      return { isValid: false, message: 'Validation failed' };
    } catch (err) {
      console.error('Error validating blockchain:', err);
      return { isValid: false, message: err.message };
    }
  };

  // Initial data fetch
  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchBlockchainInfo(),
          fetchRecentBlocks(),
          fetchMempool(),
          fetchMiningStatus()
        ]);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    initializeData();
  }, []);

  // Periodic updates
  useEffect(() => {
    const interval = setInterval(() => {
      fetchBlockchainInfo();
      fetchRecentBlocks();
      fetchMempool();
      fetchMiningStatus();
    }, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const value = {
    // State
    blockchainStats,
    recentBlocks,
    mempool,
    miningStatus,
    loading,
    error,
    
    // Actions
    submitTransaction,
    startMining,
    stopMining,
    getBalance,
    createWallet,
    importWallet,
    getWallets,
    getWalletDetails,
    deleteWallet,
    generateWallet,
    getBlock,
    getTransaction,
    validateBlockchain,
    
    // Refresh functions
    refreshData: () => {
      fetchBlockchainInfo();
      fetchRecentBlocks();
      fetchMempool();
      fetchMiningStatus();
    }
  };

  return (
    <BlockchainContext.Provider value={value}>
      {children}
    </BlockchainContext.Provider>
  );
};
