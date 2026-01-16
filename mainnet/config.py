"""
GSC Coin Mainnet Configuration
Production-ready configuration for GSC blockchain mainnet
"""

import os
from datetime import datetime

class MainnetConfig:
    # Network Configuration
    NETWORK_NAME = "GSC_MAINNET"
    NETWORK_ID = 1
    DEFAULT_PORT = 8333
    RPC_PORT = 8334
    
    # Blockchain Parameters
    BLOCK_TIME_TARGET = 120  # 2 minutes in seconds
    DIFFICULTY_ADJUSTMENT_INTERVAL = 2016  # blocks (maintain same for stability)
    MAX_BLOCK_SIZE = 1000000  # 1MB
    MAX_TRANSACTIONS_PER_BLOCK = 4000
    
    # Mining Configuration
    INITIAL_DIFFICULTY = 5  # Fixed difficulty with 4 zeros (00000)
    MAX_DIFFICULTY = 5  # Keep difficulty constant
    BLOCK_REWARD = 50.0
    HALVING_INTERVAL = 1051200  # blocks (4 years: 4*365*24*30 blocks at 2min intervals)
    
    # Economic Parameters
    TOTAL_SUPPLY = 21750000000000  # 21.75 trillion GSC
    MIN_TRANSACTION_FEE = 0.1  # 0.1 GSC
    DUST_THRESHOLD = 0.00000546  # Minimum output value
    
    # Genesis Block Configuration
    GENESIS_TIMESTAMP = 1736766600  # January 13, 2026 (mainnet launch)
    GENESIS_PREVIOUS_HASH = "0" * 64
    GENESIS_NONCE = 0
    GENESIS_DIFFICULTY = 1
    GENESIS_COINBASE_MESSAGE = "GSC Coin Mainnet Genesis Block - The Future of Digital Currency"
    
    # Foundation Reserve
    FOUNDATION_ADDRESS = "GSC_FOUNDATION_RESERVE"
    FOUNDATION_INITIAL_SUPPLY = 2750000000000  # 2.75 trillion GSC for development/marketing
    
    # Genesis Reward Address
    GENESIS_REWARD_ADDRESS = "GSC1705641e65321ef23ac5fb3d470f39627"
    GENESIS_REWARD_AMOUNT = 255.0  # Genesis reward amount
    
    # Seed Nodes (Production)
    SEED_NODES = [
        "seed1.gsccoin.network:8333",
        "seed2.gsccoin.network:8333", 
        "seed3.gsccoin.network:8333",
        "seed4.gsccoin.network:8333"
    ]
    
    # Security Settings
    MIN_CONFIRMATIONS = 6
    MAX_REORG_DEPTH = 100
    CHECKPOINT_INTERVAL = 10000  # blocks
    
    # P2P Network Settings
    MAX_PEERS = 125
    MAX_OUTBOUND_CONNECTIONS = 8
    MAX_INBOUND_CONNECTIONS = 117
    CONNECTION_TIMEOUT = 30
    PING_INTERVAL = 120
    
    # Database and Storage
    DATA_DIR = os.path.expanduser("~/.gsccoin")
    BLOCKCHAIN_FILE = "mainnet_blockchain.json"
    WALLET_DIR = "wallets"
    LOG_DIR = "logs"
    
    # API Configuration
    API_ENABLED = True
    API_HOST = "0.0.0.0"
    API_PORT = 8335
    API_RATE_LIMIT = 100  # requests per minute
    
    # Monitoring and Health
    HEALTH_CHECK_INTERVAL = 60  # seconds
    METRICS_ENABLED = True
    PROMETHEUS_PORT = 9090
    
    @classmethod
    def get_data_dir(cls):
        """Get or create data directory"""
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR)
            os.makedirs(os.path.join(cls.DATA_DIR, cls.WALLET_DIR))
            os.makedirs(os.path.join(cls.DATA_DIR, cls.LOG_DIR))
        return cls.DATA_DIR
    
    @classmethod
    def get_blockchain_path(cls):
        """Get blockchain file path"""
        return os.path.join(cls.get_data_dir(), cls.BLOCKCHAIN_FILE)
    
    @classmethod
    def is_mainnet(cls):
        """Check if running on mainnet"""
        return cls.NETWORK_ID == 1

class TestnetConfig(MainnetConfig):
    """Testnet configuration inherits from mainnet but overrides key parameters"""
    NETWORK_NAME = "GSC_TESTNET"
    NETWORK_ID = 2
    DEFAULT_PORT = 18333
    RPC_PORT = 18334
    API_PORT = 18335
    
    # Faster testing parameters
    BLOCK_TIME_TARGET = 60  # 1 minute
    DIFFICULTY_ADJUSTMENT_INTERVAL = 144  # blocks
    INITIAL_DIFFICULTY = 3  # Lower difficulty for testing
    MAX_DIFFICULTY = 3  # Keep testnet difficulty constant
    HALVING_INTERVAL = 525600  # 2 years for testnet (faster testing)
    
    # Testnet seed nodes
    SEED_NODES = [
        "testnet1.gsccoin.network:18333",
        "testnet2.gsccoin.network:18333"
    ]
    
    DATA_DIR = os.path.expanduser("~/.gsccoin-testnet")
    BLOCKCHAIN_FILE = "testnet_blockchain.json"
    
    @classmethod
    def is_mainnet(cls):
        return False

# Default to mainnet
Config = MainnetConfig
