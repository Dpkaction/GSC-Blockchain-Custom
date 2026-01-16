const express = require('express');
const cors = require('cors');
const WebSocket = require('ws');
const http = require('http');
const path = require('path');

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

// Middleware
app.use(cors());
app.use(express.json());
// Serve static files
const fs = require('fs');
const clientBuildPath = path.join(__dirname, 'client/build');
const publicPath = path.join(__dirname, 'public');

if (fs.existsSync(clientBuildPath)) {
    app.use(express.static(clientBuildPath));
} else if (fs.existsSync(publicPath)) {
    app.use(express.static(publicPath));
}

// WebSocket connections
const clients = new Set();

wss.on('connection', (ws) => {
    clients.add(ws);
    console.log('🔗 New WebSocket client connected');
    
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
        console.log('❌ WebSocket client disconnected');
    });
});

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
    stats: {}
};

// API Routes

// Blockchain info
app.get('/api/blockchain/info', (req, res) => {
    res.json({
        success: true,
        data: blockchain.getBlockchainStats()
    });
});

// Get blocks
app.get('/api/blockchain/blocks', (req, res) => {
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
});

// Get specific block
app.get('/api/blockchain/blocks/:index', (req, res) => {
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
});

// Get balance
app.get('/api/blockchain/balance/:address', (req, res) => {
    const address = req.params.address;
    const balance = blockchain.getBalance(address);
    
    res.json({
        success: true,
        data: {
            address,
            balance
        }
    });
});

// Get mempool
app.get('/api/blockchain/mempool', (req, res) => {
    const mempool = blockchain.mempool.map(tx => tx.toJSON());
    
    res.json({
        success: true,
        data: {
            transactions: mempool,
            count: mempool.length
        }
    });
});

// Submit transaction
app.post('/api/blockchain/transactions', (req, res) => {
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
        broadcast({
            type: 'new_transaction',
            data: transaction.toJSON()
        });
        
        broadcast({
            type: 'mempool_update',
            data: blockchain.mempool.map(tx => tx.toJSON())
        });
    }
    
    res.json(result);
});

// Get transaction by ID
app.get('/api/blockchain/transactions/:txId', (req, res) => {
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
});

// Start mining
app.post('/api/mining/start', (req, res) => {
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
    
    if (blockchain.mempool.length === 0) {
        return res.json({
            success: true,
            message: 'Waiting for transactions in mempool before mining',
            waiting: true
        });
    }
    
    miningState.isMining = true;
    miningState.minerAddress = minerAddress;
    
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
});

// Stop mining
app.post('/api/mining/stop', (req, res) => {
    miningState.isMining = false;
    miningState.minerAddress = null;
    miningState.stats = {};
    
    broadcast({
        type: 'mining_stopped',
        data: {}
    });
    
    res.json({
        success: true,
        message: 'Mining stopped'
    });
});

// Get mining status
app.get('/api/mining/status', (req, res) => {
    res.json({
        success: true,
        data: {
            isMining: miningState.isMining,
            minerAddress: miningState.minerAddress,
            stats: miningState.stats,
            mempoolSize: blockchain.mempool.length
        }
    });
});

// Wallet endpoints

// Create wallet
app.post('/api/wallet/create', (req, res) => {
    const { name } = req.body;
    const wallet = walletManager.createWallet(name);
    wallet.balance = blockchain.getBalance(wallet.address);
    
    res.json({
        success: true,
        data: wallet
    });
});

// Import wallet
app.post('/api/wallet/import', (req, res) => {
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
});

// Get all wallets
app.get('/api/wallet/list', (req, res) => {
    const wallets = walletManager.getAllWallets().map(wallet => ({
        ...wallet,
        balance: blockchain.getBalance(wallet.address),
        privateKey: undefined // Don't expose private key in list
    }));
    
    res.json({
        success: true,
        data: wallets
    });
});

// Get wallet details
app.get('/api/wallet/:id', (req, res) => {
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
});

// Delete wallet
app.delete('/api/wallet/:id', (req, res) => {
    const deleted = walletManager.deleteWallet(req.params.id);
    
    res.json({
        success: deleted,
        message: deleted ? 'Wallet deleted successfully' : 'Wallet not found'
    });
});

// Validate blockchain
app.get('/api/blockchain/validate', (req, res) => {
    const isValid = blockchain.isChainValid();
    
    res.json({
        success: true,
        data: {
            isValid,
            message: isValid ? 'Blockchain is valid' : 'Blockchain validation failed'
        }
    });
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

// Serve UI or API info
app.get('*', (req, res) => {
    const clientIndexPath = path.join(__dirname, 'client/build/index.html');
    const publicIndexPath = path.join(__dirname, 'public/index.html');
    
    if (fs.existsSync(clientIndexPath)) {
        res.sendFile(clientIndexPath);
    } else if (fs.existsSync(publicIndexPath)) {
        res.sendFile(publicIndexPath);
    } else {
        // Show API documentation if no UI available
        res.json({
            name: 'GSC Coin Blockchain API',
            version: '1.0.0',
            description: 'Complete GSC Coin Blockchain Implementation',
            endpoints: {
                health: 'GET /api/health',
                blockchain: {
                    info: 'GET /api/blockchain/info',
                    blocks: 'GET /api/blockchain/blocks',
                    balance: 'GET /api/blockchain/balance/:address',
                    mempool: 'GET /api/blockchain/mempool',
                    transactions: 'POST /api/blockchain/transactions'
                },
                mining: {
                    start: 'POST /api/mining/start',
                    stop: 'POST /api/mining/stop',
                    status: 'GET /api/mining/status'
                },
                wallet: {
                    create: 'POST /api/wallet/create',
                    import: 'POST /api/wallet/import',
                    list: 'GET /api/wallet/list',
                    details: 'GET /api/wallet/:id',
                    delete: 'DELETE /api/wallet/:id'
                }
            },
            genesis: {
                address: blockchain.genesisAddress,
                balance: blockchain.getBalance(blockchain.genesisAddress)
            }
        });
    }
});

// Auto-mining when transactions are available
setInterval(() => {
    if (!miningState.isMining && blockchain.mempool.length > 0) {
        console.log(`🤖 Auto-mining triggered: ${blockchain.mempool.length} transactions in mempool`);
        
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
const PORT = process.env.PORT || 5001;
server.listen(PORT, () => {
    console.log(`🚀 GSC Coin Complete Server running on port ${PORT}`);
    console.log(`📊 Blockchain initialized with ${blockchain.chain.length} blocks`);
    console.log(`💰 Genesis address: ${blockchain.genesisAddress}`);
    console.log(`💎 Genesis balance: ${blockchain.getBalance(blockchain.genesisAddress)} GSC`);
    console.log(`🎯 Smart mining enabled - will mine when transactions are available`);
});

module.exports = app;
