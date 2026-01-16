const fs = require('fs');
const path = require('path');
const Transaction = require('./Transaction');
const Block = require('./Block');

class GSCBlockchain {
    constructor() {
        this.chain = [];
        this.difficulty = 5; // Fixed difficulty (4 leading zeros)
        this.mempool = [];
        this.balances = {};
        this.miningReward = 50.0;
        this.isMining = false;
        this.blockTimeTarget = 120; // 2 minutes in seconds
        this.halvingInterval = 1051200; // 4 years at 2-minute blocks
        this.totalSupply = 21750000000000; // 21.75 trillion GSC
        this.currentSupply = 0;
        
        // Genesis configuration
        this.genesisAddress = 'GSC1705641e65321ef23ac5fb3d470f39627';
        this.genesisReward = 255.0;
        
        // Initialize blockchain
        this.createGenesisBlock();
        this.loadBlockchain();
    }

    createGenesisBlock() {
        console.log('Creating GSC Coin Genesis Block...');
        console.log('Genesis block with minimal allocation - only 255 GSC genesis reward');
        
        // Genesis transaction - only 255 GSC to genesis address
        const genesisTransaction = new Transaction(
            'GENESIS',
            this.genesisAddress,
            this.genesisReward,
            0.0,
            1704067200000 // Jan 1, 2024
        );
        
        const genesisBlock = new Block(
            0,
            [genesisTransaction],
            1704067200000,
            '0'.repeat(64),
            0,
            1 // Minimal difficulty for genesis
        );
        
        // Mine genesis block
        genesisBlock.mineBlock(1, 'GENESIS');
        this.chain.push(genesisBlock);
        
        // Update balances
        this.updateBalances();
        this.currentSupply = this.genesisReward;
        
        console.log(`GSC Coin Genesis Block Created!`);
        console.log(`Genesis Hash: ${genesisBlock.hash}`);
        console.log(`Genesis Address Balance: ${this.genesisReward} GSC`);
        console.log(`Total Genesis Supply: ${this.currentSupply} GSC`);
        console.log(`Remaining supply (21.75T - 255) will be created through mining`);
    }

    getLatestBlock() {
        return this.chain[this.chain.length - 1];
    }

    getCurrentReward() {
        const blockHeight = this.chain.length - 1;
        if (blockHeight === 0) return this.miningReward;
        
        const halvings = Math.floor((blockHeight - 1) / this.halvingInterval);
        if (halvings >= 64) return 0;
        
        return this.miningReward / Math.pow(2, halvings);
    }

    addTransactionToMempool(transaction) {
        if (!this.isTransactionValid(transaction)) {
            return { success: false, message: 'Invalid transaction' };
        }

        // Check sender balance
        const senderBalance = this.getBalance(transaction.sender);
        const totalCost = transaction.amount + transaction.fee;
        
        if (senderBalance < totalCost) {
            return { 
                success: false, 
                message: `Insufficient balance. Required: ${totalCost}, Available: ${senderBalance}` 
            };
        }

        // Check for duplicate transaction
        const exists = this.mempool.some(tx => tx.txId === transaction.txId);
        if (exists) {
            return { success: false, message: 'Transaction already in mempool' };
        }

        this.mempool.push(transaction);
        console.log(`Transaction added to mempool: ${transaction.txId.substring(0, 16)}...`);
        
        return { success: true, message: 'Transaction added to mempool' };
    }

    isTransactionValid(transaction) {
        if (!transaction.isValid()) return false;
        
        // Check for double spending in mempool
        const senderTxs = this.mempool.filter(tx => tx.sender === transaction.sender);
        const totalSpending = senderTxs.reduce((sum, tx) => sum + tx.amount + tx.fee, 0);
        const senderBalance = this.getBalance(transaction.sender);
        
        return (totalSpending + transaction.amount + transaction.fee) <= senderBalance;
    }

    minePendingTransactions(minerAddress, callback, forceMine = false) {
        if (!this.mempool.length && !forceMine) {
            console.log('⏳ No transactions in mempool - smart mining waiting for transactions');
            return null;
        }

        if (this.isMining) {
            console.log('Mining already in progress...');
            return null;
        }

        this.isMining = true;
        
        try {
            // Select transactions from mempool (up to 10 per block)
            const selectedTransactions = this.mempool.slice(0, 10);
            
            // Create coinbase transaction (mining reward)
            const currentReward = this.getCurrentReward();
            const totalFees = selectedTransactions.reduce((sum, tx) => sum + tx.fee, 0);
            
            const coinbaseTransaction = new Transaction(
                'COINBASE',
                minerAddress,
                currentReward + totalFees,
                0.0
            );

            // Create new block
            const newBlock = new Block(
                this.chain.length,
                [coinbaseTransaction, ...selectedTransactions],
                Date.now(),
                this.getLatestBlock().hash,
                0,
                this.difficulty
            );

            newBlock.reward = currentReward;
            newBlock.miner = minerAddress;

            // Mine the block
            const miningStats = newBlock.mineBlock(this.difficulty, minerAddress, callback);

            // Add block to chain
            if (this.addBlock(newBlock)) {
                // Remove mined transactions from mempool
                selectedTransactions.forEach(tx => {
                    const index = this.mempool.findIndex(mempoolTx => mempoolTx.txId === tx.txId);
                    if (index > -1) {
                        this.mempool.splice(index, 1);
                    }
                });

                console.log(`Block ${newBlock.index} successfully mined and added to GSC blockchain!`);
                console.log(`Block Hash: ${newBlock.hash}`);
                console.log(`Mining Reward: ${newBlock.reward} GSC`);
                console.log(`Transactions: ${newBlock.transactions.length}`);

                this.saveBlockchain();
                return newBlock;
            } else {
                console.log('Failed to add mined block to chain!');
                return null;
            }
        } finally {
            this.isMining = false;
        }
    }

