#!/usr/bin/env python3
"""
GSC Coin Integration Script
Easy deployment and testing of improved GSC Blockchain
"""

import os
import sys
import time
import json
import argparse
import threading
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'hashlib', 'json', 'time', 'threading', 'socket',
        'http.server', 'urllib.parse', 'datetime', 'dataclasses',
        'typing', 'unittest', 'tempfile', 'logging'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Missing required modules: {missing}")
        return False
    
    print("✅ All required modules available")
    return True

def backup_existing_files():
    """Backup existing files before upgrade"""
    files_to_backup = [
        'blockchain.py',
        'network.py', 
        'gsc_blockchain.json',
        'wallets/'
    ]
    
    backup_dir = f"backup_{int(time.time())}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                import shutil
                shutil.copytree(file_path, os.path.join(backup_dir, file_path))
            else:
                import shutil
                shutil.copy2(file_path, backup_dir)
            print(f"✅ Backed up {file_path}")
    
    return backup_dir

def deploy_improved_components():
    """Deploy improved components"""
    deployments = [
        ('blockchain_improved.py', 'blockchain.py'),
        ('network_improved.py', 'network.py'),
        ('rpc_server_improved.py', 'rpc_server.py')
    ]
    
    for source, target in deployments:
        if os.path.exists(source):
            import shutil
            shutil.copy2(source, target)
            print(f"✅ Deployed {source} -> {target}")
        else:
            print(f"❌ Source file not found: {source}")
            return False
    
    return True

