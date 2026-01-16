#!/usr/bin/env python3
"""
Test Bitcoin Sync Pipeline
==========================
Test the complete Bitcoin-style sync process
"""

import time
import threading
from bitcoin_sync_node import BitcoinSyncNode

def test_headers_first_sync():
    """Test headers-first sync between two nodes"""
    print("🧪 Testing Headers-First Sync")
    print("=" * 50)
    
    # Create two nodes
    node1 = BitcoinSyncNode(port=5000)  # Will have test data
    node2 = BitcoinSyncNode(port=5001)  # Will sync from node1
    
    try:
        # Start both nodes
        print("Starting nodes...")
        node1.start()
        time.sleep(1)
        
        # Add test data to node1
        node1.add_test_data()
        print(f"Node1 has {len(node1.best_chain)} blocks")
        
        node2.start()
        time.sleep(2)
        
        # Connect node2 to node1 and start sync
        print("Connecting and starting sync...")
        success = node2.connect_to_peer("127.0.0.1", 5000)
        
        if success:
            print("✅ Connection successful!")
            time.sleep(1)
            
            # Start sync
            node2.start_headers_sync("127.0.0.1:5000")
            
            # Monitor sync progress
            print("\nMonitoring sync progress...")
            for i in range(20):  # Wait up to 20 seconds
                status1 = node1.get_sync_status()
                status2 = node2.get_sync_status()
                
                print(f"Node1: {status1['sync_mode']} | Height: {status1['chain_height']} | Blocks: {status1['blocks_count']}")
                print(f"Node2: {status2['sync_mode']} | Height: {status2['chain_height']} | Blocks: {status2['blocks_count']} | Missing: {status2['missing_blocks']}")
                print(f"Node2 syncing with: {status2['syncing_with']}")
                print("-" * 40)
                
                if status2['sync_mode'] == 'live' and status2['missing_blocks'] == 0:
                    print("🎉 Sync completed successfully!")
                    break
                
                time.sleep(1)
            
            # Final status
            final_status1 = node1.get_sync_status()
            final_status2 = node2.get_sync_status()
            
            print("\nFinal Status:")
            print(f"Node1: Height {final_status1['chain_height']}, {final_status1['blocks_count']} blocks, {final_status1['mempool_size']} mempool")
            print(f"Node2: Height {final_status2['chain_height']}, {final_status2['blocks_count']} blocks, {final_status2['mempool_size']} mempool")
            
            if (final_status1['chain_height'] == final_status2['chain_height'] and 
                final_status1['blocks_count'] == final_status2['blocks_count']):
                print("✅ Sync test PASSED - Blockchains match!")
            else:
                print("❌ Sync test FAILED - Blockchains don't match")
        else:
            print("❌ Connection failed!")
        
    finally:
        print("\nStopping nodes...")
        node1.stop()
        node2.stop()
        time.sleep(1)

def test_multi_node_sync():
    """Test sync with multiple nodes"""
    print("\n🧪 Testing Multi-Node Sync")
    print("=" * 50)
    
    # Create 3 nodes
    nodes = []
    for i in range(3):
        port = 5000 + i
        node = BitcoinSyncNode(port=port)
        nodes.append(node)
    
    try:
        # Start all nodes
        print("Starting 3 nodes...")
        for i, node in enumerate(nodes):
            node.start()
            time.sleep(0.5)
            print(f"  Node {i+1} started on port {5000+i}")
        
        time.sleep(1)
        
        # Add test data to first node only
        nodes[0].add_test_data()
        print(f"Node1 has {len(nodes[0].best_chain)} blocks with test data")
        
        # Connect nodes: 2->1, 3->1
        print("\nConnecting nodes to node1...")
        nodes[1].connect_to_peer("127.0.0.1", 5000)
        time.sleep(1)
        nodes[2].connect_to_peer("127.0.0.1", 5000)
        time.sleep(1)
        
        # Start sync on both nodes
        print("Starting sync on node2 and node3...")
        nodes[1].start_headers_sync("127.0.0.1:5000")
        time.sleep(1)
        nodes[2].start_headers_sync("127.0.0.1:5000")
        
        # Monitor all nodes
        print("\nMonitoring multi-node sync...")
        for i in range(15):
            print(f"\n--- Sync Progress (t={i+1}s) ---")
            for j, node in enumerate(nodes):
                status = node.get_sync_status()
                print(f"Node{j+1}: {status['sync_mode']} | H:{status['chain_height']} | B:{status['blocks_count']} | M:{status['missing_blocks']} | MP:{status['mempool_size']}")
            
            # Check if all synced
            all_synced = all(
                node.get_sync_status()['sync_mode'] == 'live' and 
                node.get_sync_status()['missing_blocks'] == 0 
                for node in nodes[1:]  # Skip node1 as it's the source
            )
            
            if all_synced:
                print("🎉 All nodes synced!")
                break
            
            time.sleep(1)
        
        # Final verification
        print("\nFinal Multi-Node Status:")
        statuses = [node.get_sync_status() for node in nodes]
        
        for i, status in enumerate(statuses):
            print(f"Node{i+1}: Height {status['chain_height']}, {status['blocks_count']} blocks, {status['mempool_size']} mempool")
        
        # Check if all match
        heights = [s['chain_height'] for s in statuses]
        blocks = [s['blocks_count'] for s in statuses]
        
        if len(set(heights)) == 1 and len(set(blocks)) == 1:
            print("✅ Multi-node sync PASSED - All blockchains match!")
        else:
            print("❌ Multi-node sync FAILED - Blockchains don't match")
        
    finally:
        print("\nStopping all nodes...")
        for node in nodes:
            node.stop()
        time.sleep(1)

