import hashlib
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import Telegram bot for notifications
try:
    from telegram_bot import telegram_bot
    TELEGRAM_ENABLED = True
except ImportError:
    TELEGRAM_ENABLED = False
    print("Telegram bot not available - notifications disabled")
from dataclasses import dataclass, asdict
import pickle
import re

# Authorized mining addresses - mining rewards and fees go to the address that unlocked mining
AUTHORIZED_MINING_ADDRESSES = [
    "GSC1705641e65321ef23ac5fb3d470f39627",
    "GSC1221fe3e6139bbe0b76f0230d9cd5bbc1"
]

# Current active mining address (set when mining is unlocked)
CURRENT_MINING_ADDRESS = None

@dataclass
class Transaction:
    """GSC Coin Transaction Class"""
    sender: str
    receiver: str
    amount: float
    fee: float
    timestamp: float
    signature: str = ""
    tx_id: str = ""
    
    def __post_init__(self):
        if not self.tx_id:
            self.tx_id = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate transaction hash"""
        tx_string = f"{self.sender}{self.receiver}{self.amount}{self.fee}{self.timestamp}"
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def is_valid(self) -> bool:
        """Validate transaction"""
        if self.amount <= 0:
            return False
        if self.fee < 0:
            return False
        if self.sender == self.receiver:
            return False
        return True

@dataclass
class Block:
    """GSC Coin Block Class"""
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    nonce: int = 0
    hash: str = ""
    merkle_root: str = ""
    difficulty: int = 4
    miner: str = ""
    reward: float = 50.0
    
    def __post_init__(self):
        if not self.merkle_root:
            self.merkle_root = self.calculate_merkle_root()
        if not self.hash:
            self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate block hash"""
        block_string = f"{self.index}{self.timestamp}{self.previous_hash}{self.merkle_root}{self.nonce}{self.difficulty}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def calculate_merkle_root(self) -> str:
        """Calculate Merkle root of transactions"""
        if not self.transactions:
            return hashlib.sha256(b"").hexdigest()
        
        tx_hashes = [tx.tx_id for tx in self.transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])
            
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            
            tx_hashes = new_hashes
        
        return tx_hashes[0]
    
    def mine_block(self, difficulty: int, miner_address: str, callback=None) -> dict:
        """Mine the block with proof of work - all rewards go to authorized address"""
        # Enforce authorized mining address
        global CURRENT_MINING_ADDRESS
        if miner_address not in AUTHORIZED_MINING_ADDRESSES:
            if CURRENT_MINING_ADDRESS and CURRENT_MINING_ADDRESS in AUTHORIZED_MINING_ADDRESSES:
                print(f"WARNING: Mining address changed to current authorized address: {CURRENT_MINING_ADDRESS}")
                miner_address = CURRENT_MINING_ADDRESS
            else:
                print(f"WARNING: Mining address changed to default authorized address: {AUTHORIZED_MINING_ADDRESSES[0]}")
                miner_address = AUTHORIZED_MINING_ADDRESSES[0]
        
        target = "0" * difficulty
        mining_stats = {
            'start_time': time.time(),
            'nonce': 0,
            'hash_rate': 0,
            'found': False
        }
        
        self.difficulty = difficulty
        self.miner = miner_address
        
        # Note: Coinbase transaction should already be added by create_new_block()
        # Do not add another coinbase transaction here to avoid double rewards
        self.merkle_root = self.calculate_merkle_root()
        
        print(f"Mining GSC block {self.index} with difficulty {difficulty}...")
        
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
            mining_stats['nonce'] = self.nonce
            
            # Calculate hash rate every 1000 nonces
            if self.nonce % 1000 == 0:
                elapsed = time.time() - mining_stats['start_time']
                if elapsed > 0:
                    mining_stats['hash_rate'] = self.nonce / elapsed
                
                if callback:
                    callback(mining_stats)
        
        mining_stats['found'] = True
        mining_stats['final_time'] = time.time() - mining_stats['start_time']
        
        print(f"Block {self.index} mined! Hash: {self.hash}")
        print(f"Nonce: {self.nonce}, Time: {mining_stats['final_time']:.2f}s")
        
        return mining_stats
    
    def is_valid(self, previous_block=None) -> bool:
        """Validate block"""
        # Check hash
        if self.hash != self.calculate_hash():
            return False
        
        # Check previous hash
        if previous_block and self.previous_hash != previous_block.hash:
            return False
        
        # Check merkle root
        if self.merkle_root != self.calculate_merkle_root():
            return False
        
        # Check proof of work
        if not self.hash.startswith("0" * self.difficulty):
            return False
        
        # Validate transactions
        for tx in self.transactions:
            if not tx.is_valid():
                return False
        
        return True
    
    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash,
            'merkle_root': self.merkle_root,
            'difficulty': self.difficulty,
            'miner': self.miner,
            'reward': self.reward
        }
    
    def get_header(self) -> dict:
        """Get block header (block without transactions)"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash,
            'merkle_root': self.merkle_root,
            'difficulty': self.difficulty,
            'miner': self.miner,
            'reward': self.reward,
            'tx_count': len(self.transactions)
        }

class GSCBlockchain:
    """GSC Coin Blockchain Implementation"""
    
    def __init__(self):
        # Initialize basic attributes first
        self.difficulty = 8  # Fixed difficulty 8 (range 5-8 as requested)
        self.difficulty_locked = True  # Keep difficulty fixed as requested
        self.mempool = []
        self.balances = {}
        self.mining_reward = 50.0
        self.is_mining = False
        self.mining_stats = {}
        self.network_node = None
        self.block_height = 0
        self.nodes = []  # Initialize nodes list for network connectivity
        
        # GSC reward system
        self.initial_reward = 50.0  # Starting reward
        self.halving_interval = 4350000000000  # Halving every 4.35 trillion blocks (43,50,00,00,00,000)
        self.max_supply = 21750000000000  # 21.75 trillion GSC
        self.current_supply = 0
        
        # Initialize empty chain first
        self.chain = []
        
        # Create and add genesis block
        genesis_block = self.create_genesis_block()
    
    def get_current_reward(self):
        """Calculate current mining reward based on GSC halving system"""
        # Genesis block (index 0) has no reward, mining rewards start from block 1
        if self.block_height == 0:  # For the first mined block (index 1)
            return self.initial_reward
        
        halving_count = (self.block_height - 1) // self.halving_interval  # Adjust for genesis block
        if halving_count >= 64:  # After 64 halvings, reward becomes 0
            return 0
        return self.initial_reward / (2 ** halving_count)
    
    def create_genesis_block(self):
        print("Creating GSC Coin Genesis Block...")
        print("Genesis block with minimal allocation - only 255 GSC genesis reward")
        
        # Genesis transactions - only genesis reward
        genesis_transactions = []
        
        # Only genesis reward to specified address (255 GSC)
        genesis_reward_tx = Transaction(
            sender="GENESIS",
            receiver="GSC1705641e65321ef23ac5fb3d470f39627",
            amount=255.0,  # Genesis reward amount
            fee=0.0,
            timestamp=1704067200
        )
        genesis_transactions.append(genesis_reward_tx)
        
        genesis_block = Block(
            index=0,
            transactions=genesis_transactions,
            timestamp=1704067200,  # Fixed genesis timestamp (Jan 1, 2024)
            previous_hash="0" * 64,
            nonce=0,
            reward=0.0  # No mining reward for genesis block
        )
        
        # Mine genesis block with minimal difficulty
        genesis_block.mine_block(1, "GENESIS")
        self.chain.append(genesis_block)
        
        # Update balances
        self.update_balances()
        
        self.current_supply = 255.0  # Only genesis reward
        print(f"GSC Coin Genesis Block Created!")
        print(f"Genesis Hash: {genesis_block.hash}")
        print(f"Genesis Address Balance: 255 GSC")
        print(f"Total Genesis Supply: {self.current_supply} GSC")
        print(f"Remaining supply (21.75T - 255) will be created through mining")
        
        return genesis_block
    
    def get_latest_block(self) -> Block:
        """Get the latest block in the chain"""
        return self.chain[-1]

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        for b in self.chain:
            if b.hash == block_hash:
                return b
        return None

    def get_transaction_by_hash(self, tx_id: str):
        """Return (tx, block_height) or None. block_height=-1 means mempool."""
        for height, block in enumerate(self.chain):
            for tx in block.transactions:
                if tx.tx_id == tx_id:
                    return tx, height
        for tx in self.mempool:
            if tx.tx_id == tx_id:
                return tx, -1
        return None
    
    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """Add transaction to mempool with comprehensive GSC protocol validation"""
        try:
            print(f"🔍 Validating transaction for mempool: {transaction.tx_id[:16]}...")
            
            # 1. Basic transaction validation
            if not transaction.is_valid():
                print(f"❌ INVALID TRANSACTION: Basic validation failed")
                return False
            
            # 2. GSC address format validation
            if not self.validate_gsc_address(transaction.sender):
                print(f"❌ INVALID TRANSACTION: Invalid sender address format: {transaction.sender}")
                return False
            
            if not self.validate_gsc_address(transaction.receiver):
                print(f"❌ INVALID TRANSACTION: Invalid receiver address format: {transaction.receiver}")
                return False
            
            # 3. Amount and fee validation
            if transaction.amount <= 0:
                print(f"❌ INVALID TRANSACTION: Invalid amount: {transaction.amount}")
                return False
            
            if transaction.fee < 0:
                print(f"❌ INVALID TRANSACTION: Invalid fee: {transaction.fee}")
                return False
            
            # 4. Check for duplicate transaction ID in entire blockchain
            if self.is_transaction_duplicate(transaction):
                print(f"❌ INVALID TRANSACTION: Duplicate transaction detected in blockchain")
                return False
            
            # 5. Check for duplicate transactions in mempool
            for existing_tx in self.mempool:
                if existing_tx.tx_id == transaction.tx_id:
                    print(f"❌ INVALID TRANSACTION: Duplicate transaction in mempool")
                    return False
                
                # Check for identical transaction content (replay attack)
                if (existing_tx.sender == transaction.sender and 
                    existing_tx.receiver == transaction.receiver and 
                    existing_tx.amount == transaction.amount and 
                    abs(existing_tx.timestamp - transaction.timestamp) < 1.0):
                    print(f"❌ INVALID TRANSACTION: Identical transaction already in mempool")
                    return False
            
            # 6. Balance validation (skip for coinbase transactions)
            if transaction.sender not in ["COINBASE", "GENESIS", "Genesis"]:
                sender_balance = self.get_balance(transaction.sender)
                required_amount = transaction.amount + transaction.fee
                
                if sender_balance < required_amount:
                    print(f"❌ INVALID TRANSACTION: Insufficient balance: {sender_balance} < {required_amount}")
                    return False
            
            # 7. Comprehensive double spending check
            if self.check_double_spending_comprehensive(transaction):
                print(f"❌ INVALID TRANSACTION: Double spending detected")
                return False
            
            # 8. Timestamp validation
            import time
            current_time = time.time()
            
            # Allow transactions from 24 hours ago to 5 minutes in the future
            if (transaction.timestamp > current_time + 300 or 
                transaction.timestamp < current_time - 86400):
                print(f"❌ INVALID TRANSACTION: Invalid timestamp: {transaction.timestamp}")
                return False
            
            # 9. Replay attack prevention - check against all blockchain history
            for block in self.chain:
                for tx in block.transactions:
                    if (tx.sender == transaction.sender and 
                        tx.receiver == transaction.receiver and 
                        tx.amount == transaction.amount and 
                        abs(tx.timestamp - transaction.timestamp) < 1.0):
                        print(f"❌ INVALID TRANSACTION: Replay attack detected - identical transaction found in blockchain")
                        return False
            
            # All validations passed - add to mempool
            self.mempool.append(transaction)
            print(f"✅ Transaction added to mempool successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error validating transaction: {e}")
            return False
    
    def validate_gsc_address(self, address: str) -> bool:
        """Validate GSC address format according to protocol"""
        if not address or not isinstance(address, str):
            return False
        
        # Allow special addresses
        if address in ["COINBASE", "GENESIS", "Genesis"]:
            return True
        
        # GSC address format: GSC1 + 32 hex characters
        if not address.startswith("GSC1"):
            return False
        
        if len(address) != 36:  # GSC1 (4) + 32 hex chars
            return False
        
        # Check if remaining characters are valid hex
        hex_part = address[4:]
        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False
    
    def check_double_spending_comprehensive(self, transaction: Transaction) -> bool:
        """Comprehensive double spending detection"""
        if transaction.sender in ["COINBASE", "GENESIS", "Genesis"]:
            return False  # Special transactions can't double spend
        
        # Check if sender has already spent these funds in blockchain
        sender_spent = 0.0
        sender_received = 0.0
        
        # Calculate actual balance from blockchain
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == transaction.sender and tx.sender not in ["COINBASE", "GENESIS"]:
                    sender_spent += (tx.amount + tx.fee)
                if tx.receiver == transaction.sender:
                    sender_received += tx.amount
        
        # Check pending transactions in mempool
        mempool_spent = 0.0
        for tx in self.mempool:
            if tx.sender == transaction.sender and tx.sender not in ["COINBASE", "GENESIS"]:
                mempool_spent += (tx.amount + tx.fee)
        
        # Calculate available balance
        available_balance = sender_received - sender_spent - mempool_spent
        required_amount = transaction.amount + transaction.fee
        
        if available_balance < required_amount:
            print(f"🚫 Double spending attempt: available={available_balance}, required={required_amount}")
            return True
        
        # Check for identical transaction signatures (replay attack)
        for block in self.chain:
            for tx in block.transactions:
                if (tx.sender == transaction.sender and 
                    tx.receiver == transaction.receiver and 
                    tx.amount == transaction.amount and 
                    tx.timestamp == transaction.timestamp):
                    print(f"🚫 Replay attack detected: identical transaction found")
                    return True
        
        return False
    
    def is_transaction_duplicate(self, transaction: Transaction) -> bool:
        """Check if transaction already exists in blockchain"""
        for block in self.chain:
            for tx in block.transactions:
                if tx.tx_id == transaction.tx_id:
                    return True
                # Also check for identical transaction content
                if (tx.sender == transaction.sender and 
                    tx.receiver == transaction.receiver and 
                    tx.amount == transaction.amount and 
                    abs(tx.timestamp - transaction.timestamp) < 1.0):
                    return True
        return False
    
    def validate_transaction_for_mining(self, transaction: Transaction) -> bool:
        """Validate transaction specifically for mining inclusion"""
        try:
            # 1. Basic transaction validation
            if not transaction.is_valid():
                return False
            
            # 2. GSC address format validation
            if not self.validate_gsc_address(transaction.sender) or not self.validate_gsc_address(transaction.receiver):
                return False
            
            # 3. Amount and fee validation
            if transaction.amount <= 0 or transaction.fee < 0:
                return False
            
            # 4. Balance validation (skip coinbase)
            if transaction.sender not in ["COINBASE", "GENESIS", "Genesis"]:
                sender_balance = self.get_balance(transaction.sender)
                if sender_balance < (transaction.amount + transaction.fee):
                    return False
            
            # 5. Double spending check
            if self.check_double_spending_comprehensive(transaction):
                return False
            
            # 6. Timestamp validation
            import time
            current_time = time.time()
            if (transaction.timestamp > current_time + 300 or 
                transaction.timestamp < current_time - 86400):
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Transaction validation error: {e}")
            return False
    
    def validate_block_before_mining(self, block: Block) -> bool:
        """Validate block structure before mining"""
        try:
            # Check block has transactions
            if not block.transactions:
                return False
            
            # Validate coinbase transaction (first transaction)
            coinbase_tx = block.transactions[0]
            if coinbase_tx.sender != "COINBASE":
                return False
            
            # Validate all other transactions
            for tx in block.transactions[1:]:
                if not self.validate_transaction_for_mining(tx):
                    return False
            
            # Check block index
            if block.index != len(self.chain):
                return False
            
            # Check previous hash
            if block.previous_hash != self.get_latest_block().hash:
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Block pre-mining validation error: {e}")
            return False
    
    def validate_mined_block(self, block: Block) -> bool:
        """Final validation of mined block"""
        try:
            # Check proof of work
            if not block.hash.startswith("0" * self.difficulty):
                return False
            
            # Verify hash calculation
            calculated_hash = block.calculate_hash()
            if calculated_hash != block.hash:
                return False
            
            # Check block integrity
            previous_block = self.get_latest_block()
            if not block.is_valid(previous_block):
                return False
            
            # Validate all transactions again
            for tx in block.transactions:
                if tx.sender != "COINBASE" and not self.validate_transaction_for_mining(tx):
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Mined block validation error: {e}")
            return False
    
    def export_mempool_transactions(self, filepath: str) -> bool:
        """Export mempool transactions to file (Bitcoin-like functionality)"""
        try:
            mempool_data = {
                'version': '1.0',
                'timestamp': time.time(),
                'transaction_count': len(self.mempool),
                'transactions': [tx.to_dict() for tx in self.mempool]
            }
            
            with open(filepath, 'w') as f:
                json.dump(mempool_data, f, indent=2)
            
            print(f"Exported {len(self.mempool)} transactions to {filepath}")
            return True
        except Exception as e:
            print(f"Error exporting mempool: {e}")
            return False
    
    def import_mempool_transactions(self, filepath: str) -> int:
        """Import transactions from file to mempool (Bitcoin-like functionality)"""
        try:
            with open(filepath, 'r') as f:
                mempool_data = json.load(f)
            
            imported_count = 0
            for tx_data in mempool_data.get('transactions', []):
                # Reconstruct transaction object
                tx = Transaction(
                    sender=tx_data['sender'],
                    receiver=tx_data['receiver'],
                    amount=tx_data['amount'],
                    fee=tx_data['fee'],
                    timestamp=tx_data['timestamp'],
                    signature=tx_data.get('signature', ''),
                    tx_id=tx_data.get('tx_id', '')
                )
                
                # Add to mempool if valid and not duplicate
                if self.add_transaction_to_mempool(tx):
                    imported_count += 1
            
            print(f"Imported {imported_count} transactions from {filepath}")
            return imported_count
        except Exception as e:
            print(f"Error importing mempool: {e}")
            return 0
    
    def get_mempool_from_network(self) -> int:
        """Request mempool transactions from network peers (Bitcoin-like)"""
        if not self.network_node:
            print("No network node available")
            return 0
        
        imported_count = 0
        for peer in self.network_node.peers:
            try:
                # Request mempool from peer
                peer_mempool = self.network_node.request_mempool_from_peer(peer)
                if peer_mempool:
                    for tx_data in peer_mempool:
                        tx = Transaction(**tx_data)
                        if self.add_transaction_to_mempool(tx):
                            imported_count += 1
            except Exception as e:
                print(f"Error getting mempool from peer {peer}: {e}")
        
        return imported_count
    
    def is_transaction_valid(self, transaction: Transaction) -> bool:
        """Bitcoin-like transaction validation"""
        # Basic validation
        if not transaction.is_valid():
            return False
            
        # Check for double spending in mempool
        for tx in self.mempool:
            if tx.sender == transaction.sender and tx.tx_id != transaction.tx_id:
                sender_balance = self.get_balance(transaction.sender)
                total_spending = sum(t.amount + t.fee for t in self.mempool if t.sender == transaction.sender)
                total_spending += transaction.amount + transaction.fee
                if total_spending > sender_balance:
                    print(f"Double spending detected: {transaction.tx_id[:16]}...")
                    return False
        
        return True
    
    def export_blockchain(self, filepath: str) -> bool:
        """Export entire blockchain to file (Bitcoin-like functionality)"""
        try:
            blockchain_data = {
                'version': '1.0',
                'timestamp': time.time(),
                'block_count': len(self.chain),
                'total_supply': self.current_supply,
                'difficulty': self.difficulty,
                'blocks': []
            }
            
            for block in self.chain:
                block_data = {
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'previous_hash': block.previous_hash,
                    'hash': block.hash,
                    'merkle_root': block.merkle_root,
                    'nonce': block.nonce,
                    'difficulty': block.difficulty,
                    'miner': block.miner,
                    'reward': block.reward,
                    'transactions': [tx.to_dict() for tx in block.transactions]
                }
                blockchain_data['blocks'].append(block_data)
            
            with open(filepath, 'w') as f:
                json.dump(blockchain_data, f, indent=2)
            
            print(f"Exported blockchain with {len(self.chain)} blocks to {filepath}")
        except Exception as e:
            print(f"Error loading blockchain: {e}")
            return False

    def synchronize_chains(self, current_chain: List[Block], imported_chain: List[Block]) -> List[Block]:
        """Synchronize two blockchain chains chronologically with comprehensive validation"""
        print(f"🔄 Synchronizing chains: Local({len(current_chain)} blocks) vs Imported({len(imported_chain)} blocks)")
        
        # Validate both chains first
        if not self.validate_imported_chain(current_chain):
            print("❌ Current chain is invalid, using imported chain")
            if self.validate_imported_chain(imported_chain):
                return imported_chain
            else:
                print("❌ Both chains are invalid, keeping current")
                return current_chain
        
        if not self.validate_imported_chain(imported_chain):
            print("❌ Imported chain is invalid, keeping current chain")
            return current_chain
        
        # Find common ancestor block (fork point)
        common_ancestor_index = -1
        for i, current_block in enumerate(current_chain):
            for j, imported_block in enumerate(imported_chain):
                if current_block.hash == imported_block.hash:
                    common_ancestor_index = i
                    print(f"📍 Found common ancestor at block {i}: {current_block.hash[:16]}...")
                    break
            if common_ancestor_index >= 0:
                break
        
        if common_ancestor_index == -1:
            # No common ancestor - choose the longer valid chain
            print("⚠️ No common ancestor found")
            if len(imported_chain) > len(current_chain):
                print(f"✅ Using imported chain (longer: {len(imported_chain)} vs {len(current_chain)})")
                return imported_chain
            else:
                print(f"✅ Keeping current chain (longer: {len(current_chain)} vs {len(imported_chain)})")
                return current_chain
        
        # Merge chains chronologically from common ancestor
        base_chain = current_chain[:common_ancestor_index + 1]
        current_fork = current_chain[common_ancestor_index + 1:]
        imported_fork = imported_chain[common_ancestor_index + 1:]
        
        # Combine all blocks after fork point and sort chronologically
        all_fork_blocks = current_fork + imported_fork
        
        # Remove duplicates based on hash
        unique_blocks = []
        seen_hashes = set()
        for block in all_fork_blocks:
            if block.hash not in seen_hashes:
                unique_blocks.append(block)
                seen_hashes.add(block.hash)
        
        # Sort by timestamp for chronological order
        unique_blocks.sort(key=lambda b: b.timestamp)
        
        # Rebuild chain with proper indexing and hash integrity
        synchronized_chain = base_chain.copy()
        for block in unique_blocks:
            # Update block index to maintain sequence
            block.index = len(synchronized_chain)
            # Update previous hash to maintain chain integrity
            if synchronized_chain:
                block.previous_hash = synchronized_chain[-1].hash
            
            # Recalculate hash to maintain integrity
            # We need to satisfy the difficulty requirement of the block
            target = "0" * block.difficulty
            block.hash = block.calculate_hash()
            
            # Simple proof-of-work to find a valid hash for the new index/previous_hash
            while not block.hash.startswith(target):
                block.nonce += 1
                block.hash = block.calculate_hash()
                
            synchronized_chain.append(block)
        
        print(f"✅ Synchronized chain created with {len(synchronized_chain)} blocks")
        print(f"   Base: {len(base_chain)} blocks, Added: {len(unique_blocks)} blocks")
        
        # Final validation of synchronized chain
        if self.validate_imported_chain(synchronized_chain):
            return synchronized_chain
        else:
            print("❌ Synchronized chain validation failed, keeping current chain")
            return current_chain

    def import_blockchain(self, filepath: str) -> bool:
        """Import blockchain from file with chronological synchronization"""
        try:
            with open(filepath, 'r') as f:
                blockchain_data = json.load(f)
            
            # Validate and reconstruct imported blocks
            imported_blocks = []
            for block_data in blockchain_data.get('blocks', []):
                # Reconstruct transactions
                transactions = []
                for tx_data in block_data['transactions']:
                    tx = Transaction(
                        sender=tx_data['sender'],
                        receiver=tx_data['receiver'],
                        amount=tx_data['amount'],
                        fee=tx_data['fee'],
                        timestamp=tx_data['timestamp'],
                        signature=tx_data.get('signature', ''),
                        tx_id=tx_data.get('tx_id', '')
                    )
                    transactions.append(tx)
                
                # Reconstruct block
                block = Block(
                    index=block_data['index'],
                    timestamp=block_data['timestamp'],
                    transactions=transactions,
                    previous_hash=block_data['previous_hash'],
                    nonce=block_data['nonce'],
                    difficulty=block_data['difficulty'],
                    miner=block_data.get('miner', ''),
                    reward=block_data.get('reward', 0.0)
                )
                block.hash = block_data['hash']
                block.merkle_root = block_data['merkle_root']
                imported_blocks.append(block)
            
            # Use synchronize_chains to merge instead of replace
            synchronized_chain = self.synchronize_chains(self.chain, imported_blocks)
            
            if synchronized_chain and (len(synchronized_chain) > len(self.chain) or synchronized_chain != self.chain):
                self.chain = synchronized_chain
                self.update_balances()
                self.block_height = len(self.chain) - 1
                # Update current supply after sync
                self.update_current_supply()
                
                print(f"✅ Successfully imported and synchronized blockchain. New height: {self.block_height}")
                return True
            else:
                print("⚠️ Import did not result in a new/better chain")
                return False
                
        except Exception as e:
            print(f"❌ Error importing blockchain: {e}")
            return False
    
    def validate_imported_chain(self, chain: List[Block]) -> bool:
        """Validate imported blockchain integrity"""
        if not chain:
            return False
        
        # Check genesis block
        if chain[0].index != 0 or chain[0].previous_hash != "0" * 64:
            return False
        
        # Validate each block
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]
            
            # Check block integrity
            if not current_block.is_valid(previous_block):
                return False
            
            # Check hash chain
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def sync_with_network(self) -> bool:
        """Synchronize blockchain with network peers (Bitcoin-like)"""
        if not self.network_node:
            print("No network node available for sync")
            return False
        
        try:
            # Get blockchain from peers
            best_chain = None
            best_height = len(self.chain)
            
            for peer in self.network_node.peers:
                try:
                    peer_chain_info = self.network_node.request_blockchain_info(peer)
                    if peer_chain_info and peer_chain_info['height'] > best_height:
                        peer_chain = self.network_node.request_full_blockchain(peer)
                        if peer_chain and self.validate_imported_chain(peer_chain):
                            best_chain = peer_chain
                            best_height = len(peer_chain)
                except Exception as e:
                    print(f"Error syncing with peer {peer}: {e}")
            
            if best_chain:
                self.chain = best_chain
                self.update_balances()
                self.block_height = len(self.chain) - 1
                print(f"Blockchain synced - new height: {self.block_height}")
                return True
            else:
                print("No better chain found - already up to date")
                return True
                
        except Exception as e:
            print(f"Error during blockchain sync: {e}")
            return False
    
    def create_new_block(self, miner_address: str) -> Block:
        """Create a new block with transactions from mempool"""
        latest_block = self.get_latest_block()
        
        # Select transactions from mempool (up to 10 transactions per block)
        selected_transactions = self.mempool[:10].copy()
        
        # Get current reward based on Bitcoin-like halving
        current_reward = self.get_current_reward()
        
        # Always add coinbase transaction (mining reward) as first transaction
        coinbase_tx = Transaction(
            sender="COINBASE",
            receiver=miner_address,
            amount=current_reward,
            fee=0.0,
            timestamp=time.time()
        )
        
        # Ensure no duplicate coinbase transactions in selected_transactions
        non_coinbase_transactions = [tx for tx in selected_transactions if tx.sender != "COINBASE"]
        
        # Insert coinbase transaction at the beginning
        all_transactions = [coinbase_tx] + non_coinbase_transactions
        
        print(f"🔨 Creating block with 1 coinbase + {len(non_coinbase_transactions)} regular transactions")
        
        new_block = Block(
            index=latest_block.index + 1,
            timestamp=time.time(),
            transactions=all_transactions,
            previous_hash=latest_block.hash,
            difficulty=8,  # Fixed difficulty 8 (range 5-8 as requested)
            reward=current_reward,
            miner=miner_address
        )
        
        return new_block
    
    def mine_pending_transactions(self, miner_address: str, callback=None, force_mine=False):
        """Secure mining with double mining prevention and transaction validation"""
        
        # 1. Prevent double mining - check if already mining
        if self.is_mining:
            print("🚫 Mining already in progress - preventing double mining")
            return None
        
        # 2. Validate miner address
        if not self.validate_gsc_address(miner_address):
            print(f"🚫 Invalid miner address format: {miner_address}")
            return None
        
        # 3. Check authorized mining addresses
        global CURRENT_MINING_ADDRESS
        if miner_address not in AUTHORIZED_MINING_ADDRESSES:
            print(f"🚫 Unauthorized mining address: {miner_address}")
            return None
        
        # 4. Sync mempool with network peers to get latest transactions
        if hasattr(self, 'network_node') and self.network_node and len(self.network_node.peers) > 0:
            try:
                print("🔄 Syncing mempool with network before mining...")
                synced_count = self.get_mempool_from_network()
                if synced_count > 0:
                    print(f"📥 Synced {synced_count} new transactions from network")
            except Exception as e:
                print(f"⚠️ Failed to sync mempool: {e}")
        
        # 5. Require transactions in mempool (no empty blocks)
        if not self.mempool:
            print("🚫 No valid transactions in mempool - cannot mine empty block")
            return None
        
        # 6. Validate all transactions in mempool before mining
        valid_transactions = []
        invalid_count = 0
        
        print(f"🔍 Validating {len(self.mempool)} transactions before mining...")
        for tx in self.mempool:
            if self.validate_transaction_for_mining(tx):
                valid_transactions.append(tx)
            else:
                invalid_count += 1
                print(f"   ❌ INVALID TRANSACTION: Removing from mempool: {tx.tx_id[:16]}...")
                print(f"      Sender: {tx.sender}, Receiver: {tx.receiver}, Amount: {tx.amount}")
        
        # Remove invalid transactions from mempool
        self.mempool = valid_transactions
        
        if invalid_count > 0:
            print(f"🧹 Removed {invalid_count} INVALID TRANSACTIONS from mempool")
            print(f"   Only {len(self.mempool)} valid transactions remain for mining")
        
        if not self.mempool:
            print("🚫 No valid transactions remaining after validation")
            return None
        
        # 7. Set mining flag to prevent concurrent mining
        self.is_mining = True
        
        try:
            print(f"⛏️ Starting secure mining with {len(self.mempool)} validated transactions...")
            
            # Bitcoin-like transaction selection: prioritize high fees
            sorted_transactions = sorted(
                self.mempool, 
                key=lambda tx: (tx.fee, -tx.timestamp),  # High fee first, then newer
                reverse=True
            )
            total_fees = sum(tx.fee for tx in sorted_transactions)
            print(f"💰 Total transaction fees: {total_fees} GSC")
            
            # Create new block with validated transactions
            new_block = self.create_new_block(miner_address)
            self.current_mining_block = new_block  # Store for GUI updates
            
            # Verify block integrity before mining
            if not self.validate_block_before_mining(new_block):
                print("🚫 Block validation failed before mining")
                return None
            
            # Mine the block with Bitcoin-like proof of work
            mining_stats = new_block.mine_block(self.difficulty, miner_address, callback)
            
            # Final validation before adding to chain
            if not self.validate_mined_block(new_block):
                print("🚫 Mined block failed final validation")
                return None
            
            # Add block to chain
            if self.add_block(new_block):
                # Remove mined transactions from mempool
                mined_tx_count = 0
                for tx in new_block.transactions[1:]:  # Skip coinbase transaction
                    if tx in self.mempool:
                        self.mempool.remove(tx)
                        mined_tx_count += 1
                
                print(f"🧹 Removed {mined_tx_count} mined transactions from mempool")
                
                self.mining_stats = mining_stats
                self.block_height = len(self.chain) - 1
                
                # Automatically broadcast new block to all connected peers
                if hasattr(self, 'network_node') and self.network_node:
                    try:
                        print("📡 Broadcasting new block to network...")
                        self.network_node.broadcast_block(new_block)
                        print(f"✅ Block broadcasted to {len(self.network_node.peers)} peers")
                    except Exception as e:
                        print(f"⚠️ Failed to broadcast block: {e}")
                else:
                    print("⚠️ No network node - block only in local chain")
                
                print(f"🎉 Block {new_block.index} successfully mined and added to GSC blockchain!")
                print(f"📊 Block Hash: {new_block.hash}")
                print(f"💎 Mining Reward: {new_block.reward} GSC")
                print(f"🌐 Network Height: {self.block_height}")
                
                return new_block
            else:
                print("❌ Failed to add mined block to chain!")
                return None
        
        finally:
            self.is_mining = False
            if hasattr(self, 'current_mining_block'):
                delattr(self, 'current_mining_block')
    
    def add_block(self, block: Block) -> bool:
        """Add a new block to the chain"""
        previous_block = self.get_latest_block()
        
        if block.is_valid(previous_block):
            self.chain.append(block)
            self.update_balances()
            # Update current supply after adding block
            self.update_current_supply()
            return True
        
        return False
    
    def update_balances(self):
        """Update all account balances and current supply"""
        self.balances.clear()
        total_supply = 0.0
        
        for block in self.chain:
            # Track fees for this block to avoid double counting
            block_fees = 0.0
            
            for tx in block.transactions:
                # Deduct from sender (except for coinbase and genesis)
                if tx.sender not in ["COINBASE", "GENESIS", "Genesis"]:
                    if tx.sender not in self.balances:
                        self.balances[tx.sender] = 0.0
                    self.balances[tx.sender] -= (tx.amount + tx.fee)
                    # Accumulate fees for this block
                    block_fees += tx.fee
                
                # Add to receiver
                if tx.receiver not in self.balances:
                    self.balances[tx.receiver] = 0.0
                self.balances[tx.receiver] += tx.amount
            
            # Add all block fees to authorized mining addresses (avoid double counting)
            if block_fees > 0:
                global CURRENT_MINING_ADDRESS
                fee_recipient = CURRENT_MINING_ADDRESS if CURRENT_MINING_ADDRESS else AUTHORIZED_MINING_ADDRESSES[0]
                if fee_recipient not in self.balances:
                    self.balances[fee_recipient] = 0.0
                self.balances[fee_recipient] += block_fees
    
    def update_current_supply(self):
        """Professional current supply calculation: Sum of all positive balances"""
        try:
            # Professional method: Sum all positive balances (circulating supply)
            total_circulating = 0.0
            
            for address, balance in self.balances.items():
                if balance > 0:
                    total_circulating += balance
            
            self.current_supply = total_circulating
            print(f"📊 Professional blockchain current_supply: {self.current_supply:.2f} GSC")
            print(f"   Method: Sum of all positive account balances")
            
        except Exception as e:
            print(f"Error updating current supply: {e}")

    def add_manual_block(self, miner_address: str) -> Optional[Block]:
        """Manually add a block with a low difficulty for instant inclusion"""
        if self.is_mining:
            print("🚫 Mining already in progress - cannot add manual block")
            return None
            
        try:
            # 1. Check if we have transactions (optional, but good for GSC protocol)
            if not self.mempool:
                print("⚠️ No pending transactions in mempool")
                # We could allow empty blocks, but let's stick to the protocol
            
            # 2. Create a new block with transactions from mempool
            new_block = self.create_new_block(miner_address)
            
            # 3. Use a low difficulty for manual blocks (difficulty 1)
            # This ensures near-instant mining while still creating a valid hash
            print(f"🛠️ Adding manual block {new_block.index} with instant mining...")
            mining_stats = new_block.mine_block(1, miner_address)
            
            # 4. Add to chain
            if self.add_block(new_block):
                # Remove mined transactions from mempool
                mined_count = 0
                for tx in new_block.transactions[1:]: # Skip coinbase
                    if tx in self.mempool:
                        self.mempool.remove(tx)
                        mined_count += 1
                
                print(f"✅ Manual block {new_block.index} added successfully with {mined_count} transactions!")
                self.block_height = len(self.chain) - 1
                return new_block
            return None
        except Exception as e:
            print(f"❌ Error adding manual block: {e}")
            return None
    
    def get_balance(self, address: str) -> float:
        """Get balance for an address"""
        return self.balances.get(address, 0.0)
    
    def is_chain_valid(self) -> bool:
        """Bitcoin-like blockchain validation with invalid block removal"""
        if len(self.chain) == 0:
            return False
        
        # Validate genesis block
        genesis = self.chain[0]
        if genesis.index != 0 or genesis.previous_hash != "0" * 64:
            print("Invalid genesis block")
            return False
        
        # Validate each block in sequence and remove invalid ones
        valid_chain = [self.chain[0]]  # Keep genesis block
        removed_blocks = 0
        
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = valid_chain[-1]  # Use last valid block as previous
            
            # Bitcoin-like validation checks
            if self.validate_block_bitcoin_style(current_block, previous_block):
                valid_chain.append(current_block)
            else:
                print(f"❌ INVALID BLOCK: Removing block {i} from chain")
                print(f"   Block hash: {current_block.hash[:16]}...")
                print(f"   Block contains {len(current_block.transactions)} transactions")
                removed_blocks += 1
                
                # Add transactions back to mempool if they're still valid
                for tx in current_block.transactions:
                    if tx.sender != "COINBASE" and self.validate_transaction_for_mining(tx):
                        if tx not in self.mempool:
                            self.mempool.append(tx)
                            print(f"   ↩️ Returned transaction {tx.tx_id[:16]}... to mempool")
        
        # Update chain if invalid blocks were removed
        if removed_blocks > 0:
            print(f"🧹 Removed {removed_blocks} INVALID BLOCKS from blockchain")
            self.chain = valid_chain
            self.block_height = len(self.chain) - 1
            print(f"   New blockchain height: {self.block_height}")
        
        # Validate balances consistency
        if not self.validate_balances():
            print("Balance validation failed")
            return False
        
        print("Blockchain validation passed - Bitcoin-like standards met")
        return True
    
    def is_chain_valid_network(self, chain) -> bool:
        """Validate a chain received from network"""
        if len(chain) == 0:
            return False
        
        # Validate genesis block
        genesis = chain[0]
        if genesis.index != 0 or genesis.previous_hash != "0" * 64:
            return False
        
        # Validate each block in sequence
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            
            if not current_block.is_valid(previous_block):
                return False
        
        return True

    def find_common_ancestor(self, peer_hashes):
        """Find the most recent common block hash with a peer"""
        # Iterate backwards through our chain
        for i in range(len(self.chain) - 1, -1, -1):
            block_hash = self.chain[i].hash
            if block_hash in peer_hashes:
                return self.chain[i]
        return None

    def get_block_headers(self, start_hash, limit=2000):
        """Get block headers starting after a specific hash"""
        headers = []
        start_index = -1
        
        # If start_hash is all zeros (genesis request), start from beginning
        if start_hash == "0" * 64:
             start_index = 0
        else:
            # Find start block
            for i, block in enumerate(self.chain):
                if block.hash == start_hash:
                    start_index = i + 1
                    break
        
        if start_index != -1:
            end_index = min(start_index + limit, len(self.chain))
            for i in range(start_index, end_index):
                headers.append(self.chain[i].get_header())
                
        return headers
    
    def replace_chain_if_longer(self, new_chain):
        """Replace current chain if new chain is longer and valid"""
        if len(new_chain) > len(self.chain) and self.is_chain_valid_network(new_chain):
            print(f"Replacing chain with longer valid chain ({len(new_chain)} blocks)")
            self.chain = new_chain
            self.update_balances()
            self.block_height = len(self.chain) - 1 if self.chain else 0
            return True
        return False
    
    def set_network_node(self, network_node):
        """Set network node for P2P communication"""
        self.network_node = network_node
    
    def broadcast_new_block(self, block):
        """Broadcast new block to network"""
        if self.network_node:
            self.network_node.broadcast_block(block)
    
    def broadcast_new_transaction(self, transaction):
        """Broadcast new transaction to network"""
        if self.network_node:
            self.network_node.broadcast_transaction(transaction)
    
    def is_block_valid(self, block, previous_block):
        """Check if a single block is valid"""
        return block.is_valid(previous_block)
    
    def validate_block_bitcoin_style(self, block: Block, previous_block: Block) -> bool:
        """Bitcoin-style block validation"""
        
        # 1. Check block index sequence
        if block.index != previous_block.index + 1:
            print(f"Invalid block index: {block.index}, expected: {previous_block.index + 1}")
            return False
        
        # 2. Check previous hash linkage
        if block.previous_hash != previous_block.hash:
            print(f"Invalid previous hash linkage")
            return False
        
        # 3. Check block hash integrity
        if block.hash != block.calculate_hash():
            print(f"Block hash integrity check failed")
            return False
        
        # 4. Check proof of work (difficulty requirement)
        if not block.hash.startswith("0" * self.difficulty):
            print(f"Proof of work validation failed - difficulty {self.difficulty}")
            return False
        
        # 5. Check merkle root
        if block.merkle_root != block.calculate_merkle_root():
            print(f"Merkle root validation failed")
            return False
        
        # 6. Validate all transactions in block
        for i, tx in enumerate(block.transactions):
            if not self.validate_transaction_bitcoin_style(tx, block, i):
                print(f"Transaction {i} validation failed")
                return False
        
        # 7. Check coinbase transaction (first transaction must be coinbase)
        if len(block.transactions) > 0:
            coinbase = block.transactions[0]
            if coinbase.sender != "COINBASE":
                print("First transaction must be coinbase")
                return False
            
            # Check mining reward amount
            expected_reward = self.get_current_reward()
            if coinbase.amount != expected_reward:
                print(f"Invalid mining reward: {coinbase.amount}, expected: {expected_reward}")
                return False
            
            # Ensure only ONE coinbase transaction per block
            coinbase_count = sum(1 for tx in block.transactions if tx.sender == "COINBASE")
            if coinbase_count != 1:
                print(f"Invalid coinbase count: {coinbase_count}, must be exactly 1")
                return False
        
        # 8. Check timestamp (must be greater than previous block)
        if block.timestamp <= previous_block.timestamp:
            print("Block timestamp must be greater than previous block")
            return False
        
        return True
    
    def validate_transaction_bitcoin_style(self, tx: Transaction, block: Block, tx_index: int) -> bool:
        """Bitcoin-style transaction validation"""
        
        # Skip coinbase transaction validation (different rules)
        if tx.sender == "COINBASE":
            return True
        
        # 1. Check transaction hash integrity
        if tx.tx_id != tx.calculate_hash():
            print(f"Transaction hash integrity failed")
            return False
        
        # 2. Check basic transaction validity
        if not tx.is_valid():
            print(f"Basic transaction validation failed")
            return False
        
        # 3. Check sender has sufficient balance (at time of transaction)
        sender_balance = self.get_balance_at_block(tx.sender, block.index - 1)
        if sender_balance < (tx.amount + tx.fee):
            print(f"Insufficient balance: {sender_balance} < {tx.amount + tx.fee}")
            return False
        
        # 4. Check for double spending
        if self.check_double_spending(tx, block.index):
            print(f"Double spending detected")
            return False
        
        return True
    
    def validate_balances(self) -> bool:
        """Validate that all balances are consistent with blockchain history"""
        calculated_balances = {}
        
        # Recalculate balances from scratch
        for block in self.chain:
            for tx in block.transactions:
                # Handle coinbase transactions
                if tx.sender == "COINBASE":
                    if tx.receiver not in calculated_balances:
                        calculated_balances[tx.receiver] = 0.0
                    calculated_balances[tx.receiver] += tx.amount
                
                # Handle genesis transactions
                elif tx.sender == "Genesis":
                    if tx.receiver not in calculated_balances:
                        calculated_balances[tx.receiver] = 0.0
                    calculated_balances[tx.receiver] += tx.amount
                
                # Handle regular transactions
                else:
                    # Deduct from sender
                    if tx.sender not in calculated_balances:
                        calculated_balances[tx.sender] = 0.0
                    calculated_balances[tx.sender] -= (tx.amount + tx.fee)
                    
                    # Add to receiver
                    if tx.receiver not in calculated_balances:
                        calculated_balances[tx.receiver] = 0.0
                    calculated_balances[tx.receiver] += tx.amount
                    
                    # Add fee to current mining address
                    global CURRENT_MINING_ADDRESS
                    fee_recipient = CURRENT_MINING_ADDRESS if CURRENT_MINING_ADDRESS else AUTHORIZED_MINING_ADDRESSES[0]
                    if fee_recipient not in calculated_balances:
                        calculated_balances[fee_recipient] = 0.0
                    calculated_balances[fee_recipient] += tx.fee
        
        # Compare with current balances and update if needed
        for address, balance in calculated_balances.items():
            if abs(self.balances.get(address, 0.0) - balance) > 0.00000001:  # Allow for floating point precision
                print(f"Balance mismatch for {address}: stored={self.balances.get(address, 0.0)}, calculated={balance}")
                # Update the stored balance to match calculated balance
                self.balances[address] = balance
        
        # Also ensure all calculated balances are in the stored balances
        self.balances = calculated_balances.copy()
        
        return True
    
    def get_balance_at_block(self, address: str, block_index: int) -> float:
        """Get balance of address at specific block height"""
        balance = 0.0
        
        for i in range(min(block_index + 1, len(self.chain))):
            block = self.chain[i]
            for tx in block.transactions:
                if tx.sender == address and tx.sender not in ["COINBASE", "Genesis"]:
                    balance -= (tx.amount + tx.fee)
                if tx.receiver == address:
                    balance += tx.amount
                if address in AUTHORIZED_MINING_ADDRESSES and tx.sender not in ["COINBASE", "Genesis"]:
                    balance += tx.fee
        
        return balance
    
    def check_double_spending(self, transaction: Transaction, current_block_index: int) -> bool:
        """Check if transaction represents double spending"""
        # Look for identical transactions in previous blocks
        for i in range(current_block_index):
            if i < len(self.chain):
                block = self.chain[i]
                for tx in block.transactions:
                    if (tx.sender == transaction.sender and 
                        tx.receiver == transaction.receiver and 
                        tx.amount == transaction.amount and
                        tx.timestamp == transaction.timestamp):
                        return True
        return False
    
    def get_blockchain_info(self) -> dict:
        """Get blockchain information"""
        return {
            'blocks': len(self.chain),
            'difficulty': self.difficulty,
            'mempool_size': len(self.mempool),
            'total_addresses': len(self.balances),
            'is_mining': self.is_mining,
            'latest_block_hash': self.get_latest_block().hash,
            'chain_valid': self.is_chain_valid()
        }
    
    def save_blockchain(self, filename: str):
        """Save blockchain to file"""
        blockchain_data = {
            'chain': [block.to_dict() for block in self.chain],
            'mempool': [tx.to_dict() for tx in self.mempool],
            'balances': self.balances,
            'difficulty': self.difficulty,
            'mining_reward': self.mining_reward
        }
        
        with open(filename, 'w') as f:
            json.dump(blockchain_data, f, indent=2)
        
        print(f"GSC Blockchain saved to {filename}")
    
    def load_blockchain(self, filename: str):
        """Load blockchain from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Reconstruct blockchain
            self.chain.clear()
            for block_data in data['chain']:
                transactions = [
                    Transaction(**tx_data) for tx_data in block_data['transactions']
                ]
                block = Block(
                    index=block_data['index'],
                    timestamp=block_data['timestamp'],
                    transactions=transactions,
                    previous_hash=block_data['previous_hash'],
                    nonce=block_data['nonce'],
                    hash=block_data['hash'],
                    merkle_root=block_data['merkle_root'],
                    difficulty=block_data['difficulty'],
                    miner=block_data['miner'],
                    reward=block_data['reward']
                )
                self.chain.append(block)
            
            # Reconstruct mempool
            self.mempool = [Transaction(**tx_data) for tx_data in data['mempool']]
            
            # Restore other data
            self.balances = data['balances']
            self.difficulty = data['difficulty']
            self.mining_reward = data.get('mining_reward', 50.0)

            # Update blockchain state
            self.block_height = len(self.chain) - 1
            self.update_balances()
            # Update current supply after loading
            self.update_current_supply()
            
            print(f"GSC Blockchain loaded from {filename}")
            return True
        except FileNotFoundError:
            print(f"No existing blockchain file found. Starting fresh.")
        except Exception as e:
            print(f"Error loading blockchain: {e}")
            self.create_genesis_block()

