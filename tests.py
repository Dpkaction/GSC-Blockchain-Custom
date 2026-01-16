"""
GSC Coin Test Suite - Comprehensive Testing Framework
Tests for blockchain, networking, RPC, and security features
"""

import unittest
import tempfile
import os
import sys
import time
import threading
import json
import requests
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blockchain_improved import GSCBlockchain, Transaction, Block
from network_improved import GSCNetworkNode, MessageValidator, BanscoreManager
from rpc_server_improved import GSCRPCServer, RPCErrorCodes
from wallet_manager import WalletManager
from gsc_logger import blockchain_logger, network_logger, rpc_logger

class TestBlockchain(unittest.TestCase):
    """Test blockchain core functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.blockchain = GSCBlockchain()
    
    def test_genesis_block(self):
        """Test genesis block creation"""
        self.assertEqual(len(self.blockchain.chain), 1)
        genesis = self.blockchain.chain[0]
        self.assertEqual(genesis.index, 0)
        self.assertEqual(genesis.previous_hash, "0" * 64)
        self.assertEqual(len(genesis.transactions), 1)
        self.assertEqual(genesis.transactions[0].receiver, "GSC_FOUNDATION_RESERVE")
    
    def test_transaction_validation(self):
        """Test transaction validation"""
        # Valid transaction
        tx = Transaction(
            sender="test_sender",
            receiver="test_receiver",
            amount=10.0,
            fee=0.1,
            timestamp=time.time()
        )
        self.assertTrue(tx.is_valid())
        
        # Invalid amount
        tx_invalid = Transaction(
            sender="test_sender",
            receiver="test_receiver",
            amount=-10.0,
            fee=0.1,
            timestamp=time.time()
        )
        self.assertFalse(tx_invalid.is_valid())
        
        # Same sender and receiver
        tx_same = Transaction(
            sender="test",
            receiver="test",
            amount=10.0,
            fee=0.1,
            timestamp=time.time()
        )
        self.assertFalse(tx_same.is_valid())
    
    def test_block_validation(self):
        """Test block validation"""
        # Create valid block
        tx = Transaction(
            sender="GSC_FOUNDATION_RESERVE",
            receiver="test_receiver",
            amount=10.0,
            fee=0.1,
            timestamp=time.time()
        )
        
        block = Block(
            index=1,
            timestamp=time.time(),
            transactions=[tx],
            previous_hash=self.blockchain.chain[0].hash,
            difficulty=4,
            reward=50.0
        )
        
        # Mine block
        block.mine_block(4, "test_miner")
        self.assertTrue(block.is_valid(self.blockchain.chain[0]))
        
        # Test BIP-34 compliance
        coinbase = block.transactions[0]
        self.assertTrue(coinbase.is_coinbase())
        self.assertIn(str(block.index), coinbase.extra_data)
    
    def test_mempool_operations(self):
        """Test mempool operations"""
        tx = Transaction(
            sender="GSC_FOUNDATION_RESERVE",
            receiver="test_receiver",
            amount=10.0,
            fee=0.1,
            timestamp=time.time()
        )
        
        # Add transaction to mempool
        self.assertTrue(self.blockchain.add_transaction_to_mempool(tx))
        self.assertEqual(len(self.blockchain.mempool), 1)
        
        # Test duplicate transaction
        self.assertFalse(self.blockchain.add_transaction_to_mempool(tx))
        
        # Test transaction lookup
        self.assertTrue(self.blockchain.is_tx_known(tx.tx_id))
        result = self.blockchain.get_transaction_by_hash(tx.tx_id)
        self.assertIsNotNone(result)
        found_tx, height = result
        self.assertEqual(found_tx.tx_id, tx.tx_id)
        self.assertEqual(height, -1)  # -1 indicates mempool
    
    def test_block_mining(self):
        """Test block mining"""
        # Add transactions to mempool
        for i in range(3):
            tx = Transaction(
                sender="GSC_FOUNDATION_RESERVE",
                receiver=f"receiver_{i}",
                amount=10.0,
                fee=0.1,
                timestamp=time.time()
            )
            self.blockchain.add_transaction_to_mempool(tx)
        
        # Mine block
        block = self.blockchain.mine_pending_transactions("test_miner")
        self.assertIsNotNone(block)
        self.assertEqual(block.index, 1)
        self.assertEqual(len(block.transactions), 4)  # 3 mempool + 1 coinbase
        
        # Check mempool is cleared
        self.assertEqual(len(self.blockchain.mempool), 0)
    
    def test_balance_calculation(self):
        """Test balance calculation"""
        # Mine a block with transactions
        tx = Transaction(
            sender="GSC_FOUNDATION_RESERVE",
            receiver="test_receiver",
            amount=100.0,
            fee=0.1,
            timestamp=time.time()
        )
        
        block = Block(
            index=1,
            timestamp=time.time(),
            transactions=[tx],
            previous_hash=self.blockchain.chain[0].hash,
            difficulty=4,
            reward=50.0
        )
        
        block.mine_block(4, "test_miner")
        self.blockchain.add_block(block)
        
        # Check balances
        foundation_balance = self.blockchain.get_balance("GSC_FOUNDATION_RESERVE")
        receiver_balance = self.blockchain.get_balance("test_receiver")
        miner_balance = self.blockchain.get_balance("test_miner")
        
        expected_foundation = 21750000000000 - 100.0 - 0.1
        self.assertEqual(foundation_balance, expected_foundation)
        self.assertEqual(receiver_balance, 100.0)
        self.assertEqual(miner_balance, 50.0 + 0.1)  # reward + fee
    
    def test_blockchain_persistence(self):
        """Test blockchain save/load"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # Override blockchain file path
            original_get_path = self.blockchain.get_blockchain_file_path
            self.blockchain.get_blockchain_file_path = lambda: temp_path
            
            # Save blockchain
            self.blockchain.save_blockchain()
            self.assertTrue(os.path.exists(temp_path))
            
            # Create new blockchain and load
            new_blockchain = GSCBlockchain()
            new_blockchain.get_blockchain_file_path = lambda: temp_path
            loaded = new_blockchain.load_blockchain()
            self.assertTrue(loaded)
            
            # Verify loaded data
            self.assertEqual(len(new_blockchain.chain), len(self.blockchain.chain))
            self.assertEqual(new_blockchain.chain[0].hash, self.blockchain.chain[0].hash)
            
        finally:
            # Restore original method and cleanup
            self.blockchain.get_blockchain_file_path = original_get_path
            if os.path.exists(temp_path):
                os.unlink(temp_path)

