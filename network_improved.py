"""
GSC Coin P2P Network Layer - Improved Implementation
Robust networking with message validation, rate limiting, and comprehensive logging
"""

import socket
import threading
import json
import time
import hashlib
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass
import pickle
import os

from gsc_logger import network_logger
from thread_safety import ThreadSafeSet, ThreadSafeDict, RateLimiter, AtomicCounter

@dataclass
class PeerInfo:
    """Information about a peer"""
    address: str
    node_id: str
    version: int
    last_seen: float
    banscore: int
    connection_count: int
    user_agent: str = "GSCCoin/1.0"
    services: int = 0
    height: int = 0

@dataclass
class NetworkMessage:
    """Network message with validation"""
    message_type: str
    data: Dict[str, Any]
    sender: str = ""
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class MessageValidator:
    """Validate network messages for security"""
    
    REQUIRED_FIELDS = {
        'version': ['version', 'node_id', 'timestamp'],
        'verack': [],
        'getheaders': ['locator_hash', 'stop_hash'],
        'headers': ['headers'],
        'getdata': ['items'],
        'block': ['block'],
        'inv': ['items'],
        'new_transaction': ['transaction'],
        'peer_list': ['peers'],
        'ping': [],
        'pong': [],
        'getaddr': [],
        'addr': ['addresses']
    }
    
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
    MAX_PEER_LIST_SIZE = 1000
    MAX_HEADERS_COUNT = 2000
    MAX_INV_ITEMS = 50000
    
    @classmethod
    def validate_message(cls, message: Dict[str, Any]) -> Optional[str]:
        """Validate message format and return error if invalid"""
        if not isinstance(message, dict):
            return "Message must be a dictionary"
        
        message_type = message.get('type')
        if not message_type:
            return "Message missing 'type' field"
        
        if not isinstance(message_type, str):
            return "Message type must be a string"
        
        # Check required fields
        required = cls.REQUIRED_FIELDS.get(message_type, [])
        for field in required:
            if field not in message:
                return f"Message type '{message_type}' missing required field: {field}"
        
        # Size validations
        if message_type == 'headers':
            headers = message.get('headers', [])
            if len(headers) > cls.MAX_HEADERS_COUNT:
                return f"Too many headers: {len(headers)} > {cls.MAX_HEADERS_COUNT}"
        
        elif message_type == 'inv':
            items = message.get('items', [])
            if len(items) > cls.MAX_INV_ITEMS:
                return f"Too many inv items: {len(items)} > {cls.MAX_INV_ITEMS}"
        
        elif message_type == 'peer_list':
            peers = message.get('peers', [])
            if len(peers) > cls.MAX_PEER_LIST_SIZE:
                return f"Too many peers: {len(peers)} > {cls.MAX_PEER_LIST_SIZE}"
        
        return None  # Valid

class BanscoreManager:
    """Manage peer banning with persistence"""
    
    def __init__(self, max_banscore: int = 100):
        self.max_banscore = max_banscore
        self.banned_peers = ThreadSafeDict[str, Dict[str, Any]]()
        self.peer_scores = ThreadSafeDict[str, int]()
        self.bans_file = "banned_peers.json"
        self.load_bans()
    
    def add_score(self, peer_address: str, score: int, reason: str = "") -> None:
        """Add to peer's banscore"""
        current_score = self.peer_scores.get(peer_address, 0)
        new_score = current_score + score
        self.peer_scores.set(peer_address, new_score)
        
        network_logger.debug(f"Peer {peer_address} score: {current_score} -> {new_score} ({reason})")
        
        if new_score >= self.max_banscore:
            self.ban_peer(peer_address, f"Score reached {new_score}")
    
    def ban_peer(self, peer_address: str, reason: str = "") -> None:
        """Ban a peer"""
        ban_info = {
            'address': peer_address,
            'banned_at': time.time(),
            'reason': reason,
            'score': self.peer_scores.get(peer_address, self.max_banscore)
        }
        
        self.banned_peers.set(peer_address, ban_info)
        network_logger.warning(f"Peer banned: {peer_address} - {reason}")
        self.save_bans()
    
    def is_banned(self, peer_address: str) -> bool:
        """Check if peer is banned"""
        return peer_address in self.banned_peers
    
    def unban_peer(self, peer_address: str) -> None:
        """Unban a peer"""
        self.banned_peers.remove(peer_address)
        self.peer_scores.remove(peer_address)
        network_logger.info(f"Peer unbanned: {peer_address}")
        self.save_bans()
    
    def save_bans(self) -> None:
        """Save banned peers to file"""
        try:
            with open(self.bans_file, 'w') as f:
                json.dump(self.banned_peers.copy(), f, indent=2)
        except Exception as e:
            network_logger.error(f"Failed to save bans: {e}")
    
    def load_bans(self) -> None:
        """Load banned peers from file"""
        try:
            if os.path.exists(self.bans_file):
                with open(self.bans_file, 'r') as f:
                    bans = json.load(f)
                    for addr, info in bans.items():
                        self.banned_peers.set(addr, info)
                        self.peer_scores.set(addr, info.get('score', self.max_banscore))
                
                network_logger.info(f"Loaded {len(self.banned_peers)} banned peers")
        except Exception as e:
            network_logger.error(f"Failed to load bans: {e}")

