const crypto = require('crypto');

class WalletManager {
    constructor() {
        this.wallets = new Map();
    }

    generateMnemonic() {
        const words = [
            'abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb', 'abstract',
            'absurd', 'abuse', 'access', 'accident', 'account', 'accuse', 'achieve', 'acid',
            'acoustic', 'acquire', 'across', 'act', 'action', 'actor', 'actress', 'actual',
            'adapt', 'add', 'addict', 'address', 'adjust', 'admit', 'adult', 'advance',
            'advice', 'aerobic', 'affair', 'afford', 'afraid', 'again', 'against', 'age',
            'agent', 'agree', 'ahead', 'aim', 'air', 'airport', 'aisle', 'alarm',
            'album', 'alcohol', 'alert', 'alien', 'all', 'alley', 'allow', 'almost',
            'alone', 'alpha', 'already', 'also', 'alter', 'always', 'amateur', 'amazing',
            'among', 'amount', 'amused', 'analyst', 'anchor', 'ancient', 'anger', 'angle',
            'angry', 'animal', 'ankle', 'announce', 'annual', 'another', 'answer', 'antenna'
        ];
        
        const mnemonic = [];
        for (let i = 0; i < 12; i++) {
            mnemonic.push(words[Math.floor(Math.random() * words.length)]);
        }
        return mnemonic.join(' ');
    }

    generatePrivateKey() {
        return crypto.randomBytes(32).toString('hex');
    }

    generateAddress(privateKey) {
        const hash = crypto.createHash('sha256').update(privateKey).digest('hex');
        return 'GSC' + hash.substring(0, 32);
    }

    createWallet(name) {
        const mnemonic = this.generateMnemonic();
        const privateKey = this.generatePrivateKey();
        const address = this.generateAddress(privateKey);
        
        const wallet = {
            id: crypto.randomUUID(),
            name: name || `Wallet ${this.wallets.size + 1}`,
            address,
            privateKey,
            mnemonic,
            balance: 0,
            created: Date.now()
        };
        
        this.wallets.set(wallet.id, wallet);
        return wallet;
    }

    importWallet(mnemonic, name) {
        const privateKey = crypto.createHash('sha256').update(mnemonic).digest('hex');
        const address = this.generateAddress(privateKey);
        
        const wallet = {
            id: crypto.randomUUID(),
            name: name || 'Imported Wallet',
            address,
            privateKey,
            mnemonic,
            balance: 0,
            imported: true,
            created: Date.now()
        };
        
        this.wallets.set(wallet.id, wallet);
        return wallet;
    }

    getWallet(id) {
        return this.wallets.get(id);
    }

    getAllWallets() {
        return Array.from(this.wallets.values());
    }

    deleteWallet(id) {
        return this.wallets.delete(id);
    }
}

module.exports = WalletManager;
