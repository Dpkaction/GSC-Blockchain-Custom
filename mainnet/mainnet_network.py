"""
GSC Coin Mainnet P2P Network Implementation
Production-ready networking with enhanced security and reliability
"""

import socket
import threading
import json
import time
import hashlib
import logging
import ssl
import select
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
import struct
import zlib
from .config import Config
from .mainnet_blockchain import MainnetBlockchain, MainnetTransaction, MainnetBlock

logger = logging.getLogger(__name__)

class NetworkMessage:
    """Network message protocol for GSC mainnet"""
    
    # Message types
    VERSION = "version"
    VERACK = "verack"
    PING = "ping"
    PONG = "pong"
    GETBLOCKS = "getblocks"
    BLOCKS = "blocks"
    GETTX = "gettx"
    TX = "tx"
    MEMPOOL = "mempool"
    PEERS = "peers"
    DISCONNECT = "disconnect"
    
    def __init__(self, msg_type: str, payload: dict = None):
        self.type = msg_type
        self.payload = payload or {}
        self.timestamp = time.time()
        self.checksum = self.calculate_checksum()
    
    def calculate_checksum(self) -> str:
        """Calculate message checksum for integrity"""
        data = json.dumps({
            'type': self.type,
            'payload': self.payload,
            'timestamp': self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:8]
    
    def to_bytes(self) -> bytes:
        """Serialize message to bytes with compression"""
        data = {
            'type': self.type,
            'payload': self.payload,
            'timestamp': self.timestamp,
            'checksum': self.checksum
        }
        json_data = json.dumps(data).encode('utf-8')
        compressed = zlib.compress(json_data)
        
        # Add length prefix
        length = struct.pack('!I', len(compressed))
        return length + compressed
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'NetworkMessage':
        """Deserialize message from bytes"""
        try:
            decompressed = zlib.decompress(data)
            msg_data = json.loads(decompressed.decode('utf-8'))
            
            msg = cls(msg_data['type'], msg_data['payload'])
            msg.timestamp = msg_data['timestamp']
            
            # Verify checksum
            if msg.checksum != msg_data['checksum']:
                raise ValueError("Invalid message checksum")
            
            return msg
        except Exception as e:
            logger.error(f"Failed to deserialize message: {e}")
            raise

class PeerConnection:
    """Represents a connection to a peer node"""
    
    def __init__(self, socket_conn: socket.socket, address: Tuple[str, int], is_outbound: bool = False):
        self.socket = socket_conn
        self.address = address
        self.is_outbound = is_outbound
        self.connected_at = time.time()
        self.last_ping = 0
        self.last_pong = 0
        self.version = None
        self.user_agent = None
        self.services = 0
        self.height = 0
        self.relay = True
        self.bytes_sent = 0
        self.bytes_received = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.lock = threading.Lock()
        self.send_queue = []
        self.is_alive = True
    
    def send_message(self, message: NetworkMessage) -> bool:
        """Send message to peer"""
        try:
            with self.lock:
                if not self.is_alive:
                    return False
                
                data = message.to_bytes()
                self.socket.sendall(data)
                self.bytes_sent += len(data)
                self.messages_sent += 1
                return True
        except Exception as e:
            logger.error(f"Failed to send message to {self.address}: {e}")
            self.disconnect()
            return False
    
    def receive_message(self) -> Optional[NetworkMessage]:
        """Receive message from peer"""
        try:
            # Read length prefix
            length_data = self._recv_exact(4)
            if not length_data:
                return None
            
            length = struct.unpack('!I', length_data)[0]
            if length > 10 * 1024 * 1024:  # 10MB max message size
                raise ValueError("Message too large")
            
            # Read message data
            msg_data = self._recv_exact(length)
            if not msg_data:
                return None
            
            message = NetworkMessage.from_bytes(msg_data)
            self.bytes_received += len(length_data) + len(msg_data)
            self.messages_received += 1
            
            return message
        except Exception as e:
            logger.error(f"Failed to receive message from {self.address}: {e}")
            self.disconnect()
            return None
    
    def _recv_exact(self, size: int) -> bytes:
        """Receive exact number of bytes"""
        data = b''
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data
    
    def ping(self):
        """Send ping to peer"""
        self.last_ping = time.time()
        ping_msg = NetworkMessage(NetworkMessage.PING, {'timestamp': self.last_ping})
        return self.send_message(ping_msg)
    
    def pong(self, ping_timestamp: float):
        """Send pong response"""
        pong_msg = NetworkMessage(NetworkMessage.PONG, {'ping_timestamp': ping_timestamp})
        return self.send_message(pong_msg)
    
    def disconnect(self):
        """Disconnect from peer"""
        self.is_alive = False
        try:
            self.socket.close()
        except:
            pass
    
    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            'address': f"{self.address[0]}:{self.address[1]}",
            'connected_at': self.connected_at,
            'uptime': time.time() - self.connected_at,
            'is_outbound': self.is_outbound,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'last_ping': self.last_ping,
            'last_pong': self.last_pong,
            'version': self.version,
            'height': self.height
        }