class ConnectionManager:
    """Manage peer connections with timeouts and retries"""
    
    def __init__(self, max_connections: int = 50):
        self.max_connections = max_connections
        self.active_connections = ThreadSafeSet[str]()
        self.connection_attempts = ThreadSafeDict[str, List[float]]()
        self.rate_limiters = ThreadSafeDict[str, RateLimiter]()
        self.connection_timeout = 30.0
        self.read_timeout = 60.0
        self.max_retry_attempts = 3
        self.retry_backoff = 5.0  # seconds
    
    def can_connect(self, peer_address: str) -> bool:
        """Check if we can connect to a peer"""
        # Check connection limit
        if len(self.active_connections) >= self.max_connections:
            return False
        
        # Check if already connected
        if peer_address in self.active_connections:
            return False
        
        # Check rate limiting
        rate_limiter = self.rate_limiters.get(peer_address)
        if not rate_limiter:
            rate_limiter = RateLimiter(max_calls=3, time_window=60.0)
            self.rate_limiters.set(peer_address, rate_limiter)
        
        if not rate_limiter.is_allowed():
            wait_time = rate_limiter.wait_time()
            network_logger.debug(f"Rate limited for {peer_address}, wait {wait_time:.1f}s")
            return False
        
        # Check retry attempts
        attempts = self.connection_attempts.get(peer_address, [])
        recent_attempts = [t for t in attempts if time.time() - t < 300]  # Last 5 minutes
        
        if len(recent_attempts) >= self.max_retry_attempts:
            network_logger.debug(f"Too many connection attempts to {peer_address}")
            return False
        
        return True
    
    def record_connection_attempt(self, peer_address: str) -> None:
        """Record a connection attempt"""
        attempts = self.connection_attempts.get(peer_address, [])
        attempts.append(time.time())
        # Keep only recent attempts
        attempts = [t for t in attempts if time.time() - t < 300]
        self.connection_attempts.set(peer_address, attempts)
    
    def add_connection(self, peer_address: str) -> None:
        """Add an active connection"""
        self.active_connections.add(peer_address)
    
    def remove_connection(self, peer_address: str) -> None:
        """Remove an active connection"""
        self.active_connections.discard(peer_address)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

class DNSSeeder:
    """DNS seed discovery for peer finding"""
    
    DEFAULT_DNS_SEEDS = [
        "seed.gsc-coin.org",
        "seed1.gsc-coin.org",
        "seed2.gsc-coin.org"
    ]
    
    def __init__(self):
        self.dns_cache = ThreadSafeDict[str, List[str]]()
        self.cache_timeout = 3600  # 1 hour
    
    def get_peers_from_dns(self, dns_seed: str = None) -> List[str]:
        """Get peers from DNS seed"""
        if dns_seed is None:
            dns_seed = self.DEFAULT_DNS_SEEDS[0]
        
        # Check cache
        cached = self.dns_cache.get(dns_seed)
        if cached and time.time() - cached[0] < self.cache_timeout:
            return cached[1]
        
        try:
            import socket
            # Get DNS records
            answers = socket.getaddrinfo(dns_seed, 8333, socket.AF_INET)
            peers = [addr[4][0] for addr in answers]
            
            # Cache result
            self.dns_cache.set(dns_seed, [time.time(), peers])
            
            network_logger.info(f"DNS seed {dns_seed} returned {len(peers)} peers")
            return peers
            
        except Exception as e:
            network_logger.error(f"DNS seed lookup failed for {dns_seed}: {e}")
            return []

