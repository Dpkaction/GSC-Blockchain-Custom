"""
GSC Coin Mainnet Blockchain Implementation
Production-ready blockchain with enhanced security and performance
"""

import hashlib
import json
import time
import threading
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import os
import pickle
from .config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(Config.get_data_dir(), Config.LOG_DIR, 'mainnet.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MainnetTransaction:
    """Production-ready transaction class with enhanced validation"""
    sender: str
    receiver: str
    amount: float
    fee: float
    timestamp: float
    signature: str = ""
    tx_id: str = ""
    version: int = 1
    lock_time: int = 0
    
    def __post_init__(self):
        if not self.tx_id:
            self.tx_id = self.calculate_hash()
        if not self.timestamp:
            self.timestamp = time.time()
    
    def calculate_hash(self) -> str:
        """Calculate transaction hash with version and lock_time"""
        tx_string = f"{self.version}{self.sender}{self.receiver}{self.amount}{self.fee}{self.timestamp}{self.lock_time}"
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def is_valid(self) -> Tuple[bool, str]:
        """Enhanced validation with detailed error messages"""
        if self.amount <= 0:
            return False, "Amount must be positive"
        
        if self.amount < Config.DUST_THRESHOLD:
            return False, f"Amount below dust threshold ({Config.DUST_THRESHOLD})"
        
        if self.fee < Config.MIN_TRANSACTION_FEE:
            return False, f"Fee below minimum ({Config.MIN_TRANSACTION_FEE})"
        
        if self.sender == self.receiver:
            return False, "Sender and receiver cannot be the same"
        
        if not self.sender or not self.receiver:
            return False, "Invalid sender or receiver address"
        
        if self.timestamp > time.time() + 7200:  # 2 hours in future
            return False, "Transaction timestamp too far in future"
        
        return True, "Valid"
    
    def get_size(self) -> int:
        """Calculate transaction size in bytes"""
        return len(json.dumps(self.to_dict()).encode('utf-8'))

@dataclass
class MainnetBlock:
    """Production-ready block class with enhanced features"""
    index: int
    timestamp: float
    transactions: List[MainnetTransaction]
    previous_hash: str
    nonce: int = 0
    hash: str = ""
    merkle_root: str = ""
    difficulty: int = Config.INITIAL_DIFFICULTY
    miner: str = ""
    reward: float = Config.BLOCK_REWARD
    version: int = 1
    bits: int = 0
    size: int = 0
    
    def __post_init__(self):
        if not self.merkle_root:
            self.merkle_root = self.calculate_merkle_root()
        if not self.hash:
            self.hash = self.calculate_hash()
        if not self.size:
            self.size = self.calculate_size()
        if not self.timestamp:
            self.timestamp = time.time()
    
    def calculate_hash(self) -> str:
        """Calculate block hash"""
        block_string = f"{self.version}{self.index}{self.timestamp}{self.previous_hash}{self.merkle_root}{self.nonce}{self.difficulty}{self.bits}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def calculate_merkle_root(self) -> str:
        """Calculate Merkle root with proper binary tree structure"""
        if not self.transactions:
            return hashlib.sha256(b"").hexdigest()
        
        tx_hashes = [tx.tx_id for tx in self.transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])  # Duplicate last hash if odd
            
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            
            tx_hashes = new_hashes
        
        return tx_hashes[0]
    
    def calculate_size(self) -> int:
        """Calculate block size in bytes"""
        return len(json.dumps(self.to_dict()).encode('utf-8'))
    
    def to_dict(self) -> dict:
        """Convert block to dictionary"""
        return {
            'version': self.version,
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash,
            'merkle_root': self.merkle_root,
            'difficulty': self.difficulty,
            'miner': self.miner,
            'reward': self.reward,
            'bits': self.bits,
            'size': self.size
        }
    
    def mine_block(self, difficulty: int, miner_address: str, callback=None) -> dict:
        """Mine block with production-ready proof of work"""
        target = "0" * difficulty
        mining_stats = {
            'start_time': time.time(),
            'nonce': 0,
            'hash_rate': 0,
            'found': False,
            'target': target
        }
        
        self.difficulty = difficulty
        self.miner = miner_address
        self.nonce = 0
        
        logger.info(f"Starting to mine block {self.index} with difficulty {difficulty}")
        
        while True:
            self.hash = self.calculate_hash()
            mining_stats['nonce'] = self.nonce
            
            if callback:
                callback(mining_stats)
            
            if self.hash.startswith(target):
                mining_stats['found'] = True
                mining_stats['end_time'] = time.time()
                mining_stats['duration'] = mining_stats['end_time'] - mining_stats['start_time']
                mining_stats['hash_rate'] = self.nonce / max(mining_stats['duration'], 0.001)
                
                logger.info(f"Block {self.index} mined! Hash: {self.hash}, Nonce: {self.nonce}, Time: {mining_stats['duration']:.2f}s")
                break
            
            self.nonce += 1
            
            # Update hash rate every 1000 nonces
            if self.nonce % 1000 == 0:
                elapsed = time.time() - mining_stats['start_time']
                mining_stats['hash_rate'] = self.nonce / max(elapsed, 0.001)
        
        return mining_stats