class TestNetwork(unittest.TestCase):
    """Test networking functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.blockchain = Mock()
        self.blockchain.chain = []
        self.blockchain.mempool = []
        self.node = GSCNetworkNode(self.blockchain, port=18444)  # Test port
    
    def test_message_validation(self):
        """Test message validation"""
        # Valid message
        valid_msg = {
            'type': 'version',
            'version': 1,
            'node_id': 'test123',
            'timestamp': time.time()
        }
        error = MessageValidator.validate_message(valid_msg)
        self.assertIsNone(error)
        
        # Missing required field
        invalid_msg = {
            'type': 'version',
            'version': 1
        }
        error = MessageValidator.validate_message(invalid_msg)
        self.assertIsNotNone(error)
        self.assertIn('node_id', error)
        
        # Unknown message type
        unknown_msg = {
            'type': 'unknown_type',
            'data': 'test'
        }
        error = MessageValidator.validate_message(unknown_msg)
        self.assertIsNone(error)  # Unknown types are allowed but not handled
    
    def test_banscore_manager(self):
        """Test banscore management"""
        banscore = BanscoreManager(max_banscore=50)
        
        # Add score below threshold
        banscore.add_score('192.168.1.1', 20, 'Test violation')
        self.assertFalse(banscore.is_banned('192.168.1.1'))
        
        # Add score above threshold
        banscore.add_score('192.168.1.1', 40, 'Major violation')
        self.assertTrue(banscore.is_banned('192.168.1.1'))
        
        # Test unban
        banscore.unban_peer('192.168.1.1')
        self.assertFalse(banscore.is_banned('192.168.1.1'))
    
    def test_connection_management(self):
        """Test connection management"""
        from network_improved import ConnectionManager
        
        conn_mgr = ConnectionManager(max_connections=2)
        
        # Test connection limit
        self.assertTrue(conn_mgr.can_connect('peer1:8333'))
        conn_mgr.add_connection('peer1:8333')
        
        self.assertTrue(conn_mgr.can_connect('peer2:8333'))
        conn_mgr.add_connection('peer2:8333')
        
        self.assertFalse(conn_mgr.can_connect('peer3:8333'))  # Limit reached
        
        # Test removal
        conn_mgr.remove_connection('peer1:8333')
        self.assertTrue(conn_mgr.can_connect('peer3:8333'))
    
    def test_peer_info_handling(self):
        """Test peer information handling"""
        from network_improved import PeerInfo
        
        peer_info = PeerInfo(
            address='192.168.1.1:8333',
            node_id='test123',
            version=1,
            last_seen=time.time(),
            banscore=0,
            connection_count=1
        )
        
        self.assertEqual(peer_info.address, '192.168.1.1:8333')
        self.assertEqual(peer_info.node_id, 'test123')
        self.assertEqual(peer_info.version, 1)

class TestRPC(unittest.TestCase):
    """Test RPC functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.blockchain = GSCBlockchain()
        self.wallet_manager = WalletManager()
        self.rpc_server = GSCRPCServer(
            self.blockchain, 
            self.wallet_manager, 
            host='127.0.0.1', 
            port=18332
        )
    
    def tearDown(self):
        """Clean up after tests"""
        if self.rpc_server.is_running():
            self.rpc_server.stop()
    
    def test_rpc_server_start_stop(self):
        """Test RPC server start and stop"""
        self.assertTrue(self.rpc_server.start())
        self.assertTrue(self.rpc_server.is_running())
        
        # Give server time to start
        time.sleep(0.1)
        
        self.rpc_server.stop()
        self.assertFalse(self.rpc_server.is_running())
    
    def test_rpc_blockchain_info(self):
        """Test getblockchaininfo RPC method"""
        handler = self.rpc_server.server.RequestHandlerClass(
            self.blockchain, 
            self.wallet_manager
        )
        
        result = handler.getblockchaininfo([])
        
        self.assertIn('chain', result)
        self.assertEqual(result['chain'], 'main')
        self.assertIn('blocks', result)
        self.assertEqual(result['blocks'], len(self.blockchain.chain))
        self.assertIn('difficulty', result)
        self.assertEqual(result['difficulty'], self.blockchain.difficulty)
    
    def test_rpc_block_methods(self):
        """Test block-related RPC methods"""
        handler = self.rpc_server.server.RequestHandlerClass(
            self.blockchain, 
            self.wallet_manager
        )
        
        # Test getblockcount
        count = handler.getblockcount([])
        self.assertEqual(count, len(self.blockchain.chain))
        
        # Test getbestblockhash
        best_hash = handler.getbestblockhash([])
        self.assertEqual(best_hash, self.blockchain.chain[0].hash)
        
        # Test getblockhash
        block_hash = handler.getblockhash([0])
        self.assertEqual(block_hash, self.blockchain.chain[0].hash)
        
        # Test getblock
        block_info = handler.getblock([0])
        self.assertEqual(block_info['hash'], self.blockchain.chain[0].hash)
        self.assertEqual(block_info['height'], 0)
    
    def test_rpc_transaction_methods(self):
        """Test transaction-related RPC methods"""
        handler = self.rpc_server.server.RequestHandlerClass(
            self.blockchain, 
            self.wallet_manager
        )
        
        # Test getmempoolinfo
        mempool_info = handler.getmempoolinfo([])
        self.assertIn('size', mempool_info)
        self.assertEqual(mempool_info['size'], len(self.blockchain.mempool))
        
        # Test getrawmempool
        mempool_txs = handler.getrawmempool([])
        self.assertIsInstance(mempool_txs, list)
        
        # Add transaction to mempool
        tx = Transaction(
            sender="GSC_FOUNDATION_RESERVE",
            receiver="test_receiver",
            amount=10.0,
            fee=0.1,
            timestamp=time.time()
        )
        self.blockchain.add_transaction_to_mempool(tx)
        
        # Check mempool again
        mempool_txs = handler.getrawmempool([])
        self.assertEqual(len(mempool_txs), 1)
        self.assertEqual(mempool_txs[0], tx.tx_id)
    
    def test_rpc_error_handling(self):
        """Test RPC error handling"""
        handler = self.rpc_server.server.RequestHandlerClass(
            self.blockchain, 
            self.wallet_manager
        )
        
        # Test invalid method
        with self.assertRaises(Exception):
            handler.rpc_methods['nonexistent_method']([])
        
        # Test getblock with invalid height
        with self.assertRaises(Exception):
            handler.getblock([999999])
        
        # Test getblockhash with invalid height
        with self.assertRaises(Exception):
            handler.getblockhash([-1])
    
    def test_rpc_wallet_methods(self):
        """Test wallet-related RPC methods"""
        # Create a wallet first
        wallet_info = self.wallet_manager.create_wallet("test_wallet")
        self.wallet_manager.current_wallet = "test_wallet"
        
        handler = self.rpc_server.server.RequestHandlerClass(
            self.blockchain, 
            self.wallet_manager
        )
        
        # Test getwalletinfo
        wallet_info = handler.getwalletinfo([])
        self.assertIn('walletname', wallet_info)
        self.assertIn('balance', wallet_info)
        
        # Test getbalance
        balance = handler.getbalance(['*'])
        self.assertIsInstance(balance, (int, float))
        
        # Test getnewaddress
        address = handler.getnewaddress([])
        self.assertIsInstance(address, str)
        self.assertTrue(len(address) > 0)

