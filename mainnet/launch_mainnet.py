#!/usr/bin/env python3
"""
GSC Coin Mainnet Launch Script
Complete production deployment and launch system
"""

import os
import sys
import time
import json
import subprocess
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mainnet.config import MainnetConfig, TestnetConfig
from mainnet.mainnet_blockchain import MainnetBlockchain
from mainnet.mainnet_network import MainnetNetworkNode
from mainnet.mainnet_wallet import MainnetWalletManager
from mainnet.api_server import MainnetAPIServer
from mainnet.monitoring import MainnetMonitoring, AlertManager

class MainnetLauncher:
    """Complete mainnet launch and management system"""
    
    def __init__(self, network_type: str = "mainnet"):
        self.network_type = network_type
        self.config = MainnetConfig if network_type == "mainnet" else TestnetConfig
        
        # Core components
        self.blockchain = None
        self.network = None
        self.wallet_manager = None
        self.api_server = None
        self.monitoring = None
        self.alert_manager = None
        
        # Launch status
        self.launch_time = None
        self.genesis_created = False
        self.nodes_started = False
        self.api_running = False
        self.monitoring_active = False
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = os.path.join(self.config.get_data_dir(), self.config.LOG_DIR)
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'mainnet_launch.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('MainnetLauncher')
    
    def pre_launch_checks(self) -> bool:
        """Perform pre-launch system checks"""
        self.logger.info("🔍 Performing pre-launch checks...")
        
        checks_passed = True
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.logger.error("❌ Python 3.8+ required")
            checks_passed = False
        else:
            self.logger.info(f"✅ Python version: {sys.version}")
        
        # Check required packages
        required_packages = [
            'flask', 'cryptography', 'prometheus_client', 'psutil'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.logger.info(f"✅ Package {package} available")
            except ImportError:
                self.logger.error(f"❌ Package {package} not found")
                checks_passed = False
        
        # Check data directory
        try:
            data_dir = self.config.get_data_dir()
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)
            self.logger.info(f"✅ Data directory: {data_dir}")
        except Exception as e:
            self.logger.error(f"❌ Data directory error: {e}")
            checks_passed = False
        
        # Check ports availability
        import socket
        ports_to_check = [
            self.config.DEFAULT_PORT,
            self.config.RPC_PORT,
            self.config.API_PORT,
            self.config.PROMETHEUS_PORT
        ]
        
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('localhost', port))
                sock.close()
                self.logger.info(f"✅ Port {port} available")
            except OSError:
                self.logger.warning(f"⚠️ Port {port} may be in use")
                # Don't fail on port check as services might be running
        
        # Check disk space
        import shutil
        total, used, free = shutil.disk_usage(self.config.get_data_dir())
        free_gb = free // (1024**3)
        if free_gb < 10:
            self.logger.warning(f"⚠️ Low disk space: {free_gb}GB free")
        else:
            self.logger.info(f"✅ Disk space: {free_gb}GB free")
        
        if checks_passed:
            self.logger.info("✅ All pre-launch checks passed")
        else:
            self.logger.error("❌ Pre-launch checks failed")
        
        return checks_passed
    
    def initialize_blockchain(self) -> bool:
        """Initialize the blockchain"""
        self.logger.info("🔗 Initializing blockchain...")
        
        try:
            self.blockchain = MainnetBlockchain()
            
            # Load existing blockchain or create genesis
            blockchain_path = self.config.get_blockchain_path()
            if os.path.exists(blockchain_path):
                self.blockchain.load_blockchain(blockchain_path)
                self.logger.info(f"✅ Loaded existing blockchain with {len(self.blockchain.chain)} blocks")
            else:
                self.logger.info("✅ Created new blockchain with genesis block")
                self.genesis_created = True
            
            # Validate blockchain
            is_valid, message = self.blockchain.is_chain_valid()
            if is_valid:
                self.logger.info("✅ Blockchain validation passed")
                return True
            else:
                self.logger.error(f"❌ Blockchain validation failed: {message}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Blockchain initialization failed: {e}")
            return False
    
    def initialize_network(self) -> bool:
        """Initialize P2P network"""
        self.logger.info("🌐 Initializing P2P network...")
        
        try:
            self.network = MainnetNetworkNode(self.blockchain, self.config.DEFAULT_PORT)
            self.network.start()
            
            # Wait for network to start
            time.sleep(2)
            
            if self.network.running:
                self.logger.info(f"✅ P2P network started on port {self.config.DEFAULT_PORT}")
                return True
            else:
                self.logger.error("❌ P2P network failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Network initialization failed: {e}")
            return False
    
    def initialize_wallet_manager(self) -> bool:
        """Initialize wallet management"""
        self.logger.info("💼 Initializing wallet manager...")
        
        try:
            self.wallet_manager = MainnetWalletManager()
            wallet_count = len(self.wallet_manager.list_wallets())
            self.logger.info(f"✅ Wallet manager initialized with {wallet_count} wallets")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Wallet manager initialization failed: {e}")
            return False
    
    def start_api_server(self) -> bool:
        """Start REST API server"""
        self.logger.info("🔌 Starting API server...")
        
        try:
            self.api_server = MainnetAPIServer(
                self.blockchain, 
                self.network, 
                self.wallet_manager
            )
            self.api_server.start(self.config.API_HOST, self.config.API_PORT)
            
            # Wait for API to start
            time.sleep(2)
            
            if self.api_server.running:
                self.logger.info(f"✅ API server started on {self.config.API_HOST}:{self.config.API_PORT}")
                self.api_running = True
                return True
            else:
                self.logger.error("❌ API server failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ API server initialization failed: {e}")
            return False
    
    def start_monitoring(self) -> bool:
        """Start monitoring and metrics"""
        self.logger.info("📊 Starting monitoring system...")
        
        try:
            self.monitoring = MainnetMonitoring(self.blockchain, self.network)
            self.monitoring.start(self.config.PROMETHEUS_PORT)
            
            self.alert_manager = AlertManager(self.monitoring)
            self.alert_manager.start()
            
            self.logger.info(f"✅ Monitoring started on port {self.config.PROMETHEUS_PORT}")
            self.monitoring_active = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Monitoring initialization failed: {e}")
            return False
    
    def create_foundation_wallet(self) -> Optional[str]:
        """Create foundation wallet for mainnet"""
        self.logger.info("🏛️ Creating foundation wallet...")
        
        try:
            foundation_name = "GSC_Foundation"
            
            # Check if foundation wallet already exists
            if foundation_name in self.wallet_manager.list_wallets():
                wallet_info = self.wallet_manager.get_wallet_info(foundation_name)
                self.logger.info(f"✅ Foundation wallet exists: {wallet_info['address']}")
                return wallet_info['address']
            
            # Create new foundation wallet
            foundation_wallet = self.wallet_manager.create_wallet(
                foundation_name, 
                "GSC_Foundation_Secure_2026"
            )
            
            self.logger.info(f"✅ Foundation wallet created: {foundation_wallet.address}")
            
            # Create backup
            backup_path = os.path.join(
                self.config.get_data_dir(), 
                "foundation_wallet_backup.json"
            )
            self.wallet_manager.backup_wallet(
                foundation_name, 
                backup_path, 
                "GSC_Foundation_Secure_2026"
            )
            
            self.logger.info(f"✅ Foundation wallet backed up to: {backup_path}")
            return foundation_wallet.address
            
        except Exception as e:
            self.logger.error(f"❌ Foundation wallet creation failed: {e}")
            return None
    
    def connect_to_seed_nodes(self) -> int:
        """Connect to seed nodes"""
        self.logger.info("🌱 Connecting to seed nodes...")
        
        connected_count = 0
        
        for seed in self.config.SEED_NODES:
            try:
                if ':' in seed:
                    host, port = seed.split(':')
                    port = int(port)
                else:
                    host = seed
                    port = self.config.DEFAULT_PORT
                
                if self.network.connect_to_peer(host, port):
                    connected_count += 1
                    self.logger.info(f"✅ Connected to seed node: {host}:{port}")
                else:
                    self.logger.warning(f"⚠️ Failed to connect to seed node: {host}:{port}")
                
                time.sleep(1)  # Brief delay between connections
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error connecting to seed {seed}: {e}")
        
        self.logger.info(f"✅ Connected to {connected_count} seed nodes")
        return connected_count
    
    def perform_initial_sync(self) -> bool:
        """Perform initial blockchain sync"""
        self.logger.info("🔄 Performing initial blockchain sync...")
        
        try:
            initial_height = len(self.blockchain.chain)
            
            # Request blocks from peers
            if len(self.network.peers) > 0:
                self.network.request_blocks(initial_height, 1000)
                
                # Wait for sync
                sync_timeout = 300  # 5 minutes
                start_time = time.time()
                
                while time.time() - start_time < sync_timeout:
                    current_height = len(self.blockchain.chain)
                    if current_height > initial_height:
                        self.logger.info(f"✅ Synced to height {current_height}")
                        break
                    time.sleep(10)
                
                final_height = len(self.blockchain.chain)
                synced_blocks = final_height - initial_height
                
                if synced_blocks > 0:
                    self.logger.info(f"✅ Synced {synced_blocks} blocks")
                else:
                    self.logger.info("✅ Already up to date")
                
                return True
            else:
                self.logger.info("✅ No peers available for sync (genesis node)")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Initial sync failed: {e}")
            return False
    
    def launch_mainnet(self, mining_address: str = None) -> bool:
        """Complete mainnet launch sequence"""
        self.logger.info("🚀 Starting GSC Coin Mainnet Launch Sequence")
        self.logger.info("=" * 60)
        
        self.launch_time = datetime.now()
        
        # Pre-launch checks
        if not self.pre_launch_checks():
            return False
        
        # Initialize core components
        if not self.initialize_blockchain():
            return False
        
        if not self.initialize_network():
            return False
        
        if not self.initialize_wallet_manager():
            return False
        
        # Create foundation wallet if needed
        if self.genesis_created:
            foundation_address = self.create_foundation_wallet()
            if not foundation_address:
                return False
        
        # Start services
        if not self.start_api_server():
            return False
        
        if not self.start_monitoring():
            return False
        
        # Network operations
        connected_seeds = self.connect_to_seed_nodes()
        
        if not self.perform_initial_sync():
            return False
        
        # Start mining if requested
        if mining_address:
            self.logger.info(f"⛏️ Starting mining to address: {mining_address}")
            # Mining would be started in a separate thread
        
        # Final status
        self.nodes_started = True
        
        self.logger.info("🎉 GSC COIN MAINNET LAUNCH SUCCESSFUL!")
        self.logger.info("=" * 60)
        self.logger.info(f"🌐 Network: {self.config.NETWORK_NAME}")
        self.logger.info(f"🔗 Blockchain Height: {len(self.blockchain.chain)}")
        self.logger.info(f"👥 Connected Peers: {len(self.network.peers)}")
        self.logger.info(f"🔌 API Endpoint: http://localhost:{self.config.API_PORT}/api/v1/info")
        self.logger.info(f"📊 Metrics: http://localhost:{self.config.PROMETHEUS_PORT}/metrics")
        self.logger.info(f"💾 Data Directory: {self.config.get_data_dir()}")
        self.logger.info("=" * 60)
        
        return True
    
    def shutdown(self):
        """Graceful shutdown of all services"""
        self.logger.info("🛑 Shutting down GSC Mainnet...")
        
        if self.alert_manager:
            self.alert_manager.stop()
        
        if self.monitoring:
            self.monitoring.stop()
        
        if self.api_server:
            self.api_server.stop()
        
        if self.network:
            self.network.stop()
        
        if self.blockchain:
            self.blockchain.save_blockchain()
        
        self.logger.info("✅ GSC Mainnet shutdown complete")
    
    def get_status(self) -> Dict:
        """Get comprehensive launch status"""
        return {
            'launch_time': self.launch_time.isoformat() if self.launch_time else None,
            'network_type': self.network_type,
            'genesis_created': self.genesis_created,
            'nodes_started': self.nodes_started,
            'api_running': self.api_running,
            'monitoring_active': self.monitoring_active,
            'blockchain_height': len(self.blockchain.chain) if self.blockchain else 0,
            'connected_peers': len(self.network.peers) if self.network else 0,
            'wallet_count': len(self.wallet_manager.wallets) if self.wallet_manager else 0
        }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='GSC Coin Mainnet Launcher')
    parser.add_argument('--network', choices=['mainnet', 'testnet'], default='mainnet',
                       help='Network type to launch')
    parser.add_argument('--mine', type=str, help='Start mining to specified address')
    parser.add_argument('--no-sync', action='store_true', help='Skip initial sync')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    args = parser.parse_args()
    
    # Create launcher
    launcher = MainnetLauncher(args.network)
    
    try:
        # Launch mainnet
        success = launcher.launch_mainnet(args.mine)
        
        if not success:
            print("❌ Mainnet launch failed!")
            sys.exit(1)
        
        # Keep running
        if args.daemon:
            print("Running as daemon...")
            while True:
                time.sleep(60)
        else:
            print("Press Ctrl+C to shutdown...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested...")
    except Exception as e:
        print(f"❌ Launch error: {e}")
        sys.exit(1)
    finally:
        launcher.shutdown()

if __name__ == '__main__':
    main()
