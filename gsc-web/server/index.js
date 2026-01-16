const express = require('express');
const cors = require('cors');
const WebSocket = require('ws');
const http = require('http');
const path = require('path');
const compression = require('compression');
const helmet = require('helmet');
const { RateLimiterMemory } = require('rate-limiter-flexible');

const GSCBlockchain = require('./blockchain/Blockchain');
const Transaction = require('./blockchain/Transaction');
const WalletManager = require('./wallet/WalletManager');

// Initialize Express app
const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Initialize blockchain and wallet manager
const blockchain = new GSCBlockchain();
const walletManager = new WalletManager();

// Rate limiting
const rateLimiter = new RateLimiterMemory({
    keyGenerator: (req) => req.ip,
    points: 100, // Number of requests
    duration: 60, // Per 60 seconds
});

// Middleware
app.use(helmet({
    contentSecurityPolicy: false, // Disable for development
}));
app.use(compression());
app.use(cors({
    origin: process.env.NODE_ENV === 'production' 
        ? ['https://gsc-coin.vercel.app', 'https://gsccoin.network']
        : ['http://localhost:3000', 'http://localhost:3001'],
    credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname, '../client/build')));

// Rate limiting middleware
app.use(async (req, res, next) => {
    try {
        await rateLimiter.consume(req.ip);
        next();
    } catch (rejRes) {
        res.status(429).json({ 
            error: 'Too many requests', 
            retryAfter: Math.round(rejRes.msBeforeNext / 1000) 
        });
    }
});

// WebSocket connections for real-time updates
const clients = new Set();

wss.on('connection', (ws) => {
    clients.add(ws);
    console.log('New WebSocket client connected');
    
    // Send initial blockchain state
    ws.send(JSON.stringify({
        type: 'blockchain_state',
        data: {
            stats: blockchain.getBlockchainStats(),
            recentBlocks: blockchain.getRecentBlocks(5),
            mempool: blockchain.mempool.map(tx => tx.toJSON())
        }
    }));
    
    ws.on('close', () => {
        clients.delete(ws);
        console.log('WebSocket client disconnected');
    });
    
    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        clients.delete(ws);
    });
});

// Broadcast to all connected clients
function broadcast(message) {
    const data = JSON.stringify(message);
    clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(data);
        }
    });
}

// Mining state
let miningState = {
    isMining: false,
    minerAddress: null,
    currentBlock: null,
    stats: {}
};

// API Routes

