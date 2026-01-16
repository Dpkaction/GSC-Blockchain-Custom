#!/usr/bin/env python3
"""
Create New GSC Genesis Block
With 2.75 trillion GSC for foundation and 255 GSC for genesis address
"""

import os
from blockchain import GSCBlockchain

def create_new_genesis():
    """Create new genesis blockchain with updated parameters"""
    
    print("🚀 Creating New GSC Genesis Blockchain")
    print("=" * 50)
    
    # Remove old blockchain
    if os.path.exists('gsc_blockchain.json'):
        os.remove('gsc_blockchain.json')
        print("✅ Removed old blockchain")
    
    # Create new blockchain with updated genesis
    blockchain = GSCBlockchain()
    
    print("\n📊 Genesis Block Created:")
    print(f"   Foundation Balance: {blockchain.get_balance('GSC_FOUNDATION_RESERVE'):,.0f} GSC")
    print(f"   Genesis Address Balance: {blockchain.get_balance('GSC1705641e65321ef23ac5fb3d470f39627')} GSC")
    print(f"   Total Genesis Supply: {blockchain.current_supply:,.0f} GSC")
    print(f"   Maximum Total Supply: 21,750,000,000,000 GSC")
    print(f"   Genesis Hash: {blockchain.chain[0].hash}")
    print(f"   Genesis Transactions: {len(blockchain.chain[0].transactions)}")
    
    # Validate blockchain
    is_valid = blockchain.is_chain_valid()
    print(f"   Blockchain Valid: {is_valid}")
    
    # Save new blockchain
    blockchain.save_blockchain('gsc_blockchain.json')
    print("\n✅ New genesis blockchain saved to gsc_blockchain.json")
    
    # Show transaction details
    print("\n📋 Genesis Transactions:")
    for i, tx in enumerate(blockchain.chain[0].transactions):
        print(f"   {i+1}. {tx.sender} -> {tx.receiver}: {tx.amount:,.0f} GSC")
    
    print("\n🎉 Genesis blockchain creation complete!")
    return blockchain

if __name__ == "__main__":
    create_new_genesis()
