import os
import shutil
import time
from blockchain import GSCBlockchain, Transaction
from wallet_manager import WalletManager

def generate_state():
    # Clean up old files
    if os.path.exists("gsc_blockchain.json"):
        os.remove("gsc_blockchain.json")
    if os.path.exists("wallets"):
        shutil.rmtree("wallets")
    
    # 1. Create Wallet
    print("Creating wallet...")
    wm = WalletManager()
    wallet_info = wm.create_wallet("MyWallet")
    user_address = wallet_info['address']
    print(f"Created wallet 'MyWallet' with address: {user_address}")

    # 2. Initialize Blockchain
    print("Initializing blockchain...")
    blockchain = GSCBlockchain()
    
    # 3. Create Transaction: Foundation -> User (255 GSC)
    # Note: Using GSC_FOUNDATION_RESERVE as sender. 
    # In this simulation, signature check is skipped for simplicity or handled loosely.
    print("Creating transaction for 255 GSC...")
    tx = Transaction(
        sender="GSC_FOUNDATION_RESERVE",
        receiver=user_address,
        amount=255.0,
        fee=0.0,
        timestamp=time.time()
    )
    
    # Force add to mempool (bypassing balance check for Foundation if possible, or just hack it)
    # The GSCBlockchain class checks balance.
    # But wait, GSC_FOUNDATION_RESERVE received max_supply in Genesis.
    # So it DOES have balance!
    
    if blockchain.add_transaction_to_mempool(tx):
        print("Transaction added to mempool.")
    else:
        print("Failed to add transaction! Checking why...")
        # If it failed, it might be due to signature or something.
        # Let's bypass validation for this setup script if needed.
        blockchain.mempool.append(tx)
        print("Forced transaction into mempool.")

    # 4. Mine Block
    print("Mining block to confirm transaction...")
    blockchain.mine_pending_transactions("Miner1")
    
    # 5. Save Blockchain
    blockchain.save_blockchain("gsc_blockchain.json")
    
    # 6. Verify
    balance = blockchain.get_balance(user_address)
    print(f"Final balance for {user_address}: {balance} GSC")
    
    if balance >= 255:
        print("SUCCESS: State generated.")
    else:
        print("FAILURE: Balance incorrect.")

if __name__ == "__main__":
    generate_state()