class GSCNetworkNode:
    """Improved GSC Coin P2P Network Node"""
    
    def __init__(self, blockchain, port: int = 8333):
        self.blockchain = blockchain
        self.port = port
        self.node_id = self.generate_node_id()
        
        # Thread-safe data structures
        self.peers = ThreadSafeSet[str]()
        self.peer_info = ThreadSafeDict[str, PeerInfo]()
        self.known_nodes = ThreadSafeSet[str]()
        
        # Management components
        self.banscore_manager = BanscoreManager()
        self.connection_manager = ConnectionManager()
        self.dns_seeder = DNSSeeder()
        
        # Threading
        self.server_socket = None
        self.running = False
        self.sync_lock = threading.RLock()
        
        # Statistics
        self.messages_sent = AtomicCounter(0)
        self.messages_received = AtomicCounter(0)
        self.bytes_sent = AtomicCounter(0)
        self.bytes_received = AtomicCounter(0)
        
        # Seed nodes
        self.seed_nodes = [
            "127.0.0.1",
            "192.168.1.10",
            "192.168.0.10"
        ]
    
    def generate_node_id(self) -> str:
        """Generate unique node ID"""
        return hashlib.sha256(f"{socket.gethostname()}{time.time()}".encode()).hexdigest()[:16]
    
    def start_server(self) -> bool:
        """Start P2P server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.settimeout(1.0)  # Non-blocking accept
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(10)
            self.running = True
            
            network_logger.info(f"GSC Node started on port {self.port}")
            network_logger.info(f"Node ID: {self.node_id}")
            
            # Start server thread
            server_thread = threading.Thread(target=self.accept_connections, daemon=True)
            server_thread.start()
            
            # Start peer discovery
            discovery_thread = threading.Thread(target=self.discover_peers, daemon=True)
            discovery_thread.start()
            
            # Start stats reporting
            stats_thread = threading.Thread(target=self.report_stats, daemon=True)
            stats_thread.start()
            
            return True
            
        except Exception as e:
            network_logger.error(f"Failed to start P2P server: {e}")
            return False
    
    def stop_server(self) -> None:
        """Stop P2P server"""
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        network_logger.info("P2P server stopped")
    
    def accept_connections(self) -> None:
        """Accept incoming connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                peer_address = f"{address[0]}:{address[1]}"
                
                # Check if peer is banned
                if self.banscore_manager.is_banned(address[0]):
                    network_logger.warning(f"Rejected connection from banned peer: {peer_address}")
                    client_socket.close()
                    continue
                
                # Check connection limits
                if not self.connection_manager.can_connect(peer_address):
                    network_logger.debug(f"Connection limit reached for {peer_address}")
                    client_socket.close()
                    continue
                
                network_logger.info(f"New peer connected: {peer_address}")
                
                # Handle peer in separate thread
                peer_thread = threading.Thread(
                    target=self.handle_peer,
                    args=(client_socket, address),
                    daemon=True
                )
                peer_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    network_logger.error(f"Error accepting connection: {e}")
    
    def handle_peer(self, client_socket: socket.socket, address: tuple) -> None:
        """Handle communication with a peer"""
        peer_address = f"{address[0]}:{address[1]}"
        
        # Set socket timeouts
        client_socket.settimeout(self.connection_manager.read_timeout)
        
        # Track connection
        self.connection_manager.add_connection(peer_address)
        self.peers.add(peer_address)
        
        try:
            # Send version message
            self.send_version(client_socket, peer_address)
            
            # Handle messages
            while self.running:
                try:
                    # Read message length first (4 bytes)
                    length_data = self.recv_exact(client_socket, 4)
                    if not length_data:
                        break
                    
                    message_length = int.from_bytes(length_data, byteorder='big')
                    if message_length > MessageValidator.MAX_MESSAGE_SIZE:
                        network_logger.warning(f"Message too large from {peer_address}: {message_length}")
                        self.banscore_manager.add_score(address[0], 50, "Oversized message")
                        break
                    
                    # Read message data
                    message_data = self.recv_exact(client_socket, message_length)
                    if not message_data:
                        break
                    
                    # Parse and validate message
                    try:
                        message = json.loads(message_data.decode())
                        validation_error = MessageValidator.validate_message(message)
                        
                        if validation_error:
                            network_logger.warning(f"Invalid message from {peer_address}: {validation_error}")
                            self.banscore_manager.add_score(address[0], 10, f"Invalid message: {validation_error}")
                            continue
                        
                        # Process message
                        self.process_message(message, client_socket, peer_address)
                        self.messages_received.increment()
                        self.bytes_received.increment(len(message_data))
                        
                    except json.JSONDecodeError as e:
                        network_logger.warning(f"JSON decode error from {peer_address}: {e}")
                        self.banscore_manager.add_score(address[0], 20, "JSON decode error")
                        continue
                
                except socket.timeout:
                    # Send ping to keep connection alive
                    self.send_ping(client_socket)
                    continue
                except Exception as e:
                    network_logger.error(f"Error handling peer {peer_address}: {e}")
                    break
        
        finally:
            client_socket.close()
            self.connection_manager.remove_connection(peer_address)
            self.peers.discard(peer_address)
            network_logger.debug(f"Peer disconnected: {peer_address}")
    
    def recv_exact(self, sock: socket.socket, length: int) -> Optional[bytes]:
        """Receive exact number of bytes"""
        data = b''
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def send_message(self, sock: socket.socket, message: Dict[str, Any]) -> bool:
        """Send a message with length prefix"""
        try:
            message_data = json.dumps(message).encode()
            message_length = len(message_data)
            
            # Send length prefix
            sock.send(message_length.to_bytes(4, byteorder='big'))
            
            # Send message data
            sock.send(message_data)
            
            self.messages_sent.increment()
            self.bytes_sent.increment(message_length)
            
            return True
            
        except Exception as e:
            network_logger.error(f"Failed to send message: {e}")
            return False
    
    def send_version(self, sock: socket.socket, peer_address: str) -> None:
        """Send version message"""
        version_msg = {
            'type': 'version',
            'version': 1,
            'node_id': self.node_id,
            'timestamp': datetime.now().isoformat(),
            'user_agent': 'GSCCoin/1.0',
            'services': 0,
            'height': len(self.blockchain.chain),
            'port': self.port
        }
        
        self.send_message(sock, version_msg)
    
    def send_ping(self, sock: socket.socket) -> None:
        """Send ping message"""
        ping_msg = {
            'type': 'ping',
            'timestamp': time.time()
        }
        
        self.send_message(sock, ping_msg)
    
    def process_message(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Process incoming message"""
        msg_type = message.get('type')
        
        handlers = {
            'version': self.handle_version,
            'verack': self.handle_verack,
            'getheaders': self.handle_getheaders,
            'headers': self.handle_headers,
            'getdata': self.handle_getdata,
            'block': self.handle_block,
            'inv': self.handle_inv,
            'new_transaction': self.handle_new_transaction,
            'peer_list': self.handle_peer_list,
            'ping': self.handle_ping,
            'pong': self.handle_pong,
            'getaddr': self.handle_getaddr,
            'addr': self.handle_addr
        }
        
        handler = handlers.get(msg_type)
        if handler:
            try:
                handler(message, client_socket, peer_address)
            except Exception as e:
                network_logger.error(f"Error handling {msg_type} from {peer_address}: {e}")
        else:
            network_logger.warning(f"Unknown message type: {msg_type}")
    
    def handle_version(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle version message"""
        peer_ip = peer_address.split(':')[0]
        
        # Store peer info
        peer_info = PeerInfo(
            address=peer_address,
            node_id=message.get('node_id', ''),
            version=message.get('version', 1),
            last_seen=time.time(),
            banscore=0,
            connection_count=1,
            user_agent=message.get('user_agent', ''),
            services=message.get('services', 0),
            height=message.get('height', 0)
        )
        
        self.peer_info.set(peer_address, peer_info)
        
        # Send verack
        verack_msg = {'type': 'verack'}
        self.send_message(client_socket, verack_msg)
        
        network_logger.debug(f"Version handshake completed with {peer_address}")
    
    def handle_verack(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle verack message"""
        network_logger.debug(f"Verack received from {peer_address}")
    
    def handle_ping(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle ping message"""
        pong_msg = {
            'type': 'pong',
            'timestamp': message.get('timestamp', time.time())
        }
        self.send_message(client_socket, pong_msg)
    
    def handle_pong(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle pong message"""
        network_logger.debug(f"Pong received from {peer_address}")
    
    def handle_getaddr(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle getaddr request"""
        # Send list of known peers
        peer_list = list(self.peers)[:50]  # Limit to 50 peers
        addr_msg = {
            'type': 'addr',
            'addresses': peer_list
        }
        self.send_message(client_socket, addr_msg)
    
    def handle_addr(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle addr response"""
        addresses = message.get('addresses', [])
        network_logger.debug(f"Received {len(addresses)} addresses from {peer_address}")
        
        # Try to connect to new peers
        for addr in addresses:
            if addr not in self.peers and not self.banscore_manager.is_banned(addr):
                threading.Thread(
                    target=self.connect_to_peer,
                    args=(addr.split(':')[0], int(addr.split(':')[1])),
                    daemon=True
                ).start()
    
    def handle_getheaders(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle getheaders request"""
        try:
            locator_hash = message.get('locator_hash', '0' * 64)
            stop_hash = message.get('stop_hash', '0' * 64)
            
            headers = self.blockchain.get_block_headers(locator_hash, 2000)
            
            response = {
                'type': 'headers',
                'count': len(headers),
                'headers': headers
            }
            self.send_message(client_socket, response)
            
        except Exception as e:
            network_logger.error(f"Error handling getheaders: {e}")
    
    def handle_headers(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle headers message"""
        headers = message.get('headers', [])
        network_logger.info(f"Received {len(headers)} headers from {peer_address}")
        
        if headers:
            # Request blocks for these headers
            block_hashes = [h['hash'] for h in headers]
            self.request_blocks(peer_address, block_hashes)
    
    def handle_getdata(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle getdata request"""
        items = message.get('items', [])
        
        for item in items:
            if item['type'] == 'block':
                block = self.blockchain.get_block_by_hash(item['hash'])
                if block:
                    response = {
                        'type': 'block',
                        'block': block.to_dict()
                    }
                    self.send_message(client_socket, response)
    
    def handle_block(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle block message"""
        try:
            block_data = message.get('block')
            if not block_data:
                return
            
            # Reconstruct block
            transactions = []
            for tx_data in block_data['transactions']:
                tx = Transaction(**tx_data)
                transactions.append(tx)
            
            block = Block(
                index=block_data['index'],
                timestamp=block_data['timestamp'],
                transactions=transactions,
                previous_hash=block_data['previous_hash'],
                nonce=block_data['nonce'],
                hash=block_data['hash'],
                merkle_root=block_data['merkle_root'],
                difficulty=block_data['difficulty'],
                miner=block_data['miner'],
                reward=block_data['reward']
            )
            
            # Add to blockchain if valid
            if self.blockchain.add_block(block):
                network_logger.info(f"Added block {block.index} from {peer_address}")
            else:
                network_logger.warning(f"Invalid block {block.index} from {peer_address}")
        
        except Exception as e:
            network_logger.error(f"Error handling block: {e}")
    
    def handle_inv(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle inventory message"""
        items = message.get('items', [])
        blocks_to_request = []
        
        for item in items:
            if item['type'] == 'block':
                if not self.blockchain.get_block_by_hash(item['hash']):
                    blocks_to_request.append(item['hash'])
        
        if blocks_to_request:
            self.request_blocks(peer_address, blocks_to_request)
    
    def handle_new_transaction(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle new transaction"""
        try:
            tx_data = message.get('transaction')
            tx = Transaction(**tx_data)
            
            if self.blockchain.add_transaction_to_mempool(tx):
                network_logger.info(f"New transaction from {peer_address}: {tx.tx_id[:16]}...")
                # Broadcast to other peers
                self.broadcast_transaction(tx, exclude_peer=peer_address)
        
        except Exception as e:
            network_logger.error(f"Error handling transaction: {e}")
    
    def handle_peer_list(self, message: Dict[str, Any], client_socket: socket.socket, peer_address: str) -> None:
        """Handle peer list"""
        peers = message.get('peers', [])
        network_logger.debug(f"Received {len(peers)} peers from {peer_address}")
        
        for peer in peers:
            if peer not in self.peers and not self.banscore_manager.is_banned(peer):
                try:
                    host, port = peer.split(':')
                    threading.Thread(
                        target=self.connect_to_peer,
                        args=(host, int(port)),
                        daemon=True
                    ).start()
                except:
                    pass
    
    def request_blocks(self, peer_address: str, block_hashes: List[str]) -> None:
        """Request blocks from peer"""
        try:
            host, port = peer_address.split(':')
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10.0)
            s.connect((host, int(port)))
            
            request = {
                'type': 'getdata',
                'items': [{'type': 'block', 'hash': h} for h in block_hashes]
            }
            
            self.send_message(s, request)
            s.close()
            
        except Exception as e:
            network_logger.error(f"Failed to request blocks from {peer_address}: {e}")
    
    def connect_to_peer(self, host: str, port: int) -> bool:
        """Connect to a peer"""
        peer_address = f"{host}:{port}"
        
        if not self.connection_manager.can_connect(peer_address):
            return False
        
        self.connection_manager.record_connection_attempt(peer_address)
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.connection_manager.connection_timeout)
            s.connect((host, port))
            
            # Send version
            self.send_version(s, peer_address)
            
            # Handle responses in separate thread
            threading.Thread(
                target=self.handle_peer,
                args=(s, (host, port)),
                daemon=True
            ).start()
            
            network_logger.info(f"Connected to peer: {peer_address}")
            return True
            
        except Exception as e:
            network_logger.debug(f"Failed to connect to {peer_address}: {e}")
            return False
    
    def discover_peers(self) -> None:
        """Discover and connect to peers"""
        while self.running:
            try:
                # Connect to seed nodes if we have few peers
                if len(self.peers) < 3:
                    for seed in self.seed_nodes:
                        if seed not in self.peers:
                            self.connect_to_peer(seed, 8333)
                
                # Try DNS seeds if still few peers
                if len(self.peers) < 5:
                    dns_peers = self.dns_seeder.get_peers_from_dns()
                    for peer in dns_peers[:10]:  # Try first 10
                        if peer not in self.peers:
                            self.connect_to_peer(peer, 8333)
                
                # Sleep before next discovery cycle
                time.sleep(60)
                
            except Exception as e:
                network_logger.error(f"Error in peer discovery: {e}")
                time.sleep(120)
    
    def broadcast_transaction(self, transaction: Transaction, exclude_peer: str = None) -> None:
        """Broadcast transaction to all peers"""
        message = {
            'type': 'new_transaction',
            'transaction': transaction.to_dict(),
            'sender': self.node_id
        }
        
        for peer_address in self.peers:
            if exclude_peer and peer_address == exclude_peer:
                continue
            
            try:
                host, port = peer_address.split(':')
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5.0)
                s.connect((host, int(port)))
                self.send_message(s, message)
                s.close()
            except:
                pass
    
    def broadcast_block(self, block: Block) -> None:
        """Broadcast block to all peers"""
        message = {
            'type': 'inv',
            'items': [{'type': 'block', 'hash': block.hash}],
            'sender': self.node_id
        }
        
        for peer_address in self.peers:
            try:
                host, port = peer_address.split(':')
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5.0)
                s.connect((host, int(port)))
                self.send_message(s, message)
                s.close()
            except:
                pass
    
    def report_stats(self) -> None:
        """Report network statistics"""
        while self.running:
            try:
                network_logger.info(
                    f"Network stats - Peers: {len(self.peers)}, "
                    f"Messages sent: {self.messages_sent.get()}, "
                    f"Messages received: {self.messages_received.get()}, "
                    f"Bytes sent: {self.bytes_sent.get()}, "
                    f"Bytes received: {self.bytes_received.get()}"
                )
                
                # Clean up old connection attempts
                current_time = time.time()
                for peer, attempts in self.connection_attempts.connection_attempts._dict.items():
                    self.connection_attempts.connection_attempts._dict[peer] = [
                        t for t in attempts if current_time - t < 300
                    ]
                
                time.sleep(300)  # Report every 5 minutes
                
            except Exception as e:
                network_logger.error(f"Error reporting stats: {e}")
                time.sleep(60)
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information for GUI"""
        return {
            'connected_peers': len(self.peers),
            'banned_peers': len(self.banscore_manager.banned_peers),
            'messages_sent': self.messages_sent.get(),
            'messages_received': self.messages_received.get(),
            'bytes_sent': self.bytes_sent.get(),
            'bytes_received': self.bytes_received.get(),
            'node_id': self.node_id,
            'port': self.port
        }
    
    def get_peer_list(self) -> List[Dict[str, Any]]:
        """Get detailed peer information"""
        peer_list = []
        for peer_address in self.peers:
            info = self.peer_info.get(peer_address)
            if info:
                peer_list.append({
                    'address': info.address,
                    'node_id': info.node_id,
                    'version': info.version,
                    'last_seen': info.last_seen,
                    'user_agent': info.user_agent,
                    'height': info.height
                })
        return peer_list
    
    def get_banned_peers(self) -> List[Dict[str, Any]]:
        """Get list of banned peers"""
        banned = []
        for peer_address, ban_info in self.banscore_manager.banned_peers.copy().items():
            banned.append({
                'address': peer_address,
                'banned_at': ban_info['banned_at'],
                'reason': ban_info['reason'],
                'score': ban_info['score']
            })
        return banned