# Example usage and testing
if __name__ == "__main__":
    # Create GSC blockchain
    gsc = GSCBlockchain()
    
    print("=== GSC Coin Blockchain Started ===")
    print(f"Genesis block created with hash: {gsc.chain[0].hash}")
    print(f"GSC Foundation balance: {gsc.get_balance('GSC_FOUNDATION')}")
    
    # Create some test transactions
    tx1 = Transaction("GSC_FOUNDATION", "Alice", 100.0, 1.0, time.time())
    tx2 = Transaction("GSC_FOUNDATION", "Bob", 200.0, 2.0, time.time())
    
    # Add to mempool
    gsc.add_transaction_to_mempool(tx1)
    gsc.add_transaction_to_mempool(tx2)
    
    print(f"\nMempool size: {len(gsc.mempool)}")
    
    # Mine a block
    print("\n=== Mining Block 1 ===")
    mined_block = gsc.mine_pending_transactions("Miner1")
    
    if mined_block:
        print(f"Block 1 mined successfully!")
        print(f"Block hash: {mined_block.hash}")
        print(f"Nonce: {mined_block.nonce}")
        print(f"Transactions in block: {len(mined_block.transactions)}")
        
        # Check balances
        print(f"\nUpdated Balances:")
        for address, balance in gsc.balances.items():
            print(f"{address}: {balance} GSC")
    
    # Blockchain info
    print(f"\n=== GSC Blockchain Info ===")
    info = gsc.get_blockchain_info()
    for key, value in info.items():
        print(f"{key}: {value}")