def run_tests():
    """Run comprehensive test suite"""
    print("\n🧪 Running comprehensive test suite...")
    
    try:
        # Import and run tests
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Test basic imports
        print("Testing imports...")
        from blockchain_improved import GSCBlockchain, Transaction, Block
        from network_improved import GSCNetworkNode, MessageValidator
        from rpc_server_improved import GSCRPCServer
        from gsc_logger import blockchain_logger, network_logger, rpc_logger
        from thread_safety import ThreadSafeList, ThreadSafeDict
        print("✅ All imports successful")
        
        # Test blockchain functionality
        print("Testing blockchain...")
        blockchain = GSCBlockchain()
        assert len(blockchain.chain) == 1, "Genesis block should exist"
        assert blockchain.get_balance("GSC_FOUNDATION_RESERVE") > 0, "Foundation should have balance"
        print("✅ Blockchain tests passed")
        
        # Test transaction creation
        print("Testing transactions...")
        tx = Transaction(
            sender="GSC_FOUNDATION_RESERVE",
            receiver="test_address",
            amount=10.0,
            fee=0.1,
            timestamp=time.time()
        )
        assert tx.is_valid(), "Transaction should be valid"
        assert blockchain.add_transaction_to_mempool(tx), "Should add to mempool"
        print("✅ Transaction tests passed")
        
        # Test mining
        print("Testing mining...")
        block = blockchain.mine_pending_transactions("test_miner")
        assert block is not None, "Should mine block successfully"
        assert block.index == 1, "Block should have index 1"
        print("✅ Mining tests passed")
        
        # Test network components
        print("Testing network...")
        validator = MessageValidator()
        valid_msg = {'type': 'version', 'version': 1, 'node_id': 'test'}
        assert validator.validate_message(valid_msg) is None, "Valid message should pass"
        print("✅ Network tests passed")
        
        print("🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_demo_node():
    """Start a demonstration node"""
    print("\n🚀 Starting demonstration node...")
    
    try:
        from blockchain_improved import GSCBlockchain
        from network_improved import GSCNetworkNode
        from rpc_server_improved import GSCRPCServer
        from wallet_manager import WalletManager
        
        # Initialize components
        print("Initializing blockchain...")
        blockchain = GSCBlockchain()
        
        print("Initializing network node...")
        network = GSCNetworkNode(blockchain, port=18444)  # Test port
        
        print("Initializing wallet manager...")
        wallet_manager = WalletManager()
        
        print("Starting RPC server...")
        rpc = GSCRPCServer(blockchain, wallet_manager, host='127.0.0.1', port=18332)
        
        # Start services
        if network.start_server():
            print("✅ Network node started on port 18444")
        
        if rpc.start():
            print("✅ RPC server started on http://127.0.0.1:18332")
        
        # Create a test wallet
        print("Creating test wallet...")
        wallet_info = wallet_manager.create_wallet("demo_wallet")
        print(f"✅ Created wallet: {wallet_info['address']}")
        
        # Mine a few blocks
        print("Mining demo blocks...")
        for i in range(3):
            tx = Transaction(
                sender="GSC_FOUNDATION_RESERVE",
                receiver=wallet_info['address'],
                amount=25.0,
                fee=0.1,
                timestamp=time.time()
            )
            blockchain.add_transaction_to_mempool(tx)
            
            block = blockchain.mine_pending_transactions("demo_miner")
            if block:
                print(f"✅ Mined block {block.index}")
        
        # Show final state
        balance = blockchain.get_balance(wallet_info['address'])
        print(f"✅ Demo wallet balance: {balance} GSC")
        
        print("\n🎉 Demo node is running!")
        print("RPC API available at: http://127.0.0.1:18332")
        print("Try: curl -X POST -H 'Content-Type: application/json' \\")
        print("  -d '{\"jsonrpc\":\"2.0\",\"method\":\"getblockchaininfo\",\"id\":1}' \\")
        print("  http://127.0.0.1:18332/")
        
        print("\nPress Ctrl+C to stop...")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            rpc.stop()
            network.stop_server()
            print("✅ Shutdown complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to start demo node: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_rpc_demo():
    """Run RPC demonstration"""
    print("\n🔌 Running RPC demonstration...")
    
    try:
        import requests
        import json
        
        # Test RPC methods
        rpc_url = "http://127.0.0.1:18332"
        
        tests = [
            ("Blockchain Info", {"jsonrpc":"2.0","method":"getblockchaininfo","id":1}),
            ("Block Count", {"jsonrpc":"2.0","method":"getblockcount","id":2}),
            ("Network Info", {"jsonrpc":"2.0","method":"getnetworkinfo","id":3}),
            ("Mining Info", {"jsonrpc":"2.0","method":"getmininginfo","id":4}),
            ("Mempool Info", {"jsonrpc":"2.0","method":"getmempoolinfo","id":5}),
        ]
        
        for test_name, payload in tests:
            try:
                response = requests.post(rpc_url, json=payload, timeout=5)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {test_name}: {json.dumps(result.get('result', {}), indent=2)}")
                else:
                    print(f"❌ {test_name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {test_name}: {e}")
        
        return True
        
    except ImportError:
        print("❌ requests module not available. Install with: pip install requests")
        return False
    except Exception as e:
        print(f"❌ RPC demo failed: {e}")
        return False

def show_status():
    """Show current system status"""
    print("\n📊 GSC Coin System Status")
    print("=" * 50)
    
    # Check files
    files = [
        ('blockchain_improved.py', 'Improved Blockchain Core'),
        ('network_improved.py', 'Improved Network Layer'),
        ('rpc_server_improved.py', 'Improved RPC Server'),
        ('gsc_logger.py', 'Logging System'),
        ('thread_safety.py', 'Thread Safety Utilities'),
        ('tests.py', 'Test Suite'),
        ('P2P_NETWORKING.md', 'Network Documentation'),
        ('IMPROVEMENT_SUMMARY.md', 'Improvement Summary')
    ]
    
    print("📁 Files Status:")
    for filename, description in files:
        status = "✅" if os.path.exists(filename) else "❌"
        print(f"  {status} {filename} - {description}")
    
    # Check backup
    backup_dirs = [d for d in os.listdir('.') if d.startswith('backup_')]
    if backup_dirs:
        print(f"\n💾 Backups: {len(backup_dirs)} backup(s) found")
    
    # Check logs
    if os.path.exists('logs'):
        log_files = os.listdir('logs')
        print(f"📝 Logs: {len(log_files)} log file(s)")
    
    print("\n🎯 Next Steps:")
    print("1. Run tests: python integration_script.py --test")
    print("2. Start demo: python integration_script.py --demo")
    print("3. View docs: cat P2P_NETWORKING.md")
    print("4. Read summary: cat IMPROVEMENT_SUMMARY.md")

def main():
    """Main integration script"""
    parser = argparse.ArgumentParser(description='GSC Coin Integration Script')
    parser.add_argument('--check', action='store_true', help='Check dependencies')
    parser.add_argument('--backup', action='store_true', help='Backup existing files')
    parser.add_argument('--deploy', action='store_true', help='Deploy improved components')
    parser.add_argument('--test', action='store_true', help='Run tests')
    parser.add_argument('--demo', action='store_true', help='Start demo node')
    parser.add_argument('--rpc-demo', action='store_true', help='Run RPC demo')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--all', action='store_true', help='Run full integration')
    
    args = parser.parse_args()
    
    print("🪙 GSC Coin Integration Script")
    print("=" * 50)
    
    # Show status by default
    if not any(vars(args).values()):
        args.status = True
    
    if args.status:
        show_status()
        return
    
    if args.check:
        if not check_dependencies():
            sys.exit(1)
    
    if args.backup:
        backup_dir = backup_existing_files()
        print(f"📦 Files backed up to: {backup_dir}")
    
    if args.deploy:
        if not deploy_improved_components():
            print("❌ Deployment failed")
            sys.exit(1)
    
    if args.test:
        if not run_tests():
            print("❌ Tests failed")
            sys.exit(1)
    
    if args.demo:
        if not start_demo_node():
            print("❌ Demo failed")
            sys.exit(1)
    
    if args.rpc_demo:
        if not run_rpc_demo():
            print("❌ RPC demo failed")
            sys.exit(1)
    
    if args.all:
        print("🚀 Running full integration...")
        
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Backup files
        backup_dir = backup_existing_files()
        print(f"📦 Files backed up to: {backup_dir}")
        
        # Deploy components
        if not deploy_improved_components():
            print("❌ Deployment failed")
            sys.exit(1)
        
        # Run tests
        if not run_tests():
            print("❌ Tests failed")
            sys.exit(1)
        
        # Start demo
        if not start_demo_node():
            print("❌ Demo failed")
            sys.exit(1)
    
    print("\n✅ Integration completed successfully!")

if __name__ == "__main__":
    main()