class MainnetBlockchain:
    """Production-ready GSC blockchain implementation"""
    
    def __init__(self):
        self.chain: List[MainnetBlock] = []
        self.mempool: List[MainnetTransaction] = []
        self.difficulty = Config.INITIAL_DIFFICULTY
        self.mining_reward = Config.BLOCK_REWARD
        self.balances: Dict[str, float] = {}
        self.utxos: Dict[str, List[dict]] = {}  # Unspent transaction outputs
        self.lock = threading.RLock()
        self.checkpoints: Dict[int, str] = {}  # Block height -> hash checkpoints
        
        # Performance metrics
        self.metrics = {
            'blocks_mined': 0,
            'transactions_processed': 0,
            'total_fees_collected': 0.0,
            'average_block_time': Config.BLOCK_TIME_TARGET,
            'network_hash_rate': 0.0
        }
        
        # Initialize with genesis block
        self.create_genesis_block()
        logger.info("Mainnet blockchain initialized")
    
    def create_genesis_block(self) -> MainnetBlock:
        """Create the mainnet genesis block"""
        # Genesis transactions - only genesis reward
        genesis_transactions = []
        
        # Only genesis reward to specified address (255 GSC)
        genesis_reward_tx = MainnetTransaction(
            sender="GENESIS",
            receiver=Config.GENESIS_REWARD_ADDRESS,
            amount=Config.GENESIS_REWARD_AMOUNT,
            fee=0.0,
            timestamp=Config.GENESIS_TIMESTAMP,
            signature="GENESIS_SIGNATURE"
        )
        genesis_transactions.append(genesis_reward_tx)
        
        genesis_block = MainnetBlock(
            index=0,
            timestamp=Config.GENESIS_TIMESTAMP,
            transactions=genesis_transactions,
            previous_hash=Config.GENESIS_PREVIOUS_HASH,
            nonce=Config.GENESIS_NONCE,
            difficulty=Config.GENESIS_DIFFICULTY,
            miner="GENESIS_MINER"
        )
        
        # Set genesis hash manually for consistency
        genesis_block.hash = self.calculate_genesis_hash()
        
        self.chain.append(genesis_block)
        
        # Update balances - only genesis reward
        self.balances[Config.GENESIS_REWARD_ADDRESS] = Config.GENESIS_REWARD_AMOUNT
        
        # Add genesis checkpoint
        self.checkpoints[0] = genesis_block.hash
        
        logger.info(f"Genesis block created: {genesis_block.hash}")
        logger.info(f"Genesis Address Balance: {Config.GENESIS_REWARD_AMOUNT} GSC")
        logger.info(f"Total Genesis Supply: {Config.GENESIS_REWARD_AMOUNT} GSC")
        logger.info(f"Remaining supply (21.75T - 255) will be created through mining")
        return genesis_block
    
    def calculate_genesis_hash(self) -> str:
        """Calculate deterministic genesis block hash"""
        genesis_string = f"GSC_MAINNET_GENESIS_{Config.GENESIS_TIMESTAMP}_{Config.GENESIS_COINBASE_MESSAGE}"
        return hashlib.sha256(genesis_string.encode()).hexdigest()
    
    def get_latest_block(self) -> MainnetBlock:
        """Get the latest block in the chain"""
        with self.lock:
            return self.chain[-1] if self.chain else None
    
    def add_transaction_to_mempool(self, transaction: MainnetTransaction) -> Tuple[bool, str]:
        """Add transaction to mempool with validation"""
        with self.lock:
            # Validate transaction
            is_valid, error_msg = transaction.is_valid()
            if not is_valid:
                return False, error_msg
            
            # Check for double spending
            if self.is_double_spend(transaction):
                return False, "Double spending detected"
            
            # Check sender balance
            sender_balance = self.get_balance(transaction.sender)
            total_needed = transaction.amount + transaction.fee
            
            if sender_balance < total_needed:
                return False, f"Insufficient balance: {sender_balance} < {total_needed}"
            
            # Check mempool size limit
            if len(self.mempool) >= Config.MAX_TRANSACTIONS_PER_BLOCK * 2:
                return False, "Mempool full"
            
            # Add to mempool
            self.mempool.append(transaction)
            logger.info(f"Transaction added to mempool: {transaction.tx_id}")
            return True, "Transaction added to mempool"
    
    def is_double_spend(self, transaction: MainnetTransaction) -> bool:
        """Check if transaction is a double spend"""
        # Check against mempool
        for tx in self.mempool:
            if (tx.sender == transaction.sender and 
                tx.tx_id != transaction.tx_id and
                tx.timestamp == transaction.timestamp):
                return True
        return False
    
    def mine_pending_transactions(self, miner_address: str, callback=None, force_mine=False) -> MainnetBlock:
        """Mine a new block with pending transactions - only mines if mempool has transactions"""
        with self.lock:
            if not self.mempool and not force_mine:
                logger.debug("No transactions in mempool - waiting for transactions before mining")
                return None
            
            if not self.mempool and force_mine:
                logger.info("Force mining empty block (for testing purposes)")
                # Create empty block with only coinbase transaction
            
            # Select transactions for block (fee priority)
            selected_txs = self.select_transactions_for_block()
            
            # Create coinbase transaction (mining reward)
            total_fees = sum(tx.fee for tx in selected_txs)
            current_reward = self.calculate_block_reward()
            
            coinbase_tx = MainnetTransaction(
                sender="COINBASE",
                receiver=miner_address,
                amount=current_reward + total_fees,
                fee=0.0,
                timestamp=time.time(),
                signature="COINBASE_SIGNATURE"
            )
            
            # Create new block
            new_block = MainnetBlock(
                index=len(self.chain),
                timestamp=time.time(),
                transactions=[coinbase_tx] + selected_txs,
                previous_hash=self.get_latest_block().hash,
                difficulty=self.difficulty,
                miner=miner_address
            )
            
            # Mine the block
            mining_stats = new_block.mine_block(self.difficulty, miner_address, callback)
            
            # Add block to chain
            self.chain.append(new_block)
            
            # Update balances
            self.update_balances_from_block(new_block)
            
            # Remove mined transactions from mempool
            for tx in selected_txs:
                if tx in self.mempool:
                    self.mempool.remove(tx)
            
            # Update metrics
            self.update_metrics(new_block, mining_stats)
            
            # Adjust difficulty if needed
            self.adjust_difficulty()
            
            logger.info(f"Block {new_block.index} mined and added to chain")
            return new_block
    
    def select_transactions_for_block(self) -> List[MainnetTransaction]:
        """Select transactions for mining (fee priority)"""
        # Sort by fee per byte (highest first)
        sorted_txs = sorted(self.mempool, key=lambda tx: tx.fee / tx.get_size(), reverse=True)
        
        selected = []
        total_size = 0
        
        for tx in sorted_txs:
            tx_size = tx.get_size()
            if (total_size + tx_size <= Config.MAX_BLOCK_SIZE and 
                len(selected) < Config.MAX_TRANSACTIONS_PER_BLOCK):
                selected.append(tx)
                total_size += tx_size
            else:
                break
        
        return selected
    
    def calculate_block_reward(self) -> float:
        """Calculate current block reward (with halving)"""
        halvings = len(self.chain) // Config.HALVING_INTERVAL
        return Config.BLOCK_REWARD / (2 ** halvings)
    
    def update_balances_from_block(self, block: MainnetBlock):
        """Update balance tracking from block transactions"""
        for tx in block.transactions:
            if tx.sender != "COINBASE" and tx.sender != "GENESIS":
                self.balances[tx.sender] = self.balances.get(tx.sender, 0) - (tx.amount + tx.fee)
            
            self.balances[tx.receiver] = self.balances.get(tx.receiver, 0) + tx.amount
    
    def get_balance(self, address: str) -> float:
        """Get balance for an address"""
        return self.balances.get(address, 0.0)
    
    def adjust_difficulty(self):
        """Keep difficulty constant as per configuration"""
        # Fixed difficulty - no adjustment needed
        if self.difficulty != Config.INITIAL_DIFFICULTY:
            self.difficulty = Config.INITIAL_DIFFICULTY
            logger.info(f"Difficulty reset to fixed value: {self.difficulty}")
    
    def update_metrics(self, block: MainnetBlock, mining_stats: dict):
        """Update blockchain metrics"""
        self.metrics['blocks_mined'] += 1
        self.metrics['transactions_processed'] += len(block.transactions)
        self.metrics['total_fees_collected'] += sum(tx.fee for tx in block.transactions)
        
        if len(self.chain) > 1:
            time_diff = block.timestamp - self.chain[-2].timestamp
            self.metrics['average_block_time'] = (
                self.metrics['average_block_time'] * 0.9 + time_diff * 0.1
            )
        
        self.metrics['network_hash_rate'] = mining_stats.get('hash_rate', 0)
    
    def is_chain_valid(self) -> Tuple[bool, str]:
        """Validate the entire blockchain"""
        with self.lock:
            if not self.chain:
                return False, "Empty chain"
            
            # Check genesis block
            if self.chain[0].hash != self.calculate_genesis_hash():
                return False, "Invalid genesis block"
            
            # Validate each block
            for i in range(1, len(self.chain)):
                current_block = self.chain[i]
                previous_block = self.chain[i - 1]
                
                # Check hash
                if current_block.hash != current_block.calculate_hash():
                    return False, f"Invalid hash at block {i}"
                
                # Check previous hash link
                if current_block.previous_hash != previous_block.hash:
                    return False, f"Invalid previous hash at block {i}"
                
                # Check merkle root
                if current_block.merkle_root != current_block.calculate_merkle_root():
                    return False, f"Invalid merkle root at block {i}"
                
                # Check proof of work
                target = "0" * current_block.difficulty
                if not current_block.hash.startswith(target):
                    return False, f"Invalid proof of work at block {i}"
                
                # Validate transactions
                for tx in current_block.transactions:
                    is_valid, error = tx.is_valid()
                    if not is_valid and tx.sender not in ["COINBASE", "GENESIS"]:
                        return False, f"Invalid transaction in block {i}: {error}"
            
            return True, "Chain is valid"
    
    def save_blockchain(self, filename: str = None):
        """Save blockchain to file"""
        if not filename:
            filename = Config.get_blockchain_path()
        
        with self.lock:
            blockchain_data = {
                'chain': [block.to_dict() for block in self.chain],
                'difficulty': self.difficulty,
                'mining_reward': self.mining_reward,
                'balances': self.balances,
                'metrics': self.metrics,
                'checkpoints': self.checkpoints,
                'network': Config.NETWORK_NAME,
                'version': 1
            }
            
            with open(filename, 'w') as f:
                json.dump(blockchain_data, f, indent=2)
            
            logger.info(f"Blockchain saved to {filename}")
    
    def load_blockchain(self, filename: str = None):
        """Load blockchain from file"""
        if not filename:
            filename = Config.get_blockchain_path()
        
        if not os.path.exists(filename):
            logger.info("No existing blockchain file found, starting fresh")
            return
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Verify network compatibility
            if data.get('network') != Config.NETWORK_NAME:
                logger.warning(f"Network mismatch: {data.get('network')} != {Config.NETWORK_NAME}")
                return
            
            with self.lock:
                # Load chain
                self.chain = []
                for block_data in data['chain']:
                    transactions = [
                        MainnetTransaction(**tx_data) 
                        for tx_data in block_data['transactions']
                    ]
                    block = MainnetBlock(
                        index=block_data['index'],
                        timestamp=block_data['timestamp'],
                        transactions=transactions,
                        previous_hash=block_data['previous_hash'],
                        nonce=block_data['nonce'],
                        hash=block_data['hash'],
                        merkle_root=block_data['merkle_root'],
                        difficulty=block_data['difficulty'],
                        miner=block_data['miner'],
                        reward=block_data.get('reward', Config.BLOCK_REWARD)
                    )
                    self.chain.append(block)
                
                # Load other data
                self.difficulty = data.get('difficulty', Config.INITIAL_DIFFICULTY)
                self.mining_reward = data.get('mining_reward', Config.BLOCK_REWARD)
                self.balances = data.get('balances', {})
                self.metrics = data.get('metrics', self.metrics)
                self.checkpoints = data.get('checkpoints', {})
            
            logger.info(f"Blockchain loaded from {filename} - {len(self.chain)} blocks")
            
        except Exception as e:
            logger.error(f"Failed to load blockchain: {e}")
    
    def get_blockchain_info(self) -> dict:
        """Get comprehensive blockchain information"""
        with self.lock:
            latest_block = self.get_latest_block()
            is_valid, validation_msg = self.is_chain_valid()
            
            return {
                'network': Config.NETWORK_NAME,
                'blocks': len(self.chain),
                'difficulty': self.difficulty,
                'latest_block_hash': latest_block.hash if latest_block else None,
                'latest_block_time': latest_block.timestamp if latest_block else None,
                'mempool_size': len(self.mempool),
                'total_supply': sum(self.balances.values()),
                'is_valid': is_valid,
                'validation_message': validation_msg,
                'metrics': self.metrics,
                'version': 1
            }
