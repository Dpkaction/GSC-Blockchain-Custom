"""
GSC Coin Blockchain Core - Improved Implementation
Bitcoin-compatible blockchain with thread safety, proper validation, and comprehensive logging
"""

import hashlib
import json
import time
import os
import threading
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
import pickle

from gsc_logger import blockchain_logger
from thread_safety import ThreadSafeList, ThreadSafeDict, AtomicCounter, ThreadSafeSet

@dataclass
class Transaction:
    """GSC Coin Transaction Class - Bitcoin-style transaction"""
    sender: str
    receiver: str
    amount: float
    fee: float
    timestamp: float
    signature: str = ""
    tx_id: str = ""
    extra_data: str = ""  # For BIP-34 coinbase height
    
    def __post_init__(self):
        if not self.tx_id:
            self.tx_id = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate transaction hash"""
        tx_string = f"{self.sender}{self.receiver}{self.amount}{self.fee}{self.timestamp}{self.extra_data}"
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary"""
        return asdict(self)
    
    def is_valid(self) -> bool:
        """Validate transaction with Bitcoin-style checks"""
        if self.amount <= 0:
            blockchain_logger.warning(f"Invalid transaction amount: {self.amount}")
            return False
        if self.fee < 0:
            blockchain_logger.warning(f"Invalid transaction fee: {self.fee}")
            return False
        if self.sender == self.receiver:
            blockchain_logger.warning("Transaction sender and receiver are the same")
            return False
        if self.tx_id != self.calculate_hash():
            blockchain_logger.warning("Transaction ID mismatch")
            return False
        return True
    
    def is_coinbase(self) -> bool:
        """Check if this is a coinbase transaction"""
        return self.sender in ["COINBASE", "GENESIS"]

