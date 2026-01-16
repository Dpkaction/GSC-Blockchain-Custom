#!/usr/bin/env python3
"""
Minimal Bitcoin-style P2P Node
===============================
Pure networking layer - no blockchain, mining, or wallet logic.
Just node discovery and connection like Bitcoin Core.

Features:
- TCP server + client (both modes)
- Bitcoin-style handshake (version/verack)
- Peer discovery (getaddr/addr)
- Bootstrap nodes
- Keep-alive (ping/pong)
"""

import socket
import threading
import json
import time
import random
import uuid
from typing import Set, List, Dict, Optional, Tuple

class BitcoinP2PNode:
    """Minimal Bitcoin-style P2P node - networking only"""
    
    def __init__(self, port: int = 5000, node_id: str = None):
        self.port = port
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.running = False
        
        # Peer management
        self.connected_peers: Set[str] = set()  # "ip:port"
        self.known_peers: Set[str] = set()      # All discovered peers
        self.peer_connections: Dict[str, socket.socket] = {}
        
        # Bootstrap nodes (hardcoded like Bitcoin)
        self.bootstrap_nodes = [
            "127.0.0.1:5001",  # For local testing
            "127.0.0.1:5002",
            "127.0.0.1:5003"
        ]
        
        # Threading
        self.server_thread = None
        self.ping_thread = None
        self.lock = threading.Lock()
        
        print(f"🚀 Bitcoin P2P Node initialized: {self.node_id} on port {self.port}")
    
    def start(self):
        """Start the P2P node (server + client)"""
        if self.running:
            return
            
        self.running = True
        
        # Start TCP server (accept incoming connections)
        self.server_thread = threading.Thread(target=self._start_server, daemon=True)
        self.server_thread.start()
        
        # Start ping/pong keep-alive
        self.ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
        self.ping_thread.start()
        
        # Connect to bootstrap nodes
        time.sleep(0.5)  # Let server start
        self._connect_to_bootstrap()
        
        print(f"✅ Node {self.node_id} started on port {self.port}")
    
    def stop(self):
        """Stop the P2P node"""
        self.running = False
        
        # Close all peer connections
        with self.lock:
            for peer_addr, conn in self.peer_connections.items():
                try:
                    conn.close()
                except:
                    pass
            self.peer_connections.clear()
            self.connected_peers.clear()
        
        print(f"🛑 Node {self.node_id} stopped")
    
    def _start_server(self):
        """TCP server - accept incoming peer connections"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("0.0.0.0", self.port))
            server_socket.listen(10)
            server_socket.settimeout(1.0)  # Non-blocking accept
            
            print(f"📡 Server listening on port {self.port}")
            
            while self.running:
                try:
                    conn, addr = server_socket.accept()
                    peer_addr = f"{addr[0]}:{addr[1]}"
                    print(f"📥 Incoming connection from {peer_addr}")
                    
                    # Handle peer in separate thread
                    peer_thread = threading.Thread(
                        target=self._handle_incoming_peer,
                        args=(conn, peer_addr),
                        daemon=True
                    )
                    peer_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"❌ Server error: {e}")
                    break
            
            server_socket.close()
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
    
    def _handle_incoming_peer(self, conn: socket.socket, peer_addr: str):
        """Handle incoming peer connection (server side)"""
        try:
            conn.settimeout(30.0)
            
            # Wait for version message
            data = conn.recv(4096)
            if not data:
                return
            
            message = json.loads(data.decode())
            
            if message.get("type") == "version":
                peer_node_id = message.get("node_id")
                peer_port = message.get("port", 5000)
                
                # Don't connect to self
                if peer_node_id == self.node_id:
                    conn.close()
                    return
                
                print(f"🤝 Received version from {peer_node_id} ({peer_addr})")
                
                # Send verack
                verack = {
                    "type": "verack",
                    "node_id": self.node_id,
                    "port": self.port
                }
                conn.send(json.dumps(verack).encode())
                
                # Add to connected peers
                peer_key = f"{peer_addr.split(':')[0]}:{peer_port}"
                with self.lock:
                    self.connected_peers.add(peer_key)
                    self.known_peers.add(peer_key)
                    self.peer_connections[peer_key] = conn
                
                print(f"✅ Peer connected: {peer_node_id} ({peer_key})")
                
                # Handle ongoing communication
                self._handle_peer_messages(conn, peer_key)
                
        except Exception as e:
            print(f"❌ Error handling incoming peer {peer_addr}: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
    
    def connect_to_peer(self, peer_ip: str, peer_port: int) -> bool:
        """Connect to a peer (client side)"""
        peer_addr = f"{peer_ip}:{peer_port}"
        
        # Don't connect to self
        if peer_port == self.port and peer_ip in ["127.0.0.1", "localhost"]:
            return False
        
        # Already connected?
        if peer_addr in self.connected_peers:
            return True
        
        try:
            print(f"🔗 Connecting to {peer_addr}...")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((peer_ip, peer_port))
            
            # Send version message (Bitcoin-style handshake)
            version_msg = {
                "type": "version",
                "node_id": self.node_id,
                "port": self.port
            }
            sock.send(json.dumps(version_msg).encode())
            
            # Wait for verack
            response = sock.recv(4096)
            if not response:
                sock.close()
                return False
            
            reply = json.loads(response.decode())
            
            if reply.get("type") == "verack":
                peer_node_id = reply.get("node_id")
                
                # Don't connect to self
                if peer_node_id == self.node_id:
                    sock.close()
                    return False
                
                print(f"✅ Connected to {peer_node_id} ({peer_addr})")
                
                # Add to connected peers
                with self.lock:
                    self.connected_peers.add(peer_addr)
                    self.known_peers.add(peer_addr)
                    self.peer_connections[peer_addr] = sock
                
                # Handle ongoing communication
                peer_thread = threading.Thread(
                    target=self._handle_peer_messages,
                    args=(sock, peer_addr),
                    daemon=True
                )
                peer_thread.start()
                
                # Request peer addresses
                self._request_peer_addresses(peer_addr)
                
                return True
            else:
                print(f"❌ Invalid handshake response from {peer_addr}")
                sock.close()
                return False
                
        except Exception as e:
            print(f"❌ Failed to connect to {peer_addr}: {e}")
            return False
    
    def _handle_peer_messages(self, conn: socket.socket, peer_addr: str):
        """Handle ongoing communication with a peer"""
        try:
            while self.running and peer_addr in self.connected_peers:
                try:
                    conn.settimeout(60.0)  # 1 minute timeout
                    data = conn.recv(4096)
                    
                    if not data:
                        break
                    
                    message = json.loads(data.decode())
                    response = self._process_message(message, peer_addr)
                    
                    if response:
                        conn.send(json.dumps(response).encode())
                        
                except socket.timeout:
                    # Send ping to check if peer is alive
                    try:
                        ping_msg = {"type": "ping", "node_id": self.node_id}
                        conn.send(json.dumps(ping_msg).encode())
                    except:
                        break
                except Exception as e:
                    print(f"❌ Error with peer {peer_addr}: {e}")
                    break
        
        except Exception as e:
            print(f"❌ Peer handler error {peer_addr}: {e}")
        finally:
            # Clean up disconnected peer
            with self.lock:
                self.connected_peers.discard(peer_addr)
                if peer_addr in self.peer_connections:
                    del self.peer_connections[peer_addr]
            
            try:
                conn.close()
            except:
                pass
            
            print(f"📤 Peer disconnected: {peer_addr}")
    
    def _process_message(self, message: dict, peer_addr: str) -> Optional[dict]:
        """Process incoming message from peer"""
        msg_type = message.get("type")
        
        if msg_type == "ping":
            # Respond to ping with pong
            return {"type": "pong", "node_id": self.node_id}
        
        elif msg_type == "pong":
            # Peer is alive
            pass
        
        elif msg_type == "getaddr":
            # Send known peer addresses
            peer_list = list(self.known_peers - {peer_addr})[:10]  # Max 10 peers
            return {
                "type": "addr",
                "peers": peer_list,
                "count": len(peer_list)
            }
        
        elif msg_type == "addr":
            # Received peer addresses
            peers = message.get("peers", [])
            print(f"📋 Received {len(peers)} peer addresses from {peer_addr}")
            
            with self.lock:
                for peer in peers:
                    self.known_peers.add(peer)
            
            # Try connecting to some new peers
            self._connect_to_random_peers()
        
        return None
    
    def _request_peer_addresses(self, peer_addr: str):
        """Request peer addresses from a connected peer"""
        try:
            if peer_addr in self.peer_connections:
                getaddr_msg = {"type": "getaddr", "node_id": self.node_id}
                self.peer_connections[peer_addr].send(json.dumps(getaddr_msg).encode())
        except Exception as e:
            print(f"❌ Failed to request addresses from {peer_addr}: {e}")
    
    def _connect_to_bootstrap(self):
        """Connect to bootstrap nodes"""
        print("🌱 Connecting to bootstrap nodes...")
        
        for bootstrap in self.bootstrap_nodes:
            if not self.running:
                break
                
            try:
                ip, port = bootstrap.split(":")
                if self.connect_to_peer(ip, int(port)):
                    print(f"✅ Connected to bootstrap: {bootstrap}")
                    time.sleep(0.5)  # Stagger connections
            except Exception as e:
                print(f"❌ Failed to connect to bootstrap {bootstrap}: {e}")
    
    def _connect_to_random_peers(self):
        """Connect to random peers from known peer list"""
        if len(self.connected_peers) >= 8:  # Bitcoin default max connections
            return
        
        available_peers = list(self.known_peers - self.connected_peers)
        if not available_peers:
            return
        
        # Try connecting to 1-2 random peers
        peers_to_try = random.sample(available_peers, min(2, len(available_peers)))
        
        for peer_addr in peers_to_try:
            if not self.running or len(self.connected_peers) >= 8:
                break
                
            try:
                ip, port = peer_addr.split(":")
                self.connect_to_peer(ip, int(port))
                time.sleep(1.0)  # Stagger connections
            except Exception as e:
                print(f"❌ Failed to connect to peer {peer_addr}: {e}")
    
    def _ping_loop(self):
        """Send periodic pings to keep connections alive"""
        while self.running:
            time.sleep(30)  # Ping every 30 seconds
            
            if not self.running:
                break
            
            peers_to_ping = list(self.connected_peers)
            for peer_addr in peers_to_ping:
                try:
                    if peer_addr in self.peer_connections:
                        ping_msg = {"type": "ping", "node_id": self.node_id}
                        self.peer_connections[peer_addr].send(json.dumps(ping_msg).encode())
                except Exception as e:
                    print(f"❌ Failed to ping {peer_addr}: {e}")
    
    def get_status(self) -> dict:
        """Get node status"""
        return {
            "node_id": self.node_id,
            "port": self.port,
            "running": self.running,
            "connected_peers": len(self.connected_peers),
            "known_peers": len(self.known_peers),
            "peer_list": list(self.connected_peers)
        }
    
    def manual_connect(self, ip: str, port: int) -> bool:
        """Manually connect to a specific peer"""
        return self.connect_to_peer(ip, port)


def main():
    """Test the Bitcoin P2P node"""
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    
    node = BitcoinP2PNode(port=port)
    node.start()
    
    try:
        print(f"\n🎯 Bitcoin P2P Node running on port {port}")
        print("Commands:")
        print("  status  - Show node status")
        print("  connect <ip> <port> - Connect to peer")
        print("  quit    - Exit")
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
                    ip, port = cmd[1], int(cmd[2])
                    if node.manual_connect(ip, port):
                        print(f"✅ Connected to {ip}:{port}")
                    else:
                        print(f"❌ Failed to connect to {ip}:{port}")
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    finally:
        node.stop()
        print("👋 Goodbye!")


if __name__ == "__main__":
    main()
