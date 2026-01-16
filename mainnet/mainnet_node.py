"""
GSC Coin Mainnet Node
Production-ready blockchain node with full functionality
"""

import os
import sys
import time
import signal
import logging
import threading
import argparse
from typing import Optional
from .config import Config, MainnetConfig, TestnetConfig
from .mainnet_blockchain import MainnetBlockchain
from .mainnet_network import MainnetNetworkNode
from .mainnet_wallet import MainnetWalletManager

logger = logging.getLogger(__name__)

class MainnetNode:
    """Production GSC blockchain node"""
    
    def __init__(self, config_class=MainnetConfig):
        self.config = config_class
        self.blockchain = MainnetBlockchain()
        self.network = MainnetNetworkNode(self.blockchain, self.config.DEFAULT_PORT)
        self.wallet_manager = MainnetWalletManager()
        self.running = False
        self.mining_thread = None
        self.is_mining = False
        
        # Set up logging
        self._setup_logging()
        
        # Load blockchain
        self.blockchain.load_blockchain()
        
        logger.info(f"GSC {self.config.NETWORK_NAME} node initialized")
    
    def _setup_logging(self):
        """Set up production logging"""
        log_dir = os.path.join(self.config.get_data_dir(), self.config.LOG_DIR)
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'node.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def start(self):
        """Start the blockchain node"""
        if self.running:
            return
        
        self.running = True
        logger.info(f"Starting GSC {self.config.NETWORK_NAME} node...")
        
        # Start network
        self.network.start()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"GSC node started successfully on port {self.config.DEFAULT_PORT}")
        logger.info(f"Data directory: {self.config.get_data_dir()}")
        logger.info(f"Blockchain height: {len(self.blockchain.chain)}")
        
        # Keep node running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the blockchain node"""
        if not self.running:
            return
        
        logger.info("Stopping GSC node...")
        self.running = False
        
        # Stop mining
        if self.is_mining:
            self.stop_mining()
        
        # Stop network
        self.network.stop()
        
        # Save blockchain
        self.blockchain.save_blockchain()
        
        logger.info("GSC node stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def start_mining(self, miner_address: str):
        """Start mining blocks"""
        if self.is_mining:
            logger.warning("Mining already in progress")
            return
        
        if not miner_address:
            logger.error("Miner address required")
            return
        
        self.is_mining = True
        self.mining_thread = threading.Thread(
            target=self._mining_loop,
            args=(miner_address,),
            daemon=True
        )
        self.mining_thread.start()
        
        logger.info(f"Started mining to address: {miner_address}")
    
    def stop_mining(self):
        """Stop mining blocks"""
        if not self.is_mining:
            return
        
        self.is_mining = False
        if self.mining_thread and self.mining_thread.is_alive():
            self.mining_thread.join(timeout=5)
        
        logger.info("Stopped mining")
    
    def _mining_loop(self, miner_address: str):
        """Main mining loop"""
        while self.is_mining and self.running:
            try:
                # Check if there are transactions to mine
                if not self.blockchain.mempool:
                    time.sleep(5)
                    continue
                
                # Mine a new block
                def mining_callback(stats):
                    if stats['nonce'] % 10000 == 0:
                        logger.debug(f"Mining block {len(self.blockchain.chain)}: nonce={stats['nonce']}, rate={stats['hash_rate']:.0f} H/s")
                
                new_block = self.blockchain.mine_pending_transactions(miner_address, mining_callback)
                
                if new_block:
                    logger.info(f"Mined block {new_block.index}! Hash: {new_block.hash}")
                    
                    # Broadcast to network
                    self.network.broadcast_block(new_block)
                    
                    # Save blockchain
                    self.blockchain.save_blockchain()
                
            except Exception as e:
                logger.error(f"Mining error: {e}")
                time.sleep(10)
    
    def get_status(self) -> dict:
        """Get node status information"""
        return {
            'network': self.config.NETWORK_NAME,
            'running': self.running,
            'mining': self.is_mining,
            'blockchain_info': self.blockchain.get_blockchain_info(),
            'network_info': self.network.get_network_info(),
            'wallet_count': len(self.wallet_manager.wallets),
            'data_dir': self.config.get_data_dir()
        }

def main():
    """Main entry point for GSC node"""
    parser = argparse.ArgumentParser(description='GSC Coin Blockchain Node')
    parser.add_argument('--testnet', action='store_true', help='Run on testnet')
    parser.add_argument('--port', type=int, help='P2P port to listen on')
    parser.add_argument('--mine', type=str, help='Start mining to specified address')
    parser.add_argument('--datadir', type=str, help='Data directory path')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    args = parser.parse_args()
    
    # Select configuration
    config_class = TestnetConfig if args.testnet else MainnetConfig
    
    # Override port if specified
    if args.port:
        config_class.DEFAULT_PORT = args.port
    
    # Override data directory if specified
    if args.datadir:
        config_class.DATA_DIR = args.datadir
    
    # Create and start node
    node = MainnetNode(config_class)
    
    try:
        node.start()
        
        # Start mining if requested
        if args.mine:
            node.start_mining(args.mine)
        
        # Keep running
        while node.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        node.stop()
    except Exception as e:
        logger.error(f"Node error: {e}")
        node.stop()
        sys.exit(1)

if __name__ == '__main__':
    main()