def test_sync_phases():
    """Test individual sync phases"""
    print("\n🧪 Testing Individual Sync Phases")
    print("=" * 50)
    
    node1 = BitcoinSyncNode(port=5000)
    node2 = BitcoinSyncNode(port=5001)
    
    try:
        # Start nodes
        node1.start()
        node1.add_test_data()
        time.sleep(1)
        
        node2.start()
        time.sleep(1)
        
        # Connect
        node2.connect_to_peer("127.0.0.1", 5000)
        time.sleep(1)
        
        print("📥 PHASE 1: Testing Headers Sync...")
        node2.sync_mode = "headers"
        node2._request_headers("127.0.0.1:5000", node2.genesis_hash)
        
        # Wait for headers
        for i in range(5):
            status = node2.get_sync_status()
            print(f"  Headers: {status['headers_count']}")
            if status['headers_count'] > 1:
                print("  ✅ Headers received!")
                break
            time.sleep(1)
        
        print("\n📋 PHASE 2: Testing Block Inventory...")
        node2.sync_mode = "blocks"
        node2._request_block_inventory("127.0.0.1:5000", node2.genesis_hash)
        
        time.sleep(2)
        
        print("\n📦 PHASE 3: Testing Block Download...")
        # Should happen automatically after inventory
        
        for i in range(10):
            status = node2.get_sync_status()
            print(f"  Blocks: {status['blocks_count']}, Missing: {status['missing_blocks']}")
            if status['missing_blocks'] == 0:
                print("  ✅ All blocks downloaded!")
                break
            time.sleep(1)
        
        print("\n💼 PHASE 5: Testing Mempool Sync...")
        node2._start_mempool_sync("127.0.0.1:5000")
        
        time.sleep(3)
        
        final_status = node2.get_sync_status()
        print(f"\nFinal: Mode={final_status['sync_mode']}, Mempool={final_status['mempool_size']}")
        
        if final_status['sync_mode'] == 'live':
            print("✅ All sync phases completed successfully!")
        else:
            print("❌ Sync phases test incomplete")
        
    finally:
        node1.stop()
        node2.stop()

def interactive_sync_test():
    """Interactive sync testing"""
    print("\n🧪 Interactive Sync Test")
    print("=" * 50)
    print("This will start two nodes for manual sync testing.")
    print("Node1 (5000) will have test data.")
    print("Node2 (5001) will sync from Node1.")
    print()
    
    node1 = BitcoinSyncNode(port=5000)
    node2 = BitcoinSyncNode(port=5001)
    
    try:
        # Start node1 with data
        node1.start()
        node1.add_test_data()
        print(f"Node1 started with {len(node1.best_chain)} blocks")
        
        # Start node2
        node2.start()
        print("Node2 started (empty)")
        
        print("\nCommands:")
        print("  connect - Connect node2 to node1")
        print("  sync - Start full sync")
        print("  status - Show both nodes status")
        print("  headers - Test headers sync only")
        print("  blocks - Test blocks sync only")
        print("  mempool - Test mempool sync only")
        print("  quit - Exit")
        print()
        
        while True:
            try:
                cmd = input("sync-test> ").strip()
                
                if cmd == "quit":
                    break
                elif cmd == "connect":
                    if node2.connect_to_peer("127.0.0.1", 5000):
                        print("✅ Connected!")
                    else:
                        print("❌ Connection failed!")
                elif cmd == "sync":
                    node2.start_headers_sync("127.0.0.1:5000")
                    print("🔄 Full sync started")
                elif cmd == "status":
                    status1 = node1.get_sync_status()
                    status2 = node2.get_sync_status()
                    print(f"Node1: {status1['sync_mode']} | H:{status1['chain_height']} | B:{status1['blocks_count']} | MP:{status1['mempool_size']}")
                    print(f"Node2: {status2['sync_mode']} | H:{status2['chain_height']} | B:{status2['blocks_count']} | M:{status2['missing_blocks']} | MP:{status2['mempool_size']}")
                elif cmd == "headers":
                    node2._request_headers("127.0.0.1:5000", node2.genesis_hash)
                    print("📥 Headers sync requested")
                elif cmd == "blocks":
                    node2._start_blocks_sync("127.0.0.1:5000")
                    print("📦 Blocks sync started")
                elif cmd == "mempool":
                    node2._start_mempool_sync("127.0.0.1:5000")
                    print("💼 Mempool sync started")
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    finally:
        node1.stop()
        node2.stop()
        print("Nodes stopped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_sync_test()
    else:
        # Run automated tests
        test_headers_first_sync()
        test_multi_node_sync()
        test_sync_phases()
        
        print("\n🎉 All Bitcoin sync tests completed!")
        print("\nTo test manually:")
        print("  python test_bitcoin_sync.py interactive")
        print("  python bitcoin_sync_gui.py")
