"""
GSC Coin Mainnet API Server
RESTful API for blockchain interaction
"""

import json
import time
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import threading
from .config import Config
from .mainnet_blockchain import MainnetBlockchain, MainnetTransaction
from .mainnet_network import MainnetNetworkNode
from .mainnet_wallet import MainnetWalletManager

logger = logging.getLogger(__name__)

class MainnetAPIServer:
    """Production-ready API server for GSC blockchain"""
    
    def __init__(self, blockchain: MainnetBlockchain, network: MainnetNetworkNode, wallet_manager: MainnetWalletManager):
        self.blockchain = blockchain
        self.network = network
        self.wallet_manager = wallet_manager
        
        # Create Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'gsc-mainnet-api-secret'
        
        # Enable CORS
        CORS(self.app)
        
        # Rate limiting
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=[f"{Config.API_RATE_LIMIT} per minute"]
        )
        
        # Set up routes
        self._setup_routes()
        
        self.server_thread = None
        self.running = False
    
    def _setup_routes(self):
        """Set up API routes"""
        
        @self.app.route('/api/v1/info', methods=['GET'])
        def get_blockchain_info():
            """Get blockchain information"""
            try:
                info = self.blockchain.get_blockchain_info()
                return jsonify({
                    'success': True,
                    'data': info
                })
            except Exception as e:
                logger.error(f"API error in get_blockchain_info: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/blocks', methods=['GET'])
        def get_blocks():
            """Get blocks with pagination"""
            try:
                start = int(request.args.get('start', 0))
                limit = min(int(request.args.get('limit', 10)), 100)
                
                blocks = []
                for i in range(start, min(start + limit, len(self.blockchain.chain))):
                    if i < len(self.blockchain.chain):
                        blocks.append(self.blockchain.chain[i].to_dict())
                
                return jsonify({
                    'success': True,
                    'data': {
                        'blocks': blocks,
                        'total': len(self.blockchain.chain),
                        'start': start,
                        'limit': limit
                    }
                })
            except Exception as e:
                logger.error(f"API error in get_blocks: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/blocks/<int:block_index>', methods=['GET'])
        def get_block(block_index):
            """Get specific block by index"""
            try:
                if block_index < 0 or block_index >= len(self.blockchain.chain):
                    return jsonify({
                        'success': False,
                        'error': 'Block not found'
                    }), 404
                
                block = self.blockchain.chain[block_index]
                return jsonify({
                    'success': True,
                    'data': block.to_dict()
                })
            except Exception as e:
                logger.error(f"API error in get_block: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/balance/<address>', methods=['GET'])
        def get_balance(address):
            """Get balance for an address"""
            try:
                balance = self.blockchain.get_balance(address)
                return jsonify({
                    'success': True,
                    'data': {
                        'address': address,
                        'balance': balance
                    }
                })
            except Exception as e:
                logger.error(f"API error in get_balance: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/mempool', methods=['GET'])
        def get_mempool():
            """Get mempool transactions"""
            try:
                transactions = [tx.to_dict() for tx in self.blockchain.mempool]
                return jsonify({
                    'success': True,
                    'data': {
                        'transactions': transactions,
                        'count': len(transactions),
                        'total_fees': sum(tx.fee for tx in self.blockchain.mempool)
                    }
                })
            except Exception as e:
                logger.error(f"API error in get_mempool: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/transactions', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def submit_transaction():
            """Submit a new transaction"""
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['sender', 'receiver', 'amount', 'fee', 'signature']
                for field in required_fields:
                    if field not in data:
                        return jsonify({
                            'success': False,
                            'error': f'Missing required field: {field}'
                        }), 400
                
                # Create transaction
                transaction = MainnetTransaction(
                    sender=data['sender'],
                    receiver=data['receiver'],
                    amount=float(data['amount']),
                    fee=float(data['fee']),
                    timestamp=time.time(),
                    signature=data['signature']
                )
                
                # Add to mempool
                success, message = self.blockchain.add_transaction_to_mempool(transaction)
                
                if success:
                    # Relay to network
                    self.network._relay_transaction(transaction)
                    
                    return jsonify({
                        'success': True,
                        'data': {
                            'tx_id': transaction.tx_id,
                            'message': message
                        }
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': message
                    }), 400
                    
            except Exception as e:
                logger.error(f"API error in submit_transaction: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/network', methods=['GET'])
        def get_network_info():
            """Get network information"""
            try:
                info = self.network.get_network_info()
                return jsonify({
                    'success': True,
                    'data': info
                })
            except Exception as e:
                logger.error(f"API error in get_network_info: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/peers', methods=['GET'])
        def get_peers():
            """Get connected peers"""
            try:
                peers = []
                for peer in self.network.peers.values():
                    peers.append(peer.get_stats())
                
                return jsonify({
                    'success': True,
                    'data': {
                        'peers': peers,
                        'count': len(peers)
                    }
                })
            except Exception as e:
                logger.error(f"API error in get_peers: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/wallets', methods=['GET'])
        def get_wallets():
            """Get wallet list"""
            try:
                wallets = []
                for name in self.wallet_manager.list_wallets():
                    info = self.wallet_manager.get_wallet_info(name)
                    if info:
                        wallets.append(info)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'wallets': wallets,
                        'count': len(wallets)
                    }
                })
            except Exception as e:
                logger.error(f"API error in get_wallets: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/wallets', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def create_wallet():
            """Create a new wallet"""
            try:
                data = request.get_json()
                
                if 'name' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Wallet name required'
                    }), 400
                
                name = data['name']
                password = data.get('password')
                
                wallet = self.wallet_manager.create_wallet(name, password)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'name': wallet.name,
                        'address': wallet.address,
                        'is_encrypted': wallet.is_encrypted
                    }
                })
                
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 400
            except Exception as e:
                logger.error(f"API error in create_wallet: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/validate', methods=['POST'])
        def validate_chain():
            """Validate blockchain"""
            try:
                is_valid, message = self.blockchain.is_chain_valid()
                return jsonify({
                    'success': True,
                    'data': {
                        'is_valid': is_valid,
                        'message': message
                    }
                })
            except Exception as e:
                logger.error(f"API error in validate_chain: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/v1/stats', methods=['GET'])
        def get_stats():
            """Get comprehensive statistics"""
            try:
                blockchain_info = self.blockchain.get_blockchain_info()
                network_info = self.network.get_network_info()
                
                stats = {
                    'blockchain': {
                        'height': len(self.blockchain.chain),
                        'difficulty': self.blockchain.difficulty,
                        'total_supply': blockchain_info['total_supply'],
                        'mempool_size': len(self.blockchain.mempool),
                        'is_valid': blockchain_info['is_valid']
                    },
                    'network': {
                        'peers_connected': network_info['peers_connected'],
                        'uptime': network_info['uptime'],
                        'bytes_sent': network_info['stats']['bytes_sent'],
                        'bytes_received': network_info['stats']['bytes_received']
                    },
                    'node': {
                        'version': '1.0.0',
                        'network_name': Config.NETWORK_NAME,
                        'is_mainnet': Config.is_mainnet()
                    }
                }
                
                return jsonify({
                    'success': True,
                    'data': stats
                })
            except Exception as e:
                logger.error(f"API error in get_stats: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.errorhandler(429)
        def ratelimit_handler(e):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded'
            }), 429
        
        @self.app.errorhandler(404)
        def not_found_handler(e):
            return jsonify({
                'success': False,
                'error': 'Endpoint not found'
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error_handler(e):
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    def start(self, host: str = None, port: int = None):
        """Start the API server"""
        if self.running:
            return
        
        host = host or Config.API_HOST
        port = port or Config.API_PORT
        
        self.running = True
        
        def run_server():
            self.app.run(
                host=host,
                port=port,
                debug=False,
                threaded=True,
                use_reloader=False
            )
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        logger.info(f"API server started on {host}:{port}")
    
    def stop(self):
        """Stop the API server"""
        if not self.running:
            return
        
        self.running = False
        logger.info("API server stopped")
