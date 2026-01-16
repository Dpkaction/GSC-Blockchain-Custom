#!/usr/bin/env python3
"""
Bitcoin-Style Sync Node
=======================
Pure Bitcoin sync pipeline: headers → blocks → mempool
No mining/wallet logic - just the sync process
"""

import socket
import threading
import json
import time
import hashlib
import random
from typing import Set, List, Dict, Optional, Tuple
from dataclasses import dataclass
from bitcoin_p2p_node import BitcoinP2PNode

@dataclass
class BlockHeader:
    """Minimal block header (~80 bytes like Bitcoin)"""
    hash: str
    prev_hash: str
    merkle_root: str
    timestamp: float
    difficulty: int
    nonce: int
    height: int
    
    def to_dict(self):
        return {
            'hash': self.hash,
            'prev_hash': self.prev_hash,
            'merkle_root': self.merkle_root,
            'timestamp': self.timestamp,
            'difficulty': self.difficulty,
            'nonce': self.nonce,
            'height': self.height
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class Transaction:
    """Minimal transaction"""
    tx_id: str
    sender: str
    receiver: str
    amount: float
    timestamp: float
    
    def to_dict(self):
        return {
            'tx_id': self.tx_id,
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class Block:
    """Full block with header + transactions"""
    header: BlockHeader
    transactions: List[Transaction]
    
    def to_dict(self):
        return {
            'header': self.header.to_dict(),
            'transactions': [tx.to_dict() for tx in self.transactions]
        }
    
    @classmethod
    def from_dict(cls, data):
        header = BlockHeader.from_dict(data['header'])
        transactions = [Transaction.from_dict(tx) for tx in data['transactions']]
        return cls(header, transactions)

class BitcoinSyncNode(BitcoinP2PNode):
    """Bitcoin-style sync node with headers-first sync"""
    
    def __init__(self, port: int = 5000, node_id: str = None):
        super().__init__(port, node_id)
        
        # Blockchain state
        self.headers: Dict[str, BlockHeader] = {}  # hash -> header
        self.blocks: Dict[str, Block] = {}         # hash -> full block
        self.mempool: Dict[str, Transaction] = {}  # tx_id -> transaction
        
        # Chain state
        self.genesis_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        self.best_chain: List[str] = []  # List of block hashes in order
        self.chain_tip = self.genesis_hash
        self.chain_height = 0
        
        # Sync state
        self.sync_mode = "headers"  # headers -> blocks -> mempool -> live
        self.syncing_with: Set[str] = set()  # Peers we're syncing with
        self.requested_headers: Set[str] = set()
        self.requested_blocks: Set[str] = set()
        
        # Create genesis
        self._create_genesis()
        
        print(f"🔗 Bitcoin Sync Node initialized: {self.node_id}")
    
    def _create_genesis(self):
        """Create genesis block"""
        genesis_header = BlockHeader(
            hash=self.genesis_hash,
            prev_hash="0" * 64,
            merkle_root="0" * 64,
            timestamp=time.time(),
            difficulty=1,
            nonce=0,
            height=0
        )
        
        genesis_block = Block(
            header=genesis_header,
            transactions=[]
        )
        
        self.headers[self.genesis_hash] = genesis_header
        self.blocks[self.genesis_hash] = genesis_block
        self.best_chain = [self.genesis_hash]
        self.chain_tip = self.genesis_hash
        self.chain_height = 0
        
        print(f"📦 Genesis block created: {self.genesis_hash[:16]}...")
    
    def _process_message(self, message: dict, peer_addr: str) -> Optional[dict]:
        """Process Bitcoin sync messages"""
        msg_type = message.get("type")
        
        # Handle base P2P messages first
        base_response = super()._process_message(message, peer_addr)
        if base_response:
            return base_response
        
        # Handle sync messages
        if msg_type == "getheaders":
            return self._handle_getheaders(message, peer_addr)
        elif msg_type == "headers":
            self._handle_headers(message, peer_addr)
        elif msg_type == "getblocks":
            return self._handle_getblocks(message, peer_addr)
        elif msg_type == "inv":
            self._handle_inv(message, peer_addr)
        elif msg_type == "getdata":
            return self._handle_getdata(message, peer_addr)
        elif msg_type == "block":
            self._handle_block(message, peer_addr)
        elif msg_type == "mempool":
            return self._handle_mempool_request(message, peer_addr)
        elif msg_type == "tx":
            self._handle_transaction(message, peer_addr)
        
        return None
    
    # PHASE 1: Headers-First Sync
    def start_headers_sync(self, peer_addr: str):
        """Start headers sync with a peer"""
        if peer_addr in self.syncing_with:
            return
        
        self.syncing_with.add(peer_addr)
        print(f"📥 Starting headers sync with {peer_addr}")
        
        # Request headers from our chain tip
        self._request_headers(peer_addr, self.chain_tip)
    
    def _request_headers(self, peer_addr: str, from_hash: str):
        """Request headers from a specific block"""
        if peer_addr not in self.peer_connections:
            return
        
        try:
            getheaders_msg = {
                "type": "getheaders",
                "from_block": from_hash,
                "node_id": self.node_id
            }
            
            self.peer_connections[peer_addr].send(json.dumps(getheaders_msg).encode())
            print(f"📤 Requested headers from {from_hash[:16]}... to {peer_addr}")
            
        except Exception as e:
            print(f"❌ Failed to request headers from {peer_addr}: {e}")
    
    def _handle_getheaders(self, message: dict, peer_addr: str) -> dict:
        """Handle getheaders request"""
        from_block = message.get("from_block", self.genesis_hash)
        
        # Find headers after from_block
        headers_to_send = []
        
        if from_block in self.headers:
            # Find position in chain
            try:
                start_idx = self.best_chain.index(from_block) + 1
                # Send up to 2000 headers (Bitcoin limit)
                for i in range(start_idx, min(start_idx + 2000, len(self.best_chain))):
                    block_hash = self.best_chain[i]
                    if block_hash in self.headers:
                        headers_to_send.append(self.headers[block_hash].to_dict())
            except ValueError:
                pass
        
        print(f"📤 Sending {len(headers_to_send)} headers to {peer_addr}")
        
        return {
            "type": "headers",
            "headers": headers_to_send,
            "count": len(headers_to_send)
        }
    
    def _handle_headers(self, message: dict, peer_addr: str):
        """Handle received headers"""
        headers_data = message.get("headers", [])
        
        if not headers_data:
            print(f"📥 No new headers from {peer_addr}")
            self._start_blocks_sync(peer_addr)
            return
        
        print(f"📥 Received {len(headers_data)} headers from {peer_addr}")
        
        new_headers = []
        for header_data in headers_data:
            header = BlockHeader.from_dict(header_data)
            
            # Validate header chain
            if self._validate_header(header):
                if header.hash not in self.headers:
                    self.headers[header.hash] = header
                    new_headers.append(header)
        
        if new_headers:
            # Update best chain if this is better
            if self._update_best_chain(new_headers):
                print(f"✅ Updated best chain, new height: {self.chain_height}")
            
            # Request more headers if we got a full batch
            if len(headers_data) >= 2000:
                last_header = new_headers[-1]
                self._request_headers(peer_addr, last_header.hash)
            else:
                # Headers sync complete, start blocks sync
                self._start_blocks_sync(peer_addr)
        else:
            self._start_blocks_sync(peer_addr)
    
    def _validate_header(self, header: BlockHeader) -> bool:
        """Validate block header"""
        # Check if previous block exists
        if header.prev_hash != "0" * 64 and header.prev_hash not in self.headers:
            return False
        
        # Basic validation
        if header.height < 0 or header.difficulty < 1:
            return False
        
        return True
    
    def _update_best_chain(self, new_headers: List[BlockHeader]) -> bool:
        """Update best chain if new headers represent better chain"""
        # Simple longest chain rule
        if not new_headers:
            return False
        
        # Check if this extends our current chain
        last_header = new_headers[-1]
        if last_header.height > self.chain_height:
            # Rebuild chain from genesis
            self._rebuild_chain()
            return True
        
        return False
    
    def _rebuild_chain(self):
        """Rebuild best chain from headers"""
        # Find the longest valid chain
        chains = {}
        
        # Start from all headers and build chains
        for block_hash, header in self.headers.items():
            if header.prev_hash in self.headers or header.prev_hash == "0" * 64:
                chains[block_hash] = header.height
        
        if chains:
            # Find highest chain
            best_hash = max(chains.keys(), key=lambda h: chains[h])
            best_header = self.headers[best_hash]
            
            # Rebuild chain backwards
            chain = []
            current_hash = best_hash
            
            while current_hash and current_hash in self.headers:
                chain.append(current_hash)
                header = self.headers[current_hash]
                current_hash = header.prev_hash if header.prev_hash != "0" * 64 else None
            
            chain.reverse()
            
            self.best_chain = chain
            self.chain_tip = best_hash
            self.chain_height = best_header.height
    
    # PHASE 2: Block Inventory
    def _start_blocks_sync(self, peer_addr: str):
        """Start block inventory and download"""
        print(f"📦 Starting blocks sync with {peer_addr}")
        self.sync_mode = "blocks"
        
        # Find blocks we need
        missing_blocks = []
        for block_hash in self.best_chain:
            if block_hash not in self.blocks:
                missing_blocks.append(block_hash)
        
        if missing_blocks:
            print(f"📋 Need {len(missing_blocks)} blocks")
            self._request_block_inventory(peer_addr, missing_blocks[0])
        else:
            self._start_mempool_sync(peer_addr)
    
    def _request_block_inventory(self, peer_addr: str, from_height_hash: str):
        """Request block inventory"""
        if peer_addr not in self.peer_connections:
            return
        
        try:
            # Find height of from_hash
            from_height = 0
            if from_height_hash in self.headers:
                from_height = self.headers[from_height_hash].height
            
            getblocks_msg = {
                "type": "getblocks",
                "from_height": from_height,
                "node_id": self.node_id
            }
            
            self.peer_connections[peer_addr].send(json.dumps(getblocks_msg).encode())
            print(f"📤 Requested block inventory from height {from_height}")
            
        except Exception as e:
            print(f"❌ Failed to request block inventory: {e}")
    
    def _handle_getblocks(self, message: dict, peer_addr: str) -> dict:
        """Handle getblocks request"""
        from_height = message.get("from_height", 0)
        
        # Send inventory of blocks we have
        available_blocks = []
        
        for i in range(from_height, min(from_height + 500, len(self.best_chain))):
            if i < len(self.best_chain):
                block_hash = self.best_chain[i]
                if block_hash in self.blocks:
                    available_blocks.append(block_hash)
        
        print(f"📤 Sending inventory of {len(available_blocks)} blocks")
        
        return {
            "type": "inv",
            "blocks": available_blocks,
            "count": len(available_blocks)
        }
    
    def _handle_inv(self, message: dict, peer_addr: str):
        """Handle block inventory"""
        available_blocks = message.get("blocks", [])
        
        print(f"📥 Received inventory of {len(available_blocks)} blocks")
        
        # Request blocks we don't have
        needed_blocks = []
        for block_hash in available_blocks:
            if block_hash not in self.blocks and block_hash not in self.requested_blocks:
                needed_blocks.append(block_hash)
                self.requested_blocks.add(block_hash)
        
        # Request blocks in batches
        for block_hash in needed_blocks[:10]:  # Limit concurrent requests
            self._request_block_data(peer_addr, block_hash)
    
    # PHASE 3: Full Block Download
    def _request_block_data(self, peer_addr: str, block_hash: str):
        """Request full block data"""
        if peer_addr not in self.peer_connections:
            return
        
        try:
            getdata_msg = {
                "type": "getdata",
                "block": block_hash,
                "node_id": self.node_id
            }
            
            self.peer_connections[peer_addr].send(json.dumps(getdata_msg).encode())
            print(f"📤 Requested block {block_hash[:16]}...")
            
        except Exception as e:
            print(f"❌ Failed to request block data: {e}")
    
    def _handle_getdata(self, message: dict, peer_addr: str) -> dict:
        """Handle getdata request"""
        block_hash = message.get("block")
        
        if block_hash and block_hash in self.blocks:
            block = self.blocks[block_hash]
            print(f"📤 Sending block {block_hash[:16]}...")
            
            return {
                "type": "block",
                "block": block.to_dict()
            }
        
        return None
    
    def _handle_block(self, message: dict, peer_addr: str):
        """Handle received full block"""
        block_data = message.get("block")
        
        if not block_data:
            return
        
        try:
            block = Block.from_dict(block_data)
            block_hash = block.header.hash
            
            print(f"📥 Received block {block_hash[:16]}... with {len(block.transactions)} transactions")
            
            # Validate block
            if self._validate_block(block):
                self.blocks[block_hash] = block
                self.requested_blocks.discard(block_hash)
                
                # Check if we have all blocks
                missing_count = sum(1 for h in self.best_chain if h not in self.blocks)
                print(f"📊 Blocks remaining: {missing_count}")
                
                if missing_count == 0:
                    print("✅ All blocks downloaded!")
                    self._start_mempool_sync(peer_addr)
            
        except Exception as e:
            print(f"❌ Error processing block: {e}")
    
    def _validate_block(self, block: Block) -> bool:
        """Validate full block"""
        # Check header is known
        if block.header.hash not in self.headers:
            return False
        
        # Validate transactions (basic)
        for tx in block.transactions:
            if not tx.tx_id or not tx.sender or not tx.receiver:
                return False
        
        return True
    
    # PHASE 5: Mempool Sync
    def _start_mempool_sync(self, peer_addr: str):
        """Start mempool sync"""
        print(f"💼 Starting mempool sync with {peer_addr}")
        self.sync_mode = "mempool"
        
        if peer_addr not in self.peer_connections:
            return
        
        try:
            mempool_msg = {
                "type": "mempool",
                "node_id": self.node_id
            }
            
            self.peer_connections[peer_addr].send(json.dumps(mempool_msg).encode())
            
        except Exception as e:
            print(f"❌ Failed to request mempool: {e}")
    
    def _handle_mempool_request(self, message: dict, peer_addr: str) -> dict:
        """Handle mempool request"""
        transactions = [tx.to_dict() for tx in self.mempool.values()]
        
        print(f"📤 Sending {len(transactions)} mempool transactions")
        
        return {
            "type": "tx",
            "transactions": transactions,
            "count": len(transactions)
        }
    
    def _handle_transaction(self, message: dict, peer_addr: str):
        """Handle received transactions"""
        transactions_data = message.get("transactions", [])
        
        if transactions_data:
            print(f"📥 Received {len(transactions_data)} transactions")
            
            for tx_data in transactions_data:
                try:
                    tx = Transaction.from_dict(tx_data)
                    if self._validate_transaction(tx):
                        self.mempool[tx.tx_id] = tx
                except Exception as e:
                    print(f"❌ Invalid transaction: {e}")
        
        # Move to live sync mode
        self.sync_mode = "live"
        self.syncing_with.discard(peer_addr)
        print(f"🎉 Sync complete with {peer_addr}! Now in live mode.")
    
    def _validate_transaction(self, tx: Transaction) -> bool:
        """Validate transaction"""
        if not tx.tx_id or not tx.sender or not tx.receiver:
            return False
        if tx.amount <= 0:
            return False
        return True
    
    # Override peer connection to start sync
    def _handle_peer_messages(self, conn: socket.socket, peer_addr: str):
        """Override to start sync after connection"""
        # Start sync after connection is established
        if peer_addr not in self.syncing_with and self.sync_mode != "live":
            threading.Thread(
                target=lambda: (time.sleep(1), self.start_headers_sync(peer_addr)),
                daemon=True
            ).start()
        
        # Call parent handler
        super()._handle_peer_messages(conn, peer_addr)
    
    def get_sync_status(self) -> dict:
        """Get sync status"""
        missing_blocks = sum(1 for h in self.best_chain if h not in self.blocks)
        
        return {
            "sync_mode": self.sync_mode,
            "chain_height": self.chain_height,
            "chain_tip": self.chain_tip[:16] + "..." if self.chain_tip else "N/A",
            "headers_count": len(self.headers),
            "blocks_count": len(self.blocks),
            "missing_blocks": missing_blocks,
            "mempool_size": len(self.mempool),
            "syncing_with": list(self.syncing_with),
            "best_chain_length": len(self.best_chain)
        }
    
    def add_test_data(self):
        """Add some test blocks and transactions for testing"""
        if len(self.best_chain) > 1:
            return  # Already has test data
        
        print("🧪 Adding test blockchain data...")
        
        # Create a few test blocks
        for i in range(1, 4):
            prev_hash = self.best_chain[-1]
            
            # Create test transactions
            test_txs = []
            for j in range(2):
                tx = Transaction(
                    tx_id=f"tx_{i}_{j}_{random.randint(1000, 9999)}",
                    sender=f"addr_{random.randint(1, 100)}",
                    receiver=f"addr_{random.randint(1, 100)}",
                    amount=random.uniform(1, 100),
                    timestamp=time.time()
                )
                test_txs.append(tx)
            
            # Create block header
            block_hash = hashlib.sha256(f"block_{i}_{time.time()}".encode()).hexdigest()
            header = BlockHeader(
                hash=block_hash,
                prev_hash=prev_hash,
                merkle_root=hashlib.sha256(f"merkle_{i}".encode()).hexdigest(),
                timestamp=time.time(),
                difficulty=1,
                nonce=random.randint(1, 1000000),
                height=i
            )
            
            # Create full block
            block = Block(header=header, transactions=test_txs)
            
            # Add to chain
            self.headers[block_hash] = header
            self.blocks[block_hash] = block
            self.best_chain.append(block_hash)
            self.chain_tip = block_hash
            self.chain_height = i
        
        # Add test mempool transactions
        for i in range(3):
            tx = Transaction(
                tx_id=f"mempool_tx_{i}_{random.randint(1000, 9999)}",
                sender=f"addr_{random.randint(1, 100)}",
                receiver=f"addr_{random.randint(1, 100)}",
                amount=random.uniform(1, 50),
                timestamp=time.time()
            )
            self.mempool[tx.tx_id] = tx
        
        print(f"✅ Test data added: {len(self.best_chain)} blocks, {len(self.mempool)} mempool txs")


def main():
    """Test the Bitcoin sync node"""
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    
    node = BitcoinSyncNode(port=port)
    
    # Add test data to first node
    if port == 5000:
        node.add_test_data()
    
    node.start()
    
    try:
        print(f"\n🔗 Bitcoin Sync Node running on port {port}")
        print("Commands:")
        print("  status  - Show sync status")
        print("  connect <ip> <port> - Connect to peer")
        print("  sync <ip> <port> - Connect and start sync")
        print("  data - Add test data")
        print("  quit - Exit")
        print()
        
        while True:
            try:
                cmd = input(f"sync-{node.node_id}> ").strip().split()
                
                if not cmd:
                    continue
                
                if cmd[0] == "quit":
                    break
                elif cmd[0] == "status":
                    status = node.get_sync_status()
                    print(f"Sync Mode: {status['sync_mode']}")
                    print(f"Chain Height: {status['chain_height']}")
                    print(f"Chain Tip: {status['chain_tip']}")
                    print(f"Headers: {status['headers_count']}")
                    print(f"Blocks: {status['blocks_count']}")
                    print(f"Missing Blocks: {status['missing_blocks']}")
                    print(f"Mempool: {status['mempool_size']}")
                    print(f"Syncing With: {status['syncing_with']}")
                elif cmd[0] == "connect" and len(cmd) == 3:
                    ip, port_str = cmd[1], cmd[2]
                    if node.manual_connect(ip, int(port_str)):
                        print(f"✅ Connected to {ip}:{port_str}")
                    else:
                        print(f"❌ Failed to connect to {ip}:{port_str}")
                elif cmd[0] == "sync" and len(cmd) == 3:
                    ip, port_str = cmd[1], cmd[2]
                    if node.manual_connect(ip, int(port_str)):
                        peer_addr = f"{ip}:{port_str}"
                        node.start_headers_sync(peer_addr)
                        print(f"🔄 Started sync with {ip}:{port_str}")
                    else:
                        print(f"❌ Failed to connect to {ip}:{port_str}")
                elif cmd[0] == "data":
                    node.add_test_data()
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