class TestSecurity(unittest.TestCase):
    """Test security features"""
    
    def test_transaction_double_spend(self):
        """Test double spend prevention"""
        blockchain = GSCBlockchain()
        
        # Create transaction that spends more than available
        tx = Transaction(
            sender="nonexistent_address",
            receiver="test_receiver",
            amount=999999999999.0,
            fee=0.1,
            timestamp=time.time()
        )
        
        # Should be rejected due to insufficient balance
        self.assertFalse(blockchain.add_transaction_to_mempool(tx))
    
    def test_block_validation_security(self):
        """Test block validation security"""
        blockchain = GSCBlockchain()
        
        # Try to add invalid block
        invalid_block = Block(
            index=1,
            timestamp=time.time(),
            transactions=[],
            previous_hash="invalid_hash",
            difficulty=4,
            reward=50.0
        )
        
        # Should be rejected
        self.assertFalse(blockchain.add_block(invalid_block))
    
    def test_message_size_limits(self):
        """Test message size limits"""
        # Test oversized message
        oversized_msg = {
            'type': 'headers',
            'headers': [{'dummy': 'data'}] * 3000  # Exceeds limit
        }
        
        error = MessageValidator.validate_message(oversized_msg)
        self.assertIsNotNone(error)
        self.assertIn('Too many headers', error)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        from network_improved import ConnectionManager
        from thread_safety import RateLimiter
        
        rate_limiter = RateLimiter(max_calls=2, time_window=1.0)
        
        # First two calls should succeed
        self.assertTrue(rate_limiter.is_allowed())
        self.assertTrue(rate_limiter.is_allowed())
        
        # Third call should fail
        self.assertFalse(rate_limiter.is_allowed())
        
        # Wait and try again
        time.sleep(1.1)
        self.assertTrue(rate_limiter.is_allowed())

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_blockchain_mining_integration(self):
        """Test complete mining workflow"""
        blockchain = GSCBlockchain()
        
        # Add transactions to mempool
        for i in range(5):
            tx = Transaction(
                sender="GSC_FOUNDATION_RESERVE",
                receiver=f"receiver_{i}",
                amount=10.0,
                fee=0.1,
                timestamp=time.time()
            )
            blockchain.add_transaction_to_mempool(tx)
        
        # Mine block
        block = blockchain.mine_pending_transactions("test_miner")
        self.assertIsNotNone(block)
        
        # Verify transactions are confirmed
        receiver_balance = blockchain.get_balance("receiver_0")
        self.assertEqual(receiver_balance, 10.0)
        
        miner_balance = blockchain.get_balance("test_miner")
        expected_miner = 50.0 + (5 * 0.1)  # reward + fees
        self.assertEqual(miner_balance, expected_miner)
    
    def test_persistence_integration(self):
        """Test blockchain persistence integration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create blockchain in temp directory
            blockchain = GSCBlockchain()
            
            # Mine a block
            tx = Transaction(
                sender="GSC_FOUNDATION_RESERVE",
                receiver="test_receiver",
                amount=100.0,
                fee=0.1,
                timestamp=time.time()
            )
            blockchain.add_transaction_to_mempool(tx)
            blockchain.mine_pending_transactions("test_miner")
            
            # Save blockchain
            original_path = blockchain.get_blockchain_file_path()
            temp_file = os.path.join(temp_dir, "test_blockchain.json")
            blockchain.get_blockchain_file_path = lambda: temp_file
            blockchain.save_blockchain()
            
            # Load in new instance
            new_blockchain = GSCBlockchain()
            new_blockchain.get_blockchain_file_path = lambda: temp_file
            loaded = new_blockchain.load_blockchain()
            
            self.assertTrue(loaded)
            self.assertEqual(len(new_blockchain.chain), 2)
            self.assertEqual(new_blockchain.get_balance("test_receiver"), 100.0)

def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestBlockchain,
        TestNetwork,
        TestRPC,
        TestSecurity,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == "__main__":
    print("GSC Coin Test Suite")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
