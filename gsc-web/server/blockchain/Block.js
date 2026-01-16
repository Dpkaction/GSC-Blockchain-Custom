const crypto = require('crypto');
const Transaction = require('./Transaction');

class Block {
    constructor(index, transactions, timestamp, previousHash, nonce = 0, difficulty = 5) {
        this.index = index;
        this.timestamp = timestamp || Date.now();
        this.transactions = transactions || [];
        this.previousHash = previousHash;
        this.nonce = nonce;
        this.difficulty = difficulty;
        this.hash = this.calculateHash();
        this.merkleRoot = this.calculateMerkleRoot();
        this.miner = '';
        this.reward = 0;
    }

    calculateHash() {
        return crypto
            .createHash('sha256')
            .update(
                this.index +
                this.previousHash +
                this.timestamp +
                JSON.stringify(this.transactions) +
                this.nonce +
                this.merkleRoot
            )
            .digest('hex');
    }

    calculateMerkleRoot() {
        if (this.transactions.length === 0) {
            return crypto.createHash('sha256').update('').digest('hex');
        }

        let hashes = this.transactions.map(tx => tx.txId || tx.calculateHash());
        
        while (hashes.length > 1) {
            const newHashes = [];
            for (let i = 0; i < hashes.length; i += 2) {
                const left = hashes[i];
                const right = hashes[i + 1] || left;
                const combined = crypto.createHash('sha256').update(left + right).digest('hex');
                newHashes.push(combined);
            }
            hashes = newHashes;
        }

        return hashes[0];
    }

    mineBlock(difficulty, minerAddress, callback) {
        const target = '0'.repeat(difficulty);
        const startTime = Date.now();
        let hashRate = 0;
        let lastUpdate = startTime;

        this.miner = minerAddress;
        
        while (this.hash.substring(0, difficulty) !== target) {
            this.nonce++;
            this.hash = this.calculateHash();
            
            // Update hash rate every 1000 hashes
            if (this.nonce % 1000 === 0) {
                const now = Date.now();
                const elapsed = (now - lastUpdate) / 1000;
                hashRate = 1000 / elapsed;
                lastUpdate = now;
                
                if (callback) {
                    callback({
                        nonce: this.nonce,
                        hashRate: hashRate,
                        hash: this.hash,
                        target: target
                    });
                }
            }
        }

        const miningTime = (Date.now() - startTime) / 1000;
        console.log(`Block ${this.index} mined! Hash: ${this.hash}`);
        console.log(`Nonce: ${this.nonce}, Time: ${miningTime.toFixed(2)}s`);
        
        return {
            nonce: this.nonce,
            hash: this.hash,
            miningTime: miningTime,
            hashRate: this.nonce / miningTime
        };
    }

    isValid(previousBlock) {
        // Check if block hash is valid
        if (this.hash !== this.calculateHash()) {
            return false;
        }

        // Check if previous hash matches
        if (previousBlock && this.previousHash !== previousBlock.hash) {
            return false;
        }

        // Check proof of work
        if (!this.hash.startsWith('0'.repeat(this.difficulty))) {
            return false;
        }

        // Check merkle root
        if (this.merkleRoot !== this.calculateMerkleRoot()) {
            return false;
        }

        // Validate all transactions
        for (const tx of this.transactions) {
            if (!tx.isValid()) {
                return false;
            }
        }

        return true;
    }

    toJSON() {
        return {
            index: this.index,
            timestamp: this.timestamp,
            transactions: this.transactions.map(tx => tx.toJSON ? tx.toJSON() : tx),
            previousHash: this.previousHash,
            nonce: this.nonce,
            hash: this.hash,
            merkleRoot: this.merkleRoot,
            difficulty: this.difficulty,
            miner: this.miner,
            reward: this.reward
        };
    }

    static fromJSON(data) {
        const transactions = data.transactions.map(tx => 
            tx.toJSON ? tx : Transaction.fromJSON(tx)
        );
        
        const block = new Block(
            data.index,
            transactions,
            data.timestamp,
            data.previousHash,
            data.nonce,
            data.difficulty
        );
        
        block.hash = data.hash;
        block.merkleRoot = data.merkleRoot;
        block.miner = data.miner;
        block.reward = data.reward;
        
        return block;
    }
}

module.exports = Block;