class MainnetNetworkNode:
    """Production-ready P2P network node for GSC mainnet"""
    
    def __init__(self, blockchain: MainnetBlockchain, port: int = None):
        self.blockchain = blockchain
        self.port = port or Config.DEFAULT_PORT
        self.node_id = self.generate_node_id()
        self.version = 1
        self.user_agent = f"GSC-Core:1.0.0"
        self.services = 1  # NODE_NETWORK
        
        # Network state
        self.peers: Dict[str, PeerConnection] = {}
        self.banned_peers: Set[str] = set()
        self.known_nodes: Set[str] = set()
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        
        # Threading
        self.lock = threading.RLock()
        self.threads: List[threading.Thread] = []
        
        # Network statistics
        self.stats = {
            'connections_made': 0,
            'connections_received': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'blocks_synced': 0,
            'transactions_relayed': 0,
            'start_time': time.time()
        }
        
        # Load known nodes from config
        for seed in Config.SEED_NODES:
            if ':' in seed:
                host, port = seed.split(':')
                self.known_nodes.add(f"{host}:{port}")
            else:
                self.known_nodes.add(f"{seed}:{Config.DEFAULT_PORT}")
    
    def generate_node_id(self) -> str:
        """Generate unique node ID"""
        node_data = f"{socket.gethostname()}{time.time()}{Config.NETWORK_NAME}"
        return hashlib.sha256(node_data.encode()).hexdigest()[:16]
    
    def start(self):
        """Start the network node"""
        if self.running:
            return
        
        self.running = True
        logger.info(f"Starting GSC mainnet node on port {self.port}")
        
        # Start server thread
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()
        self.threads.append(server_thread)
        
        # Start maintenance thread
        maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        maintenance_thread.start()
        self.threads.append(maintenance_thread)
        
        # Connect to seed nodes
        self._connect_to_seeds()
    
    def stop(self):
        """Stop the network node"""
        if not self.running:
            return
        
        logger.info("Stopping GSC mainnet node")
        self.running = False
        
        # Disconnect all peers
        with self.lock:
            for peer in list(self.peers.values()):
                peer.disconnect()
            self.peers.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
    
    def _run_server(self):
        """Run the P2P server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(Config.MAX_INBOUND_CONNECTIONS)
            
            logger.info(f"P2P server listening on port {self.port}")
            
            while self.running:
                try:
                    # Use select for non-blocking accept
                    ready, _, _ = select.select([self.server_socket], [], [], 1.0)
                    if ready:
                        client_socket, address = self.server_socket.accept()
                        self._handle_incoming_connection(client_socket, address)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Server error: {e}")
                    break
        
        except Exception as e:
            logger.error(f"Failed to start P2P server: {e}")
    
    def _handle_incoming_connection(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle incoming peer connection"""
        peer_key = f"{address[0]}:{address[1]}"
        
        # Check if peer is banned
        if address[0] in self.banned_peers:
            logger.warning(f"Rejected connection from banned peer {peer_key}")
            client_socket.close()
            return
        
        # Check connection limits
        with self.lock:
            inbound_count = sum(1 for p in self.peers.values() if not p.is_outbound)
            if inbound_count >= Config.MAX_INBOUND_CONNECTIONS:
                logger.warning(f"Rejected connection from {peer_key} - too many inbound connections")
                client_socket.close()
                return
            
            # Create peer connection
            peer = PeerConnection(client_socket, address, is_outbound=False)
            self.peers[peer_key] = peer
            self.stats['connections_received'] += 1
        
        logger.info(f"Accepted connection from {peer_key}")
        
        # Start peer handler thread
        peer_thread = threading.Thread(
            target=self._handle_peer,
            args=(peer,),
            daemon=True
        )
        peer_thread.start()
    
    def connect_to_peer(self, host: str, port: int) -> bool:
        """Connect to a peer node"""
        peer_key = f"{host}:{port}"
        
        # Check if already connected
        with self.lock:
            if peer_key in self.peers:
                return True
            
            # Check connection limits
            outbound_count = sum(1 for p in self.peers.values() if p.is_outbound)
            if outbound_count >= Config.MAX_OUTBOUND_CONNECTIONS:
                logger.warning("Cannot connect - too many outbound connections")
                return False
        
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(Config.CONNECTION_TIMEOUT)
            sock.connect((host, port))
            
            # Create peer connection
            peer = PeerConnection(sock, (host, port), is_outbound=True)
            
            with self.lock:
                self.peers[peer_key] = peer
                self.stats['connections_made'] += 1
            
            logger.info(f"Connected to peer {peer_key}")
            
            # Start peer handler thread
            peer_thread = threading.Thread(
                target=self._handle_peer,
                args=(peer,),
                daemon=True
            )
            peer_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {peer_key}: {e}")
            return False
    
    def _handle_peer(self, peer: PeerConnection):
        """Handle communication with a peer"""
        peer_key = f"{peer.address[0]}:{peer.address[1]}"
        
        try:
            # Send version message
            version_msg = NetworkMessage(NetworkMessage.VERSION, {
                'version': self.version,
                'services': self.services,
                'timestamp': time.time(),
                'user_agent': self.user_agent,
                'height': len(self.blockchain.chain),
                'relay': True,
                'node_id': self.node_id
            })
            
            if not peer.send_message(version_msg):
                return
            
            # Message handling loop
            while self.running and peer.is_alive:
                message = peer.receive_message()
                if not message:
                    break
                
                self._process_message(peer, message)
                
        except Exception as e:
            logger.error(f"Error handling peer {peer_key}: {e}")
        finally:
            # Clean up peer connection
            with self.lock:
                if peer_key in self.peers:
                    del self.peers[peer_key]
            peer.disconnect()
            logger.info(f"Disconnected from peer {peer_key}")
    
    def _process_message(self, peer: PeerConnection, message: NetworkMessage):
        """Process incoming message from peer"""
        try:
            if message.type == NetworkMessage.VERSION:
                self._handle_version(peer, message)
            elif message.type == NetworkMessage.VERACK:
                self._handle_verack(peer, message)
            elif message.type == NetworkMessage.PING:
                self._handle_ping(peer, message)
            elif message.type == NetworkMessage.PONG:
                self._handle_pong(peer, message)
            elif message.type == NetworkMessage.GETBLOCKS:
                self._handle_getblocks(peer, message)
            elif message.type == NetworkMessage.BLOCKS:
                self._handle_blocks(peer, message)
            elif message.type == NetworkMessage.TX:
                self._handle_transaction(peer, message)
            elif message.type == NetworkMessage.MEMPOOL:
                self._handle_mempool_request(peer, message)
            elif message.type == NetworkMessage.PEERS:
                self._handle_peers(peer, message)
            else:
                logger.warning(f"Unknown message type: {message.type}")
                
        except Exception as e:
            logger.error(f"Error processing message {message.type}: {e}")
    
    def _handle_version(self, peer: PeerConnection, message: NetworkMessage):
        """Handle version message"""
        payload = message.payload
        peer.version = payload.get('version', 0)
        peer.user_agent = payload.get('user_agent', 'Unknown')
        peer.height = payload.get('height', 0)
        peer.relay = payload.get('relay', True)
        
        # Send version acknowledgment
        verack_msg = NetworkMessage(NetworkMessage.VERACK)
        peer.send_message(verack_msg)
        
        logger.info(f"Peer {peer.address[0]}:{peer.address[1]} version: {peer.version}, height: {peer.height}")
    
    def _handle_verack(self, peer: PeerConnection, message: NetworkMessage):
        """Handle version acknowledgment"""
        logger.debug(f"Version handshake completed with {peer.address[0]}:{peer.address[1]}")
    
    def _handle_ping(self, peer: PeerConnection, message: NetworkMessage):
        """Handle ping message"""
        ping_timestamp = message.payload.get('timestamp', time.time())
        peer.pong(ping_timestamp)
    
    def _handle_pong(self, peer: PeerConnection, message: NetworkMessage):
        """Handle pong message"""
        peer.last_pong = time.time()
        ping_timestamp = message.payload.get('ping_timestamp', 0)
        latency = peer.last_pong - ping_timestamp
        logger.debug(f"Pong from {peer.address[0]}:{peer.address[1]}, latency: {latency:.3f}s")
    
    def _handle_getblocks(self, peer: PeerConnection, message: NetworkMessage):
        """Handle request for blocks"""
        start_height = message.payload.get('start_height', 0)
        max_blocks = min(message.payload.get('max_blocks', 500), 500)
        
        blocks_data = []
        for i in range(start_height, min(start_height + max_blocks, len(self.blockchain.chain))):
            if i < len(self.blockchain.chain):
                blocks_data.append(self.blockchain.chain[i].to_dict())
        
        if blocks_data:
            blocks_msg = NetworkMessage(NetworkMessage.BLOCKS, {'blocks': blocks_data})
            peer.send_message(blocks_msg)
    
    def _handle_blocks(self, peer: PeerConnection, message: NetworkMessage):
        """Handle incoming blocks"""
        blocks_data = message.payload.get('blocks', [])
        
        for block_data in blocks_data:
            try:
                # Reconstruct block
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
                
                # Validate and add block
                if self._validate_and_add_block(block):
                    self.stats['blocks_synced'] += 1
                    logger.info(f"Synced block {block.index} from peer")
                
            except Exception as e:
                logger.error(f"Failed to process block: {e}")
    
    def _handle_transaction(self, peer: PeerConnection, message: NetworkMessage):
        """Handle incoming transaction and broadcast to all peers"""
        try:
            tx_data = message.payload.get('transaction')
            if tx_data:
                transaction = MainnetTransaction(**tx_data)
                success, msg = self.blockchain.add_transaction_to_mempool(transaction)
                if success:
                    self.stats['transactions_relayed'] += 1
                    logger.info(f"Added transaction {transaction.tx_id} to mempool from peer {peer.address[0]}")
                    # Immediately relay to all other peers for network-wide mempool sync
                    self._relay_transaction(transaction, exclude_peer=peer)
                    # Notify about new transaction for mining
                    self._notify_new_transaction(transaction)
                else:
                    logger.warning(f"Failed to add transaction to mempool: {msg}")
        except Exception as e:
            logger.error(f"Failed to process transaction: {e}")
    
    def _notify_new_transaction(self, transaction: MainnetTransaction):
        """Notify about new transaction for potential mining trigger"""
        logger.info(f"New transaction available for mining: {transaction.tx_id} ({transaction.amount} GSC)")
        # This can be used to trigger mining if a miner is waiting
    
    def _handle_mempool_request(self, peer: PeerConnection, message: NetworkMessage):
        """Handle mempool request"""
        mempool_data = [tx.to_dict() for tx in self.blockchain.mempool]
        mempool_msg = NetworkMessage(NetworkMessage.MEMPOOL, {'transactions': mempool_data})
        peer.send_message(mempool_msg)
    
    def _handle_peers(self, peer: PeerConnection, message: NetworkMessage):
        """Handle peers list"""
        peers_list = message.payload.get('peers', [])
        for peer_addr in peers_list:
            self.known_nodes.add(peer_addr)
    
    def _validate_and_add_block(self, block: MainnetBlock) -> bool:
        """Validate and add block to chain"""
        with self.blockchain.lock:
            # Check if block already exists
            if block.index < len(self.blockchain.chain):
                existing_block = self.blockchain.chain[block.index]
                if existing_block.hash == block.hash:
                    return False  # Already have this block
            
            # Validate block
            if block.index != len(self.blockchain.chain):
                return False  # Not the next block
            
            if block.previous_hash != self.blockchain.get_latest_block().hash:
                return False  # Invalid previous hash
            
            # Add block
            self.blockchain.chain.append(block)
            self.blockchain.update_balances_from_block(block)
            
            return True
    
    def _relay_transaction(self, transaction: MainnetTransaction, exclude_peer: PeerConnection = None):
        """Relay transaction to other peers"""
        tx_msg = NetworkMessage(NetworkMessage.TX, {'transaction': transaction.to_dict()})
        
        with self.lock:
            for peer in self.peers.values():
                if peer != exclude_peer and peer.relay:
                    peer.send_message(tx_msg)
    
    def _connect_to_seeds(self):
        """Connect to seed nodes"""
        for seed in list(self.known_nodes)[:Config.MAX_OUTBOUND_CONNECTIONS]:
            if ':' in seed:
                host, port = seed.split(':')
                try:
                    port = int(port)
                    threading.Thread(
                        target=self.connect_to_peer,
                        args=(host, port),
                        daemon=True
                    ).start()
                except ValueError:
                    continue
    
    def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while self.running:
            try:
                # Ping peers
                current_time = time.time()
                with self.lock:
                    for peer in list(self.peers.values()):
                        if current_time - peer.last_ping > Config.PING_INTERVAL:
                            if not peer.ping():
                                continue
                        
                        # Check for dead peers
                        if (peer.last_ping > 0 and 
                            current_time - peer.last_ping > Config.PING_INTERVAL * 3 and
                            peer.last_pong < peer.last_ping):
                            logger.warning(f"Peer {peer.address[0]}:{peer.address[1]} appears dead, disconnecting")
                            peer.disconnect()
                
                # Try to maintain minimum connections
                with self.lock:
                    active_peers = len([p for p in self.peers.values() if p.is_alive])
                    if active_peers < Config.MAX_OUTBOUND_CONNECTIONS // 2:
                        self._connect_to_seeds()
                
                time.sleep(30)  # Run maintenance every 30 seconds
                
            except Exception as e:
                logger.error(f"Maintenance error: {e}")
                time.sleep(60)
    
    def broadcast_block(self, block: MainnetBlock):
        """Broadcast new block to all peers"""
        block_msg = NetworkMessage(NetworkMessage.BLOCKS, {'blocks': [block.to_dict()]})
        
        with self.lock:
            for peer in self.peers.values():
                peer.send_message(block_msg)
        
        logger.info(f"Broadcasted block {block.index} to {len(self.peers)} peers")
    
    def request_blocks(self, start_height: int, max_blocks: int = 500):
        """Request blocks from peers"""
        getblocks_msg = NetworkMessage(NetworkMessage.GETBLOCKS, {
            'start_height': start_height,
            'max_blocks': max_blocks
        })
        
        with self.lock:
            for peer in self.peers.values():
                peer.send_message(getblocks_msg)
    
    def get_network_info(self) -> dict:
        """Get network information"""
        with self.lock:
            peer_info = [peer.get_stats() for peer in self.peers.values()]
            
            return {
                'node_id': self.node_id,
                'version': self.version,
                'user_agent': self.user_agent,
                'port': self.port,
                'peers_connected': len(self.peers),
                'peers_info': peer_info,
                'known_nodes': len(self.known_nodes),
                'banned_peers': len(self.banned_peers),
                'running': self.running,
                'stats': self.stats,
                'uptime': time.time() - self.stats['start_time']
            }