// Get blockchain information
app.get('/api/blockchain/info', (req, res) => {
    try {
        const stats = blockchain.getBlockchainStats();
        res.json({
            success: true,
            data: stats
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get blocks with pagination
app.get('/api/blockchain/blocks', (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 10;
        const offset = (page - 1) * limit;
        
        const totalBlocks = blockchain.chain.length;
        const blocks = blockchain.chain
            .slice(Math.max(0, totalBlocks - offset - limit), totalBlocks - offset)
            .reverse()
            .map(block => block.toJSON());
        
        res.json({
            success: true,
            data: {
                blocks,
                pagination: {
                    page,
                    limit,
                    total: totalBlocks,
                    pages: Math.ceil(totalBlocks / limit)
                }
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get specific block
app.get('/api/blockchain/blocks/:index', (req, res) => {
    try {
        const index = parseInt(req.params.index);
        const block = blockchain.getBlockByIndex(index);
        
        if (!block) {
            return res.status(404).json({
                success: false,
                error: 'Block not found'
            });
        }
        
        res.json({
            success: true,
            data: block.toJSON()
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get balance for address
app.get('/api/blockchain/balance/:address', (req, res) => {
    try {
        const address = req.params.address;
        const balance = blockchain.getBalance(address);
        
        res.json({
            success: true,
            data: {
                address,
                balance
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get mempool transactions
app.get('/api/blockchain/mempool', (req, res) => {
    try {
        const mempool = blockchain.mempool.map(tx => tx.toJSON());
        
        res.json({
            success: true,
            data: {
                transactions: mempool,
                count: mempool.length
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Submit new transaction
app.post('/api/blockchain/transactions', (req, res) => {
    try {
        const { sender, receiver, amount, fee } = req.body;
        
        if (!sender || !receiver || !amount) {
            return res.status(400).json({
                success: false,
                error: 'Missing required fields: sender, receiver, amount'
            });
        }
        
        const transaction = new Transaction(sender, receiver, parseFloat(amount), parseFloat(fee) || 0.1);
        const result = blockchain.addTransactionToMempool(transaction);
        
        if (result.success) {
            // Broadcast new transaction to all clients
            broadcast({
                type: 'new_transaction',
                data: transaction.toJSON()
            });
            
            // Broadcast updated mempool
            broadcast({
                type: 'mempool_update',
                data: blockchain.mempool.map(tx => tx.toJSON())
            });
        }
        
        res.json(result);
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get transaction by ID
app.get('/api/blockchain/transactions/:txId', (req, res) => {
    try {
        const txId = req.params.txId;
        const result = blockchain.getTransactionById(txId);
        
        if (!result) {
            return res.status(404).json({
                success: false,
                error: 'Transaction not found'
            });
        }
        
        res.json({
            success: true,
            data: {
                transaction: result.transaction.toJSON(),
                blockIndex: result.blockIndex,
                confirmed: result.blockIndex !== -1
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Start mining
app.post('/api/mining/start', (req, res) => {
    try {
        const { minerAddress } = req.body;
        
        if (!minerAddress) {
            return res.status(400).json({
                success: false,
                error: 'Miner address is required'
            });
        }
        
        if (miningState.isMining) {
            return res.status(400).json({
                success: false,
                error: 'Mining already in progress'
            });
        }
        
        // Check if mempool has transactions
        if (blockchain.mempool.length === 0) {
            return res.json({
                success: true,
                message: 'Waiting for transactions in mempool before mining',
                waiting: true
            });
        }
        
        miningState.isMining = true;
        miningState.minerAddress = minerAddress;
        
        // Start mining in background
        setImmediate(() => {
            const miningCallback = (stats) => {
                miningState.stats = stats;
                broadcast({
                    type: 'mining_update',
                    data: {
                        ...stats,
                        minerAddress,
                        mempool: blockchain.mempool.length
                    }
                });
            };
            
            const newBlock = blockchain.minePendingTransactions(minerAddress, miningCallback);
            
            miningState.isMining = false;
            
            if (newBlock) {
                broadcast({
                    type: 'new_block',
                    data: {
                        block: newBlock.toJSON(),
                        stats: blockchain.getBlockchainStats()
                    }
                });
                
                broadcast({
                    type: 'mempool_update',
                    data: blockchain.mempool.map(tx => tx.toJSON())
                });
            }
        });
        
        res.json({
            success: true,
            message: 'Mining started',
            minerAddress
        });
    } catch (error) {
        miningState.isMining = false;
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Stop mining
app.post('/api/mining/stop', (req, res) => {
    try {
        miningState.isMining = false;
        miningState.minerAddress = null;
        miningState.currentBlock = null;
        miningState.stats = {};
        
        broadcast({
            type: 'mining_stopped',
            data: {}
        });
        
        res.json({
            success: true,
            message: 'Mining stopped'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get mining status
app.get('/api/mining/status', (req, res) => {
    try {
        res.json({
            success: true,
            data: {
                isMining: miningState.isMining,
                minerAddress: miningState.minerAddress,
                stats: miningState.stats,
                mempoolSize: blockchain.mempool.length
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Validate blockchain
app.get('/api/blockchain/validate', (req, res) => {
    try {
        const isValid = blockchain.isChainValid();
        
        res.json({
            success: true,
            data: {
                isValid,
                message: isValid ? 'Blockchain is valid' : 'Blockchain validation failed'
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Enhanced wallet management endpoints

// Create new wallet with mnemonic
app.post('/api/wallet/create', (req, res) => {
    try {
        const { name } = req.body;
        const wallet = walletManager.createWallet(name);
        
        // Get balance from blockchain
        wallet.balance = blockchain.getBalance(wallet.address);
        
        res.json({
            success: true,
            data: wallet
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Import wallet from mnemonic
app.post('/api/wallet/import', (req, res) => {
    try {
        const { mnemonic, name } = req.body;
        
        if (!mnemonic) {
            return res.status(400).json({
                success: false,
                error: 'Mnemonic phrase is required'
            });
        }
        
        const wallet = walletManager.importWallet(mnemonic, name);
        wallet.balance = blockchain.getBalance(wallet.address);
        
        res.json({
            success: true,
            data: wallet
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get all wallets
app.get('/api/wallet/list', (req, res) => {
    try {
        const wallets = walletManager.getAllWallets().map(wallet => ({
            ...wallet,
            balance: blockchain.getBalance(wallet.address),
            // Don't expose private key in list
            privateKey: undefined
        }));
        
        res.json({
            success: true,
            data: wallets
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get specific wallet details
app.get('/api/wallet/:id', (req, res) => {
    try {
        const wallet = walletManager.getWallet(req.params.id);
        if (!wallet) {
            return res.status(404).json({
                success: false,
                error: 'Wallet not found'
            });
        }
        
        wallet.balance = blockchain.getBalance(wallet.address);
        
        res.json({
            success: true,
            data: wallet
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Delete wallet
app.delete('/api/wallet/:id', (req, res) => {
    try {
        const deleted = walletManager.deleteWallet(req.params.id);
        
        res.json({
            success: deleted,
            message: deleted ? 'Wallet deleted successfully' : 'Wallet not found'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Generate wallet address (legacy endpoint)
app.post('/api/wallet/generate', (req, res) => {
    try {
        const wallet = walletManager.createWallet();
        wallet.balance = blockchain.getBalance(wallet.address);
        
        res.json({
            success: true,
            data: {
                address: wallet.address,
                balance: wallet.balance
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Health check
app.get('/api/health', (req, res) => {
    res.json({
        success: true,
        data: {
            status: 'healthy',
            timestamp: Date.now(),
            blockchain: {
                blocks: blockchain.chain.length,
                mempool: blockchain.mempool.length,
                valid: blockchain.isChainValid()
            }
        }
    });
});

// Serve React app for all other routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../client/build/index.html'));
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('API Error:', error);
    res.status(500).json({
        success: false,
        error: 'Internal server error'
    });
});

// Auto-mining when transactions are available
setInterval(() => {
    if (!miningState.isMining && blockchain.mempool.length > 0) {
        console.log(`Auto-mining triggered: ${blockchain.mempool.length} transactions in mempool`);
        
        // Use genesis address as default miner if no one is mining
        const defaultMiner = blockchain.genesisAddress;
        
        miningState.isMining = true;
        miningState.minerAddress = defaultMiner;
        
        setImmediate(() => {
            const miningCallback = (stats) => {
                broadcast({
                    type: 'mining_update',
                    data: {
                        ...stats,
                        minerAddress: defaultMiner,
                        mempool: blockchain.mempool.length,
                        autoMining: true
                    }
                });
            };
            
            const newBlock = blockchain.minePendingTransactions(defaultMiner, miningCallback);
            
            miningState.isMining = false;
            
            if (newBlock) {
                broadcast({
                    type: 'new_block',
                    data: {
                        block: newBlock.toJSON(),
                        stats: blockchain.getBlockchainStats(),
                        autoMining: true
                    }
                });
                
                broadcast({
                    type: 'mempool_update',
                    data: blockchain.mempool.map(tx => tx.toJSON())
                });
            }
        });
    }
}, 30000); // Check every 30 seconds

// Start server
const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
    console.log(`🚀 GSC Coin Server running on port ${PORT}`);
    console.log(`📊 Blockchain initialized with ${blockchain.chain.length} blocks`);
    console.log(`💰 Genesis address: ${blockchain.genesisAddress}`);
    console.log(`🎯 Smart mining enabled - will mine when transactions are available`);
});

module.exports = app;
