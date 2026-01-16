"""
GSC Coin Mempool Synchronization System
Real-time mempool sharing across all network nodes
"""

import time
import threading
import logging
from typing import Dict, List, Set
from .mainnet_blockchain import MainnetTransaction
from .mainnet_network import MainnetNetworkNode, NetworkMessage

logger = logging.getLogger(__name__)

class MempoolSyncManager:
    """Manages mempool synchronization across the network"""
    
    def __init__(self, blockchain, network: MainnetNetworkNode):
        self.blockchain = blockchain
        self.network = network
        self.running = False
        self.sync_thread = None
        
        # Track transaction propagation
        self.transaction_sources: Dict[str, str] = {}  # tx_id -> source_peer
        self.propagation_times: Dict[str, float] = {}  # tx_id -> timestamp
        
        # Sync settings
        self.sync_interval = 30  # seconds
        self.max_mempool_age = 3600  # 1 hour
        
    def start(self):
        """Start mempool synchronization"""
        if self.running:
            return
            
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        logger.info("Mempool synchronization started")
    
    def stop(self):
        """Stop mempool synchronization"""
        if not self.running:
            return
            
        self.running = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
            
        logger.info("Mempool synchronization stopped")
    
    def _sync_loop(self):
        """Main synchronization loop"""
        while self.running:
            try:
                # Request mempool from all peers
                self._request_mempool_from_peers()
                
                # Clean old transactions
                self._clean_old_transactions()
                
                # Broadcast our mempool to new peers
                self._broadcast_mempool_to_new_peers()
                
                time.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"Mempool sync error: {e}")
                time.sleep(60)
    
    def _request_mempool_from_peers(self):
        """Request mempool from all connected peers"""
        mempool_request = NetworkMessage(NetworkMessage.MEMPOOL, {})
        
        with self.network.lock:
            for peer in self.network.peers.values():
                if peer.is_alive:
                    peer.send_message(mempool_request)
    
    def _clean_old_transactions(self):
        """Remove old transactions from mempool"""
        current_time = time.time()
        
        with self.blockchain.lock:
            old_transactions = []
            for tx in self.blockchain.mempool:
                if current_time - tx.timestamp > self.max_mempool_age:
                    old_transactions.append(tx)
            
            for tx in old_transactions:
                self.blockchain.mempool.remove(tx)
                logger.info(f"Removed old transaction from mempool: {tx.tx_id}")
    
    def _broadcast_mempool_to_new_peers(self):
        """Broadcast our mempool to newly connected peers"""
        if not self.blockchain.mempool:
            return
            
        mempool_data = [tx.to_dict() for tx in self.blockchain.mempool]
        mempool_msg = NetworkMessage(NetworkMessage.MEMPOOL, {'transactions': mempool_data})
        
        with self.network.lock:
            for peer in self.network.peers.values():
                if peer.is_alive and time.time() - peer.connected_at < 60:  # New peer
                    peer.send_message(mempool_msg)
    
    def add_transaction_to_network(self, transaction: MainnetTransaction) -> bool:
        """Add transaction to local mempool and broadcast to network"""
        try:
            # Add to local mempool
            success, message = self.blockchain.add_transaction_to_mempool(transaction)
            
            if success:
                # Record transaction details
                self.transaction_sources[transaction.tx_id] = "local"
                self.propagation_times[transaction.tx_id] = time.time()
                
                # Broadcast to all peers immediately
                self._broadcast_transaction(transaction)
                
                logger.info(f"Transaction {transaction.tx_id} added to network mempool")
                return True
            else:
                logger.warning(f"Failed to add transaction to mempool: {message}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding transaction to network: {e}")
            return False
    
    def _broadcast_transaction(self, transaction: MainnetTransaction):
        """Broadcast transaction to all connected peers"""
        tx_msg = NetworkMessage(NetworkMessage.TX, {'transaction': transaction.to_dict()})
        
        broadcast_count = 0
        with self.network.lock:
            for peer in self.network.peers.values():
                if peer.is_alive:
                    if peer.send_message(tx_msg):
                        broadcast_count += 1
        
        logger.info(f"Broadcasted transaction {transaction.tx_id} to {broadcast_count} peers")
    
    def handle_incoming_mempool(self, peer_address: str, transactions: List[dict]):
        """Handle incoming mempool data from peer"""
        added_count = 0
        
        for tx_data in transactions:
            try:
                transaction = MainnetTransaction(**tx_data)
                
                # Check if we already have this transaction
                existing_tx = any(tx.tx_id == transaction.tx_id for tx in self.blockchain.mempool)
                
                if not existing_tx:
                    success, _ = self.blockchain.add_transaction_to_mempool(transaction)
                    if success:
                        self.transaction_sources[transaction.tx_id] = peer_address
                        self.propagation_times[transaction.tx_id] = time.time()
                        added_count += 1
                        
                        # Relay to other peers (except source)
                        self._relay_transaction_except_source(transaction, peer_address)
                        
            except Exception as e:
                logger.error(f"Error processing mempool transaction: {e}")
        
        if added_count > 0:
            logger.info(f"Added {added_count} new transactions from peer {peer_address}")
    
    def _relay_transaction_except_source(self, transaction: MainnetTransaction, source_peer: str):
        """Relay transaction to all peers except the source"""
        tx_msg = NetworkMessage(NetworkMessage.TX, {'transaction': transaction.to_dict()})
        
        relay_count = 0
        with self.network.lock:
            for peer in self.network.peers.values():
                peer_addr = f"{peer.address[0]}:{peer.address[1]}"
                if peer.is_alive and peer_addr != source_peer:
                    if peer.send_message(tx_msg):
                        relay_count += 1
        
        logger.debug(f"Relayed transaction {transaction.tx_id} to {relay_count} peers")
    
    def get_mempool_stats(self) -> Dict:
        """Get mempool statistics"""
        current_time = time.time()
        
        stats = {
            'total_transactions': len(self.blockchain.mempool),
            'total_fees': sum(tx.fee for tx in self.blockchain.mempool),
            'average_fee': 0,
            'oldest_transaction': None,
            'newest_transaction': None,
            'transaction_sources': {},
            'propagation_stats': {}
        }
        
        if self.blockchain.mempool:
            stats['average_fee'] = stats['total_fees'] / len(self.blockchain.mempool)
            
            # Find oldest and newest
            oldest_tx = min(self.blockchain.mempool, key=lambda tx: tx.timestamp)
            newest_tx = max(self.blockchain.mempool, key=lambda tx: tx.timestamp)
            
            stats['oldest_transaction'] = {
                'tx_id': oldest_tx.tx_id,
                'age_seconds': current_time - oldest_tx.timestamp
            }
            
            stats['newest_transaction'] = {
                'tx_id': newest_tx.tx_id,
                'age_seconds': current_time - newest_tx.timestamp
            }
            
            # Source statistics
            source_counts = {}
            for tx in self.blockchain.mempool:
                source = self.transaction_sources.get(tx.tx_id, 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
            
            stats['transaction_sources'] = source_counts
        
        return stats
    
    def force_mempool_sync(self):
        """Force immediate mempool synchronization"""
        logger.info("Forcing mempool synchronization...")
        self._request_mempool_from_peers()
        time.sleep(2)  # Wait for responses
        self._broadcast_mempool_to_new_peers()

class SmartMiner:
    """Smart mining that only mines when transactions are available"""
    
    def __init__(self, blockchain, network: MainnetNetworkNode, mempool_sync: MempoolSyncManager):
        self.blockchain = blockchain
        self.network = network
        self.mempool_sync = mempool_sync
        self.mining_address = None
        self.is_mining = False
        self.mining_thread = None
        self.min_transactions = 1  # Minimum transactions before mining
        self.max_wait_time = 300  # Maximum wait time (5 minutes)
        
    def start_mining(self, mining_address: str):
        """Start smart mining"""
        if self.is_mining:
            logger.warning("Mining already in progress")
            return
            
        self.mining_address = mining_address
        self.is_mining = True
        
        self.mining_thread = threading.Thread(target=self._smart_mining_loop, daemon=True)
        self.mining_thread.start()
        
        logger.info(f"Smart mining started for address: {mining_address}")
    
    def stop_mining(self):
        """Stop mining"""
        if not self.is_mining:
            return
            
        self.is_mining = False
        if self.mining_thread and self.mining_thread.is_alive():
            self.mining_thread.join(timeout=5)
            
        logger.info("Smart mining stopped")
    
    def _smart_mining_loop(self):
        """Smart mining loop - only mines when transactions are available"""
        last_mine_time = time.time()
        
        while self.is_mining:
            try:
                current_time = time.time()
                mempool_size = len(self.blockchain.mempool)
                
                # Check if we should mine
                should_mine = (
                    mempool_size >= self.min_transactions or  # Have enough transactions
                    (mempool_size > 0 and current_time - last_mine_time > self.max_wait_time)  # Or waited too long
                )
                
                if should_mine:
                    logger.info(f"Starting to mine block with {mempool_size} transactions")
                    
                    # Mine the block
                    def mining_callback(stats):
                        if stats['nonce'] % 10000 == 0:
                            logger.debug(f"Mining: nonce={stats['nonce']}, rate={stats['hash_rate']:.0f} H/s")
                    
                    new_block = self.blockchain.mine_pending_transactions(
                        self.mining_address, 
                        mining_callback
                    )
                    
                    if new_block:
                        logger.info(f"Successfully mined block {new_block.index}!")
                        logger.info(f"Block hash: {new_block.hash}")
                        logger.info(f"Transactions in block: {len(new_block.transactions)}")
                        logger.info(f"Mining reward: {new_block.reward} GSC")
                        
                        # Broadcast the new block
                        self.network.broadcast_block(new_block)
                        
                        # Save blockchain
                        self.blockchain.save_blockchain()
                        
                        last_mine_time = current_time
                    else:
                        logger.warning("Mining failed or no transactions available")
                else:
                    # Wait for transactions
                    if mempool_size == 0:
                        logger.debug("Waiting for transactions in mempool...")
                    else:
                        logger.debug(f"Waiting for more transactions ({mempool_size}/{self.min_transactions})")
                
                # Sleep before next check
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Smart mining error: {e}")
                time.sleep(30)  # Wait longer on error
