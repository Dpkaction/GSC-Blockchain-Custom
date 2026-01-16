#!/usr/bin/env python3
"""
Test Bitcoin P2P Network
========================
Test script to demonstrate pure Bitcoin-style P2P networking
"""

import time
import threading
from bitcoin_p2p_node import BitcoinP2PNode

def test_basic_connection():
    """Test basic peer-to-peer connection"""
    print("🧪 Testing Basic P2P Connection")
    print("=" * 50)
    
    # Create two nodes
    node1 = BitcoinP2PNode(port=5000)
    node2 = BitcoinP2PNode(port=5001)
    
    try:
        # Start both nodes
        print("Starting nodes...")
        node1.start()
        time.sleep(1)
        node2.start()
        time.sleep(2)
        
        # Connect node2 to node1
        print("Connecting node2 to node1...")
        success = node2.connect_to_peer("127.0.0.1", 5000)
        
        if success:
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
        
        time.sleep(3)
        
        # Check status
        status1 = node1.get_status()
        status2 = node2.get_status()
        
        print(f"\nNode 1 Status:")
        print(f"  Connected Peers: {status1['connected_peers']}")
        print(f"  Known Peers: {status1['known_peers']}")
        print(f"  Peer List: {status1['peer_list']}")
        
        print(f"\nNode 2 Status:")
        print(f"  Connected Peers: {status2['connected_peers']}")
        print(f"  Known Peers: {status2['known_peers']}")
        print(f"  Peer List: {status2['peer_list']}")
        
        # Test peer discovery
        print("\nTesting peer discovery...")
        time.sleep(5)  # Wait for peer discovery
        
        status1 = node1.get_status()
        status2 = node2.get_status()
        
        print(f"After discovery - Node 1 known peers: {status1['known_peers']}")
        print(f"After discovery - Node 2 known peers: {status2['known_peers']}")
        
    finally:
        print("\nStopping nodes...")
        node1.stop()
        node2.stop()
        time.sleep(1)

def test_multi_node_network():
    """Test multi-node network with peer discovery"""
    print("\n🧪 Testing Multi-Node Network")
    print("=" * 50)
    
    # Create 4 nodes
    nodes = []
    for i in range(4):
        port = 5000 + i
        node = BitcoinP2PNode(port=port)
        nodes.append(node)
    
    try:
        # Start all nodes
        print("Starting 4 nodes...")
        for i, node in enumerate(nodes):
            node.start()
            time.sleep(0.5)
            print(f"  Node {i+1} started on port {5000+i}")
        
        time.sleep(2)
        
        # Connect nodes in chain: 1->2->3->4
        print("\nConnecting nodes in chain...")
        nodes[1].connect_to_peer("127.0.0.1", 5000)  # 2->1
        time.sleep(1)
        nodes[2].connect_to_peer("127.0.0.1", 5001)  # 3->2
        time.sleep(1)
        nodes[3].connect_to_peer("127.0.0.1", 5002)  # 4->3
        
        time.sleep(3)
        
        # Check initial connections
        print("\nInitial connections:")
        for i, node in enumerate(nodes):
            status = node.get_status()
            print(f"  Node {i+1}: {status['connected_peers']} connected, {status['known_peers']} known")
        
        # Wait for peer discovery to propagate
        print("\nWaiting for peer discovery...")
        time.sleep(10)
        
        # Check final network state
        print("\nFinal network state:")
        for i, node in enumerate(nodes):
            status = node.get_status()
            print(f"  Node {i+1} ({node.node_id}):")
            print(f"    Connected: {status['connected_peers']}")
            print(f"    Known: {status['known_peers']}")
            print(f"    Peers: {status['peer_list']}")
            print()
        
    finally:
        print("Stopping all nodes...")
        for node in nodes:
            node.stop()
        time.sleep(1)

def interactive_test():
    """Interactive test mode"""
    print("\n🧪 Interactive Test Mode")
    print("=" * 50)
    print("This will start a node that you can control manually.")
    print("Open another terminal and run:")
    print("  python test_p2p_network.py")
    print("Or use the GUI:")
    print("  python p2p_node_gui.py")
    print()
    
    port = 5000
    node = BitcoinP2PNode(port=port)
    
    try:
        node.start()
        print(f"Node started on port {port}")
        print("Commands:")
        print("  status - Show node status")
        print("  connect <ip> <port> - Connect to peer")
        print("  quit - Exit")
        print()
        
        while True:
            try:
                cmd = input(f"node-{node.node_id}> ").strip().split()
                
                if not cmd:
                    continue
                
                if cmd[0] == "quit":
                    break
                elif cmd[0] == "status":
                    status = node.get_status()
                    print(f"Node ID: {status['node_id']}")
                    print(f"Port: {status['port']}")
                    print(f"Connected Peers: {status['connected_peers']}")
                    print(f"Known Peers: {status['known_peers']}")
                    print(f"Peer List: {status['peer_list']}")
                elif cmd[0] == "connect" and len(cmd) == 3:
                    ip, port_str = cmd[1], cmd[2]
                    if node.manual_connect(ip, int(port_str)):
                        print(f"✅ Connected to {ip}:{port_str}")
                    else:
                        print(f"❌ Failed to connect to {ip}:{port_str}")
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    finally:
        node.stop()
        print("Node stopped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        # Run automated tests
        test_basic_connection()
        test_multi_node_network()
        
        print("\n🎉 All tests completed!")
        print("\nTo test manually:")
        print("  python test_p2p_network.py interactive")
        print("  python p2p_node_gui.py")