@dataclass
class Block:
    """GSC Coin Block Class - Bitcoin-style block"""
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
        """Mine the block with proof of work"""
        target = "0" * difficulty
        mining_stats = {
            'start_time': time.time(),
            'nonce': 0,
            'hash_rate': 0,
            'found': False
        }
        
        self.difficulty = difficulty
        self.miner = miner_address
        
        # Add coinbase transaction with BIP-34 height
        coinbase_tx = Transaction(
            sender="COINBASE",
            receiver=miner_address,
            amount=self.reward,
            fee=0.0,
            timestamp=time.time(),
            extra_data=str(self.index)  # BIP-34: block height in coinbase
        )
        self.transactions.insert(0, coinbase_tx)
        self.merkle_root = self.calculate_merkle_root()
        
        blockchain_logger.info(f"Mining block {self.index} with difficulty {difficulty}")
        
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
        
        blockchain_logger.info(f"Block {self.index} mined! Hash: {self.hash}")
        blockchain_logger.debug(f"Mining stats: {mining_stats}")
        
        return mining_stats
    
    def is_valid(self, previous_block=None) -> bool:
        """Validate block with Bitcoin-style checks"""
        # Check hash
        if self.hash != self.calculate_hash():
            blockchain_logger.error("Block hash mismatch")
            return False
        
        # Check previous hash
        if previous_block and self.previous_hash != previous_block.hash:
            blockchain_logger.error(f"Previous hash mismatch: expected {previous_block.hash}, got {self.previous_hash}")
            return False
        
        # Check merkle root
        if self.merkle_root != self.calculate_merkle_root():
            blockchain_logger.error("Merkle root mismatch")
            return False
        
        # Check proof of work
        if not self.hash.startswith("0" * self.difficulty):
            blockchain_logger.error(f"Invalid proof of work: hash {self.hash} doesn't start with {'0' * self.difficulty}")
            return False
        
        # BIP-34: Check coinbase transaction contains block height
        if self.transactions:
            coinbase = self.transactions[0]
            if coinbase.is_coinbase():
                if str(self.index) not in coinbase.extra_data:
                    blockchain_logger.error(f"BIP-34 violation: block height {self.index} not found in coinbase")
                    return False
        
        # Validate all transactions
        for i, tx in enumerate(self.transactions):
            if not tx.is_valid():
                blockchain_logger.error(f"Invalid transaction {i} in block {self.index}")
                return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert block to dictionary"""
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
        """Get block header (block without full transactions)"""
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
    """GSC Coin Blockchain Implementation - Thread-safe and Bitcoin-compatible"""
    
    def __init__(self):
        # Thread-safe data structures
        self.mempool = ThreadSafeList()
        self.orphans = ThreadSafeList()
        self.balances = ThreadSafeDict()
        
        # Threading locks
        self.chain_lock = threading.RLock()
        self.mempool_lock = threading.RLock()
        self.orphans_lock = threading.RLock()
        
        # Blockchain configuration
        self.difficulty = 4
        self.difficulty_locked = True
        self.mining_reward = 50.0
        self.is_mining = False
        self.mining_stats = {}
        self.network_node = None
        self.block_height = AtomicCounter(0)
        
        # Bitcoin-like reward system
        self.initial_reward = 50.0
        self.halving_interval = 210000
        self.max_supply = 21750000000000  # 21.75 trillion GSC
        self.current_supply = 0
        
        # Initialize chain
        self.chain: List[Block] = []
        
        # Load existing blockchain or create genesis
        self.load_blockchain()
        if not self.chain:
            self.create_genesis_block()
        
        blockchain_logger.info(f"GSC Blockchain initialized with {len(self.chain)} blocks")
    
    def get_blockchain_file_path(self) -> str:
        """Get standardized blockchain file path"""
        return "gsc_blockchain.json"
    
    def get_latest_block(self) -> Optional[Block]:
        """Get the latest block in the chain - thread-safe"""
        with self.chain_lock:
            return self.chain[-1] if self.chain else None
    
    def get_current_reward(self) -> float:
        """Calculate current mining reward based on Bitcoin-like halving"""
        current_height = self.block_height.get()
        halvings = current_height // self.halving_interval
        if halvings >= 64:  # After 64 halvings, reward becomes 0
            return 0
        return self.initial_reward / (2 ** halvings)
    
    def create_genesis_block(self) -> Block:
        """Create genesis block with foundation allocation"""
        blockchain_logger.info("Creating GSC Coin Genesis Block")
        blockchain_logger.info(f"Total Supply: {self.max_supply:,.0f} GSC (21.75 Trillion)")
        
        # Genesis block with foundation allocation
        genesis_transactions = [
            Transaction(
                sender="Genesis",
                receiver="GSC_FOUNDATION_RESERVE",
                amount=self.max_supply,
                fee=0,
                timestamp=1704067200,  # Fixed genesis timestamp (Jan 1, 2024)
                extra_data="0"  # BIP-34: genesis block height
            )
        ]
        
        genesis_block = Block(
            index=0,
            transactions=genesis_transactions,
            timestamp=1704067200,
            previous_hash="0" * 64,
            nonce=0,
            reward=0  # Genesis has no reward
        )
        
        # Mine genesis block
        genesis_block.mine_block(1, "GSC_FOUNDATION")
        
        with self.chain_lock:
            self.chain.append(genesis_block)
        
        self.update_balances()
        self.block_height.set(0)
        self.current_supply = self.max_supply
        
        blockchain_logger.info(f"Genesis Block Created: {genesis_block.hash}")
        blockchain_logger.info(f"Foundation Reserve: GSC_FOUNDATION_RESERVE")
        
        self.save_blockchain()
        return genesis_block
    
    def validate_block_bitcoin_style(self, block: Block, previous_block: Block) -> bool:
        """Comprehensive Bitcoin-style block validation"""
        try:
            # Basic block validation
            if not block.is_valid(previous_block):
                return False
            
            # Check block index continuity
            if block.index != previous_block.index + 1:
                blockchain_logger.error(f"Block index discontinuity: expected {previous_block.index + 1}, got {block.index}")
                return False
            
            # Check timestamp is reasonable (not too far in future/past)
            current_time = time.time()
            if block.timestamp > current_time + 7200:  # 2 hours future tolerance
                blockchain_logger.error("Block timestamp too far in future")
                return False
            
            if block.timestamp < previous_block.timestamp - 86400:  # 1 day past tolerance
                blockchain_logger.error("Block timestamp too far in past")
                return False
            
            # Validate reward matches expected
            expected_reward = self.get_current_reward()
            if block.reward != expected_reward:
                blockchain_logger.error(f"Invalid block reward: expected {expected_reward}, got {block.reward}")
                return False
            
            # Check transaction limits
            if len(block.transactions) > 1000:  # Bitcoin-like block size limit
                blockchain_logger.error(f"Too many transactions in block: {len(block.transactions)}")
                return False
            
            # Validate all transactions
            total_fees = 0.0
            for i, tx in enumerate(block.transactions):
                if not tx.is_valid():
                    return False
                
                # Coinbase validation
                if i == 0 and tx.is_coinbase():
                    if tx.amount != block.reward:
                        blockchain_logger.error(f"Coinbase amount mismatch: expected {block.reward}, got {tx.amount}")
                        return False
                elif i > 0 and tx.is_coinbase():
                    blockchain_logger.error("Multiple coinbase transactions in block")
                    return False
                
                # Fee calculation for non-coinbase transactions
                if not tx.is_coinbase():
                    total_fees += tx.fee
            
            # Verify miner receives correct amount (reward + fees)
            if block.transactions:
                coinbase = block.transactions[0]
                expected_coinbase = block.reward + total_fees
                if coinbase.amount != expected_coinbase:
                    blockchain_logger.error(f"Coinbase total incorrect: expected {expected_coinbase}, got {coinbase.amount}")
                    return False
            
            return True
            
        except Exception as e:
            blockchain_logger.error(f"Block validation error: {e}")
            return False
    
    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """Add transaction to mempool with comprehensive validation"""
        with self.mempool_lock:
            # Check transaction validity
            if not self.is_transaction_valid(transaction):
                return False
            
            # Check for duplicate transaction
            if any(tx.tx_id == transaction.tx_id for tx in self.mempool):
                blockchain_logger.debug(f"Transaction already in mempool: {transaction.tx_id[:16]}...")
                return False
            
            # Check sender balance
            sender_balance = self.get_balance(transaction.sender)
            total_cost = transaction.amount + transaction.fee
            
            if sender_balance < total_cost:
                blockchain_logger.warning(f"Insufficient balance: need {total_cost}, have {sender_balance}")
                return False
            
            # Add to mempool
            self.mempool.append(transaction)
            blockchain_logger.info(f"Transaction added to mempool: {transaction.tx_id[:16]}...")
            
            # Broadcast to network
            if self.network_node:
                self.broadcast_new_transaction(transaction)
            
            return True
    
    def is_transaction_valid(self, transaction: Transaction) -> bool:
        """Bitcoin-like transaction validation"""
        # Basic validation
        if not transaction.is_valid():
            return False
        
        # Check for double spending in mempool
        with self.mempool_lock:
            sender_spending = 0.0
            for tx in self.mempool:
                if tx.sender == transaction.sender:
                    sender_spending += tx.amount + tx.fee
            
            sender_balance = self.get_balance(transaction.sender)
            if sender_balance < (sender_spending + transaction.amount + transaction.fee):
                blockchain_logger.warning(f"Double spending detected for {transaction.sender}")
                return False
        
        return True
    
    def is_tx_known(self, tx_id: str) -> bool:
        """Check if transaction is known (in chain or mempool)"""
        # Check mempool
        with self.mempool_lock:
            if any(tx.tx_id == tx_id for tx in self.mempool):
                return True
        
        # Check chain
        with self.chain_lock:
            for block in self.chain:
                for tx in block.transactions:
                    if tx.tx_id == tx_id:
                        return True
        
        return False
    
    def get_transaction_by_hash(self, tx_id: str) -> Optional[Tuple[Transaction, int]]:
        """Get transaction by hash and return (transaction, block_height)"""
        # Check mempool first
        with self.mempool_lock:
            for tx in self.mempool:
                if tx.tx_id == tx_id:
                    return tx, -1  # -1 indicates mempool
        
        # Check chain
        with self.chain_lock:
            for block in self.chain:
                for tx in block.transactions:
                    if tx.tx_id == tx_id:
                        return tx, block.index
        
        return None
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Get block by hash"""
        with self.chain_lock:
            for block in self.chain:
                if block.hash == block_hash:
                    return block
        return None
    
    def create_new_block(self, miner_address: str) -> Block:
        """Create a new block with transactions from mempool"""
        latest_block = self.get_latest_block()
        if not latest_block:
            raise Exception("No latest block found")
        
        # Select transactions from mempool (prioritize by fee)
        with self.mempool_lock:
            mempool_copy = self.mempool.copy()
            # Sort by fee rate (fee/amount) for optimal mining
            mempool_copy.sort(key=lambda tx: tx.fee / max(tx.amount, 0.00000001), reverse=True)
            selected_transactions = mempool_copy[:1000].copy()  # Limit to 1000 transactions
        
        current_reward = self.get_current_reward()
        
        new_block = Block(
            index=latest_block.index + 1,
            timestamp=time.time(),
            transactions=selected_transactions,
            previous_hash=latest_block.hash,
            difficulty=self.difficulty,
            reward=current_reward
        )
        
        return new_block
    
    def mine_pending_transactions(self, miner_address: str, callback=None) -> Optional[Block]:
        """Mine pending transactions with Bitcoin-like process"""
        if self.is_mining:
            blockchain_logger.warning("Mining already in progress")
            return None
        
        self.is_mining = True
        
        try:
            new_block = self.create_new_block(miner_address)
            
            # Mine the block
            mining_stats = new_block.mine_block(self.difficulty, miner_address, callback)
            
            # Add block to chain
            if self.add_block(new_block):
                # Remove mined transactions from mempool
                with self.mempool_lock:
                    for tx in new_block.transactions[1:]:  # Skip coinbase
                        self.mempool.remove(tx)
                
                self.mining_stats = mining_stats
                self.block_height.set(new_block.index)
                
                # Broadcast new block
                if self.network_node:
                    self.broadcast_new_block(new_block)
                
                blockchain_logger.info(f"Block {new_block.index} successfully mined and added")
                return new_block
            else:
                blockchain_logger.error("Failed to add mined block to chain")
                return None
        
        except Exception as e:
            blockchain_logger.error(f"Mining error: {e}")
            return None
        finally:
            self.is_mining = False
    
    def add_block(self, block: Block) -> bool:
        """Add a new block to the chain with full validation"""
        with self.chain_lock:
            if not self.chain:
                # First block must be genesis
                if block.index != 0:
                    blockchain_logger.error("First block must be genesis (index 0)")
                    return False
            else:
                previous_block = self.get_latest_block()
                if not self.validate_block_bitcoin_style(block, previous_block):
                    return False
            
            # Add block
            self.chain.append(block)
            self.block_height.set(block.index)
            
            # Update balances
            self.update_balances()
            
            # Save to disk
            self.save_blockchain()
            
            blockchain_logger.info(f"Block {block.index} added to chain")
            return True
    
    def update_balances(self) -> None:
        """Recalculate all account balances from scratch"""
        self.balances.clear()
        
        with self.chain_lock:
            for block in self.chain:
                for tx in block.transactions:
                    # Deduct from sender (except for coinbase and genesis)
                    if not tx.is_coinbase():
                        current_balance = self.balances.get(tx.sender, 0.0)
                        self.balances.set(tx.sender, current_balance - (tx.amount + tx.fee))
                    
                    # Add to receiver
                    current_balance = self.balances.get(tx.receiver, 0.0)
                    self.balances.set(tx.receiver, current_balance + tx.amount)
                    
                    # Add fee to miner
                    if not tx.is_coinbase() and block.miner:
                        current_balance = self.balances.get(block.miner, 0.0)
                        self.balances.set(block.miner, current_balance + tx.fee)
        
        blockchain_logger.debug("Balances updated")
    
    def get_balance(self, address: str) -> float:
        """Get balance for an address"""
        return self.balances.get(address, 0.0)
    
    def prune_orphans(self, max_orphans: int = 100) -> None:
        """Prune orphan pool to prevent memory bloat"""
        with self.orphans_lock:
            if len(self.orphans) > max_orphans:
                # Remove oldest orphans
                excess = len(self.orphans) - max_orphans
                for _ in range(excess):
                    if self.orphans:
                        self.orphans.pop(0)
                blockchain_logger.info(f"Pruned {excess} orphan blocks")
    
    def save_blockchain(self) -> None:
        """Save blockchain to file"""
        try:
            file_path = self.get_blockchain_file_path()
            chain_data = {
                'chain': [block.to_dict() for block in self.chain],
                'block_height': self.block_height.get(),
                'current_supply': self.current_supply,
                'saved_at': time.time()
            }
            
            with open(file_path, 'w') as f:
                json.dump(chain_data, f, indent=2)
            
            blockchain_logger.debug(f"Blockchain saved to {file_path}")
            
        except Exception as e:
            blockchain_logger.error(f"Failed to save blockchain: {e}")
    
    def load_blockchain(self) -> bool:
        """Load blockchain from file"""
        try:
            file_path = self.get_blockchain_file_path()
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r') as f:
                chain_data = json.load(f)
            
            # Reconstruct blocks
            self.chain = []
            for block_data in chain_data['chain']:
                transactions = []
                for tx_data in block_data['transactions']:
                    tx = Transaction(**tx_data)
                    transactions.append(tx)
                
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
            
            self.block_height.set(chain_data.get('block_height', len(self.chain) - 1))
            self.current_supply = chain_data.get('current_supply', 0)
            
            # Update balances
            self.update_balances()
            
            blockchain_logger.info(f"Blockchain loaded: {len(self.chain)} blocks")
            return True
            
        except Exception as e:
            blockchain_logger.error(f"Failed to load blockchain: {e}")
            return False
    
    def set_network_node(self, network_node) -> None:
        """Set network node for broadcasting"""
        self.network_node = network_node
    
    def broadcast_new_transaction(self, transaction: Transaction) -> None:
        """Broadcast new transaction to network"""
        if self.network_node:
            self.network_node.broadcast_transaction(transaction)
    
    def broadcast_new_block(self, block: Block) -> None:
        """Broadcast new block to network"""
        if self.network_node:
            self.network_node.broadcast_block(block)
    
    def get_block_headers(self, start_hash: str, limit: int = 2000) -> List[dict]:
        """Get block headers starting after a specific hash"""
        headers = []
        start_index = -1
        
        with self.chain_lock:
            # Find start index
            if start_hash == "0" * 64:
                start_index = 0
            else:
                for i, block in enumerate(self.chain):
                    if block.hash == start_hash:
                        start_index = i + 1
                        break
            
            if start_index != -1:
                end_index = min(start_index + limit, len(self.chain))
                for i in range(start_index, end_index):
                    headers.append(self.chain[i].get_header())
        
        return headers
    
    def is_chain_valid(self) -> bool:
        """Validate entire blockchain"""
        with self.chain_lock:
            if not self.chain:
                return False
            
            # Validate genesis
            genesis = self.chain[0]
            if genesis.index != 0 or genesis.previous_hash != "0" * 64:
                blockchain_logger.error("Invalid genesis block")
                return False
            
            # Validate each block
            for i in range(1, len(self.chain)):
                current = self.chain[i]
                previous = self.chain[i - 1]
                
                if not self.validate_block_bitcoin_style(current, previous):
                    blockchain_logger.error(f"Block {i} failed validation")
                    return False
            
            # Validate balances
            test_balances = {}
            for block in self.chain:
                for tx in block.transactions:
                    if not tx.is_coinbase():
                        test_balances[tx.sender] = test_balances.get(tx.sender, 0.0) - (tx.amount + tx.fee)
                    test_balances[tx.receiver] = test_balances.get(tx.receiver, 0.0) + tx.amount
            
            blockchain_logger.info("Blockchain validation passed")
            return True
