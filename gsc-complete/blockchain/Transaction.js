const crypto = require('crypto');

class Transaction {
    constructor(sender, receiver, amount, fee = 0.1, timestamp = null) {
        this.sender = sender;
        this.receiver = receiver;
        this.amount = parseFloat(amount);
        this.fee = parseFloat(fee);
        this.timestamp = timestamp || Date.now();
        this.signature = '';
        this.txId = this.calculateHash();
    }

    calculateHash() {
        return crypto
            .createHash('sha256')
            .update(this.sender + this.receiver + this.amount + this.fee + this.timestamp)
            .digest('hex');
    }

    isValid() {
        if (!this.sender || !this.receiver) return false;
        if (this.amount <= 0) return false;
        if (this.fee < 0) return false;
        
        // System transactions are always valid
        if (this.sender === 'COINBASE' || this.sender === 'GENESIS') {
            return true;
        }
        
        return this.txId === this.calculateHash();
    }

    signTransaction(privateKey) {
        const hash = this.calculateHash();
        this.signature = crypto
            .createHash('sha256')
            .update(hash + privateKey)
            .digest('hex');
    }

    toJSON() {
        return {
            sender: this.sender,
            receiver: this.receiver,
            amount: this.amount,
            fee: this.fee,
            timestamp: this.timestamp,
            signature: this.signature,
            txId: this.txId
        };
    }

    static fromJSON(data) {
        const tx = new Transaction(
            data.sender,
            data.receiver,
            data.amount,
            data.fee,
            data.timestamp
        );
        tx.signature = data.signature;
        tx.txId = data.txId;
        return tx;
    }
}

module.exports = Transaction;