    addBlock(newBlock) {
        const previousBlock = this.getLatestBlock();
        
        if (newBlock.isValid(previousBlock)) {
            this.chain.push(newBlock);
            this.updateBalances();
            return true;
        }
        
        return false;
    }

    updateBalances() {
        this.balances = {};
        
        for (const block of this.chain) {
            for (const transaction of block.transactions) {
                // Deduct from sender (except system transactions)
                if (!['COINBASE', 'GENESIS'].includes(transaction.sender)) {
                    if (!this.balances[transaction.sender]) {
                        this.balances[transaction.sender] = 0;
                    }
                    this.balances[transaction.sender] -= (transaction.amount + transaction.fee);
                }
                
                // Add to receiver
                if (!this.balances[transaction.receiver]) {
                    this.balances[transaction.receiver] = 0;
                }
                this.balances[transaction.receiver] += transaction.amount;
                
                // Add fee to miner (if not coinbase transaction)
                if (transaction.sender !== 'COINBASE' && block.miner) {
                    if (!this.balances[block.miner]) {
                        this.balances[block.miner] = 0;
                    }
                    this.balances[block.miner] += transaction.fee;
                }
            }
        }
    }

    getBalance(address) {
        return this.balances[address] || 0;
    }

    isChainValid() {
        for (let i = 1; i < this.chain.length; i++) {
            const currentBlock = this.chain[i];
            const previousBlock = this.chain[i - 1];
            
            if (!currentBlock.isValid(previousBlock)) {
                return false;
            }
        }
        return true;
    }

    getBlockchainStats() {
        return {
            totalBlocks: this.chain.length,
            mempoolSize: this.mempool.length,
            totalSupply: this.totalSupply,
            currentSupply: this.currentSupply,
            difficulty: this.difficulty,
            blockTimeTarget: this.blockTimeTarget,
            halvingInterval: this.halvingInterval,
            currentReward: this.getCurrentReward(),
            isChainValid: this.isChainValid()
        };
    }

    getRecentBlocks(limit = 10) {
        return this.chain.slice(-limit).reverse();
    }

    getBlockByIndex(index) {
        return this.chain[index] || null;
    }

    getTransactionById(txId) {
        for (const block of this.chain) {
            for (const tx of block.transactions) {
                if (tx.txId === txId) {
                    return { transaction: tx, blockIndex: block.index };
                }
            }
        }
        
        // Check mempool
        const mempoolTx = this.mempool.find(tx => tx.txId === txId);
        if (mempoolTx) {
            return { transaction: mempoolTx, blockIndex: -1 };
        }
        
        return null;
    }

    saveBlockchain() {
        try {
            const data = {
                chain: this.chain.map(block => block.toJSON()),
                mempool: this.mempool.map(tx => tx.toJSON()),
                balances: this.balances,
                currentSupply: this.currentSupply
            };
            
            const filePath = path.join(__dirname, '../../data/blockchain.json');
            const dir = path.dirname(filePath);
            
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
            console.log('Blockchain saved successfully');
        } catch (error) {
            console.error('Error saving blockchain:', error);
        }
    }

    loadBlockchain() {
        try {
            const filePath = path.join(__dirname, '../../data/blockchain.json');
            
            if (fs.existsSync(filePath)) {
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                
                // Only load if we have more than just genesis block
                if (data.chain && data.chain.length > 1) {
                    this.chain = data.chain.map(blockData => Block.fromJSON(blockData));
                    this.mempool = (data.mempool || []).map(txData => Transaction.fromJSON(txData));
                    this.balances = data.balances || {};
                    this.currentSupply = data.currentSupply || this.genesisReward;
                    
                    console.log(`Blockchain loaded: ${this.chain.length} blocks`);
                } else {
                    console.log('Using fresh genesis blockchain');
                }
            } else {
                console.log('No existing blockchain found, using genesis block');
            }
        } catch (error) {
            console.error('Error loading blockchain:', error);
            console.log('Using fresh genesis blockchain');
        }
    }
}

module.exports = GSCBlockchain;
