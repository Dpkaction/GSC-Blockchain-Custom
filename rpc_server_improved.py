"""
GSC Coin RPC Server - Bitcoin-Compatible JSON-RPC 2.0 Implementation
Secure, robust RPC server with comprehensive API endpoints
"""

import json
import threading
import time
import hashlib
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Any, Optional, Callable
import sys
import os

from gsc_logger import rpc_logger
from thread_safety import RateLimiter, ThreadSafeDict
from rpc_config import rpc_config

class JSONRPCError(Exception):
    """JSON-RPC 2.0 error"""
    
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

# JSON-RPC 2.0 standard error codes
class RPCErrorCodes:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Custom GSC Coin error codes
    WALLET_NOT_LOADED = -1
    INVALID_ADDRESS = -2
    INSUFFICIENT_FUNDS = -3
    INVALID_TRANSACTION = -4
    BLOCK_NOT_FOUND = -5
    TRANSACTION_NOT_FOUND = -6

class GSCRPCHandler(BaseHTTPRequestHandler):
    """JSON-RPC 2.0 request handler with security features"""
    
    # Class-level rate limiter
    rate_limiters = ThreadSafeDict[str, RateLimiter]()
    
    def __init__(self, blockchain, wallet_manager, *args, **kwargs):
        self.blockchain = blockchain
        self.wallet_manager = wallet_manager
        self.rpc_methods = self._register_methods()
        super().__init__(*args, **kwargs)
    
    def _register_methods(self) -> Dict[str, Callable]:
        """Register all RPC methods"""
        return {
            # Blockchain methods
            'getblockchaininfo': self.getblockchaininfo,
            'getblock': self.getblock,
            'getblockhash': self.getblockhash,
            'getblockcount': self.getblockcount,
            'getbestblockhash': self.getbestblockhash,
            'getchaintips': self.getchaintips,
            'getdifficulty': self.getdifficulty,
            
            # Transaction methods
            'getrawtransaction': self.getrawtransaction,
            'sendrawtransaction': self.sendrawtransaction,
            'decoderawtransaction': self.decoderawtransaction,
            'getmempoolinfo': self.getmempoolinfo,
            'getrawmempool': self.getrawmempool,
            
            # Wallet methods
            'getwalletinfo': self.getwalletinfo,
            'getbalance': self.getbalance,
            'listaddressgroupings': self.listaddressgroupings,
            'sendtoaddress': self.sendtoaddress,
            'getnewaddress': self.getnewaddress,
            'validateaddress': self.validateaddress,
            
            # Mining methods
            'getmininginfo': self.getmininginfo,
            'generateblock': self.generateblock,
            'generatetoaddress': self.generatetoaddress,
            
            # Network methods
            'getconnectioncount': self.getconnectioncount,
            'getpeerinfo': self.getpeerinfo,
            'getnetworkinfo': self.getnetworkinfo,
            
            # Utility methods
            'help': self.help,
            'stop': self.stop,
            'uptime': self.uptime
        }
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        pass  # Suppress default logging
    
    def do_GET(self):
        """Handle GET requests"""
        # Add CORS headers for cross-origin requests
        self._add_cors_headers()
        
        if self.path == '/':
            network_info = rpc_config.get_network_info()
            self._send_response({
                "name": "GSC Coin RPC Server",
                "version": "1.0.0",
                "protocol": "JSON-RPC 2.0",
                "methods": list(self.rpc_methods.keys()),
                "description": "Bitcoin-compatible RPC server for GSC Coin",
                "network_info": network_info,
                "external_access": "Enabled - Accepting connections from all IPs",
                "security": "Rate limiting enabled" if rpc_config.config["rate_limit_enabled"] else "No rate limiting"
            })
        elif self.path == '/status':
            connectivity = rpc_config.test_connectivity()
            self._send_response({
                "status": "running",
                "connectivity": connectivity,
                "network_info": rpc_config.get_network_info(),
                "firewall_info": rpc_config.get_firewall_info()
            })
        else:
            self._send_error(404, "Not Found")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self._add_cors_headers()
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests for JSON-RPC calls"""
        try:
            # Add CORS headers
            self._add_cors_headers()
            
            # Check IP allowlist
            client_ip = self.client_address[0]
            if not rpc_config.is_ip_allowed(client_ip):
                self._send_jsonrpc_error(RPCErrorCodes.INVALID_REQUEST, f"IP {client_ip} not allowed")
                return
            
            # Rate limiting
            if rpc_config.config["rate_limit_enabled"] and not self._check_rate_limit(client_ip):
                self._send_jsonrpc_error(RPCErrorCodes.INVALID_REQUEST, "Rate limit exceeded")
                return
            
            # Read and parse request
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_jsonrpc_error(RPCErrorCodes.INVALID_REQUEST, "Empty request")
                return
            
            if content_length > 1024 * 1024:  # 1MB limit
                self._send_jsonrpc_error(RPCErrorCodes.INVALID_REQUEST, "Request too large")
                return
            
            post_data = self.rfile.read(content_length)
            
            try:
                request = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                self._send_jsonrpc_error(RPCErrorCodes.PARSE_ERROR, f"Parse error: {str(e)}")
                return
            
            # Process JSON-RPC request
            response = self._process_jsonrpc_request(request)
            self._send_response(response)
            
        except Exception as e:
            rpc_logger.error(f"RPC request error: {e}")
            self._send_jsonrpc_error(RPCErrorCodes.INTERNAL_ERROR, f"Internal error: {str(e)}")
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is rate limited"""
        if client_ip not in self.rate_limiters:
            max_calls = rpc_config.config["rate_limit_requests"]
            time_window = rpc_config.config["rate_limit_window"]
            self.rate_limiters.set(client_ip, RateLimiter(max_calls=max_calls, time_window=time_window))
        
        return self.rate_limiters.get(client_ip).is_allowed()
    
    def _process_jsonrpc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process JSON-RPC 2.0 request"""
        # Validate JSON-RPC 2.0 format
        if not isinstance(request, dict):
            raise JSONRPCError(RPCErrorCodes.INVALID_REQUEST, "Invalid request format")
        
        jsonrpc_version = request.get('jsonrpc')
        if jsonrpc_version != '2.0':
            raise JSONRPCError(RPCErrorCodes.INVALID_REQUEST, "Unsupported JSON-RPC version")
        
        method = request.get('method')
        if not method or not isinstance(method, str):
            raise JSONRPCError(RPCErrorCodes.INVALID_REQUEST, "Invalid or missing method")
        
        params = request.get('params', [])
        if not isinstance(params, list):
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Parameters must be an array")
        
        request_id = request.get('id')
        
        # Find and call method
        if method not in self.rpc_methods:
            raise JSONRPCError(RPCErrorCodes.METHOD_NOT_FOUND, f"Method '{method}' not found")
        
        try:
            result = self.rpc_methods[method](params)
            
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
            
        except JSONRPCError as e:
            raise e
        except Exception as e:
            rpc_logger.error(f"Method '{method}' error: {e}")
            raise JSONRPCError(RPCErrorCodes.INTERNAL_ERROR, f"Method execution failed: {str(e)}")
    
    def _add_cors_headers(self):
        """Add CORS headers for cross-origin requests"""
        if rpc_config.config["enable_cors"]:
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.send_header('Access-Control-Max-Age', '86400')
    
    def _send_response(self, data: Dict[str, Any]) -> None:
        """Send JSON response"""
        response_json = json.dumps(data, indent=2)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_json)))
        self._add_cors_headers()
        self.end_headers()
        
        self.wfile.write(response_json.encode('utf-8'))
        
        # Log request if enabled
        if rpc_config.config["log_requests"]:
            client_ip = self.client_address[0]
            rpc_logger.info(f"RPC response sent to {client_ip}: {len(response_json)} bytes")
    
    def _send_jsonrpc_error(self, code: int, message: str, data: Any = None) -> None:
        """Send JSON-RPC error response"""
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            },
            "id": None
        }
        
        if data is not None:
            error_response["error"]["data"] = data
        
        self._send_response(error_response)
    
    def _send_error(self, code: int, message: str) -> None:
        """Send HTTP error"""
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
    
    # Blockchain methods
    def getblockchaininfo(self, params: List[Any]) -> Dict[str, Any]:
        """Get blockchain information"""
        latest_block = self.blockchain.get_latest_block()
        
        return {
            "chain": "main",
            "blocks": len(self.blockchain.chain),
            "headers": len(self.blockchain.chain),
            "bestblockhash": latest_block.hash if latest_block else "",
            "difficulty": self.blockchain.difficulty,
            "mediantime": latest_block.timestamp if latest_block else 0,
            "verificationprogress": 1.0,
            "chainwork": "0000000000000000000000000000000000000000000000000000000000000000",
            "size_on_disk": 0,
            "pruned": False,
            "softforks": [],
            "bip9_softforks": {}
        }
    
    def getblock(self, params: List[Any]) -> Dict[str, Any]:
        """Get block by hash or height"""
        if not params:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Block hash or height required")
        
        block_identifier = params[0]
        verbosity = params[1] if len(params) > 1 else 1
        
        block = None
        
        # Try to find by height first
        try:
            height = int(block_identifier)
            if 0 <= height < len(self.blockchain.chain):
                block = self.blockchain.chain[height]
        except ValueError:
            pass
        
        # Try to find by hash
        if not block:
            block = self.blockchain.get_block_by_hash(str(block_identifier))
        
        if not block:
            raise JSONRPCError(RPCErrorCodes.BLOCK_NOT_FOUND, "Block not found")
        
        if verbosity == 0:
            return block.hash
        
        return {
            "hash": block.hash,
            "confirmations": len(self.blockchain.chain) - block.index,
            "height": block.index,
            "version": 1,
            "versionHex": "00000001",
            "merkleroot": block.merkle_root,
            "time": block.timestamp,
            "mediantime": block.timestamp,
            "nonce": block.nonce,
            "bits": f"{block.difficulty:08x}",
            "difficulty": block.difficulty,
            "chainwork": "0000000000000000000000000000000000000000000000000000000000000000",
            "previousblockhash": block.previous_hash if block.index > 0 else None,
            "nextblockhash": self.blockchain.chain[block.index + 1].hash if block.index + 1 < len(self.blockchain.chain) else None,
            "strippedsize": 0,
            "size": 0,
            "weight": 0,
            "tx": [tx.tx_id for tx in block.transactions]
        }
    
    def getblockhash(self, params: List[Any]) -> str:
        """Get block hash by height"""
        if not params:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Height required")
        
        try:
            height = int(params[0])
            if height < 0 or height >= len(self.blockchain.chain):
                raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Block height out of range")
            
            return self.blockchain.chain[height].hash
        except ValueError:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Invalid height")
    
    def getblockcount(self, params: List[Any]) -> int:
        """Get block count"""
        return len(self.blockchain.chain)
    
    def getbestblockhash(self, params: List[Any]) -> str:
        """Get best block hash"""
        latest = self.blockchain.get_latest_block()
        return latest.hash if latest else ""
    
    def getchaintips(self, params: List[Any]) -> List[Dict[str, Any]]:
        """Get chain tips"""
        latest = self.blockchain.get_latest_block()
        return [{
            "height": latest.index if latest else 0,
            "hash": latest.hash if latest else "",
            "branchlen": 0,
            "status": "active"
        }]
    
    def getdifficulty(self, params: List[Any]) -> float:
        """Get difficulty"""
        return float(self.blockchain.difficulty)
    
    # Transaction methods
    def getrawtransaction(self, params: List[Any]) -> str:
        """Get raw transaction"""
        if not params:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Transaction ID required")
        
        tx_id = params[0]
        verbose = params[1] if len(params) > 1 else 0
        
        result = self.blockchain.get_transaction_by_hash(tx_id)
        if not result:
            raise JSONRPCError(RPCErrorCodes.TRANSACTION_NOT_FOUND, "Transaction not found")
        
        tx, block_height = result
        
        if verbose == 0:
            return json.dumps(tx.to_dict())
        
        return {
            "txid": tx.tx_id,
            "hash": tx.tx_id,
            "version": 1,
            "size": 0,
            "vsize": 0,
            "weight": 0,
            "locktime": 0,
            "vin": [{
                "txid": "",
                "vout": 0,
                "scriptSig": {
                    "asm": "",
                    "hex": ""
                },
                "sequence": 4294967295
            }],
            "vout": [{
                "value": tx.amount,
                "n": 0,
                "scriptPubKey": {
                    "asm": f"OP_DUP OP_HASH160 {hashlib.sha256(tx.receiver.encode()).hexdigest()} OP_EQUALVERIFY OP_CHECKSIG",
                    "hex": "",
                    "reqSigs": 1,
                    "type": "pubkeyhash",
                    "addresses": [tx.receiver]
                }
            }],
            "hex": json.dumps(tx.to_dict()),
            "blockhash": self.blockchain.chain[block_height].hash if block_height >= 0 else "",
            "confirmations": (len(self.blockchain.chain) - block_height) if block_height >= 0 else 0,
            "time": tx.timestamp,
            "blocktime": self.blockchain.chain[block_height].timestamp if block_height >= 0 else tx.timestamp
        }
    
    def sendrawtransaction(self, params: List[Any]) -> str:
        """Send raw transaction"""
        if not params:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Transaction hex required")
        
        try:
            tx_data = json.loads(params[0])
            from blockchain_improved import Transaction
            
            tx = Transaction(**tx_data)
            
            if self.blockchain.add_transaction_to_mempool(tx):
                rpc_logger.info(f"Transaction sent: {tx.tx_id}")
                return tx.tx_id
            else:
                raise JSONRPCError(RPCErrorCodes.INVALID_TRANSACTION, "Transaction rejected")
                
        except Exception as e:
            raise JSONRPCError(RPCErrorCodes.INVALID_TRANSACTION, f"Invalid transaction: {str(e)}")
    
    def decoderawtransaction(self, params: List[Any]) -> Dict[str, Any]:
        """Decode raw transaction"""
        if not params:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Transaction hex required")
        
        try:
            tx_data = json.loads(params[0])
            return tx_data
        except Exception as e:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, f"Invalid transaction: {str(e)}")
    
    def getmempoolinfo(self, params: List[Any]) -> Dict[str, Any]:
        """Get mempool information"""
        return {
            "size": len(self.blockchain.mempool),
            "bytes": 0,
            "usage": 0,
            "maxmempool": 100000000,
            "mempoolminfee": 0.00001,
            "minrelaytxfee": 0.00001
        }
    
    def getrawmempool(self, params: List[Any]) -> List[str]:
        """Get raw mempool"""
        verbose = params[0] if len(params) > 0 else False
        
        if verbose:
            return [tx.to_dict() for tx in self.blockchain.mempool]
        else:
            return [tx.tx_id for tx in self.blockchain.mempool]
    
    # Wallet methods
    def getwalletinfo(self, params: List[Any]) -> Dict[str, Any]:
        """Get wallet information"""
        if not self.wallet_manager or not self.wallet_manager.current_wallet:
            raise JSONRPCError(RPCErrorCodes.WALLET_NOT_LOADED, "Wallet not loaded")
        
        wallet_info = self.wallet_manager.get_wallet_info()
        balance = sum(self.blockchain.get_balance(addr) for addr in self.wallet_manager.get_receiving_addresses())
        
        return {
            "walletname": wallet_info.get('name', ''),
            "walletversion": 169900,
            "balance": balance,
            "unconfirmed_balance": 0,
            "immature_balance": 0,
            "txcount": 0,
            "keypoolsize": 1000,
            "keypoolsize_hd_internal": 1000,
            "paytxfee": 0.00000,
            "private_keys_enabled": True,
            "avoid_reuse": False,
            "scanning": False
        }
    
    def getbalance(self, params: List[Any]) -> float:
        """Get balance"""
        if not self.wallet_manager or not self.wallet_manager.current_wallet:
            raise JSONRPCError(RPCErrorCodes.WALLET_NOT_LOADED, "Wallet not loaded")
        
        account = params[0] if len(params) > 0 else "*"
        minconf = params[1] if len(params) > 1 else 1
        
        if account == "*":
            # Get total balance across all addresses
            addresses = self.wallet_manager.get_receiving_addresses()
            return sum(self.blockchain.get_balance(addr) for addr in addresses)
        else:
            # Get balance for specific address
            return self.blockchain.get_balance(account)
    
    def listaddressgroupings(self, params: List[Any]) -> List[List[List[str]]]:
        """List address groupings"""
        if not self.wallet_manager or not self.wallet_manager.current_wallet:
            raise JSONRPCError(RPCErrorCodes.WALLET_NOT_LOADED, "Wallet not loaded")
        
        addresses = self.wallet_manager.get_receiving_addresses()
        groups = []
        
        for addr in addresses:
            balance = self.blockchain.get_balance(addr)
            if balance > 0:
                groups.append([[addr, balance, ""]])
        
        return groups
    
    def sendtoaddress(self, params: List[Any]) -> str:
        """Send to address"""
        if not self.wallet_manager or not self.wallet_manager.current_wallet:
            raise JSONRPCError(RPCErrorCodes.WALLET_NOT_LOADED, "Wallet not loaded")
        
        if len(params) < 2:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Address and amount required")
        
        address = params[0]
        amount = float(params[1])
        comment = params[2] if len(params) > 2 else ""
        comment_to = params[3] if len(params) > 3 else ""
        subtractfeefromamount = params[4] if len(params) > 4 else False
        
        # Get a sending address
        sending_addresses = self.wallet_manager.get_sending_addresses()
        if not sending_addresses:
            raise JSONRPCError(RPCErrorCodes.INSUFFICIENT_FUNDS, "No sending addresses available")
        
        sender = sending_addresses[0]  # Use first sending address
        
        # Create and send transaction
        from blockchain_improved import Transaction
        
        tx = Transaction(
            sender=sender,
            receiver=address,
            amount=amount,
            fee=0.0001,  # Default fee
            timestamp=time.time()
        )
        
        if self.blockchain.add_transaction_to_mempool(tx):
            rpc_logger.info(f"Sent {amount} GSC to {address}")
            return tx.tx_id
        else:
            raise JSONRPCError(RPCErrorCodes.INSUFFICIENT_FUNDS, "Insufficient funds")
    
    def getnewaddress(self, params: List[Any]) -> str:
        """Get new address"""
        if not self.wallet_manager or not self.wallet_manager.current_wallet:
            raise JSONRPCError(RPCErrorCodes.WALLET_NOT_LOADED, "Wallet not loaded")
        
        label = params[0] if len(params) > 0 else ""
        address_type = params[1] if len(params) > 1 else "legacy"
        
        # Generate new address
        addresses = self.wallet_manager.get_receiving_addresses()
        if addresses:
            return addresses[0]  # Return first address for simplicity
        
        # If no addresses, create a new wallet
        wallet_info = self.wallet_manager.create_wallet("default")
        return wallet_info['address']
    
    def validateaddress(self, params: List[Any]) -> Dict[str, Any]:
        """Validate address"""
        if not params:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Address required")
        
        address = params[0]
        
        # Simple validation - in a real implementation, this would validate the address format
        is_valid = len(address) > 20 and address.startswith("GSC")
        
        return {
            "isvalid": is_valid,
            "address": address if is_valid else None,
            "scriptPubKey": "" if is_valid else None,
            "isscript": False,
            "iswitness": False,
            "witness_version": -1,
            "witness_program": None
        }
    
    # Mining methods
    def getmininginfo(self, params: List[Any]) -> Dict[str, Any]:
        """Get mining information"""
        return {
            "blocks": len(self.blockchain.chain),
            "currentblocksize": 0,
            "currentblocktx": len(self.blockchain.mempool),
            "difficulty": float(self.blockchain.difficulty),
            "networkhashps": 0,
            "pooledtx": len(self.blockchain.mempool),
            "chain": "main",
            "warnings": ""
        }
    
    def generateblock(self, params: List[Any]) -> str:
        """Generate block"""
        if not params or len(params) < 2:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Output and transactions required")
        
        output = params[0]
        transactions = params[1]
        
        # Create block with transactions
        from blockchain_improved import Transaction
        
        tx_list = []
        for tx_data in transactions:
            tx = Transaction(**tx_data)
            tx_list.append(tx)
        
        # Mine block
        latest = self.blockchain.get_latest_block()
        if not latest:
            raise JSONRPCError(RPCErrorCodes.INTERNAL_ERROR, "No latest block")
        
        block = self.blockchain.create_new_block(output)
        block.transactions = tx_list + block.transactions  # Add transactions before coinbase
        
        # Mine the block
        block.mine_block(self.blockchain.difficulty, output)
        
        if self.blockchain.add_block(block):
            return block.hash
        else:
            raise JSONRPCError(RPCErrorCodes.INTERNAL_ERROR, "Failed to add block")
    
    def generatetoaddress(self, params: List[Any]) -> List[str]:
        """Generate blocks to address"""
        if not params or len(params) < 2:
            raise JSONRPCError(RPCErrorCodes.INVALID_PARAMS, "Number of blocks and address required")
        
        nblocks = int(params[0])
        address = params[1]
        
        block_hashes = []
        
        for _ in range(nblocks):
            block = self.blockchain.mine_pending_transactions(address)
            if block:
                block_hashes.append(block.hash)
            else:
                break
        
        return block_hashes
    
    # Network methods
    def getconnectioncount(self, params: List[Any]) -> int:
        """Get connection count"""
        if hasattr(self.blockchain, 'network_node') and self.blockchain.network_node:
            return len(self.blockchain.network_node.peers)
        return 0
    
    def getpeerinfo(self, params: List[Any]) -> List[Dict[str, Any]]:
        """Get peer information"""
        if hasattr(self.blockchain, 'network_node') and self.blockchain.network_node:
            return self.blockchain.network_node.get_peer_list()
        return []
    
    def getnetworkinfo(self, params: List[Any]) -> Dict[str, Any]:
        """Get network information"""
        if hasattr(self.blockchain, 'network_node') and self.blockchain.network_node:
            network_info = self.blockchain.network_node.get_network_info()
            return {
                "version": 170000,
                "subversion": "/GSCCoin:1.0.0/",
                "protocolversion": 70015,
                "localservices": "0000000000000001",
                "localrelay": True,
                "timeoffset": 0,
                "networkactive": True,
                "connections": network_info['connected_peers'],
                "networks": [{
                    "name": "ipv4",
                    "limited": False,
                    "reachable": True,
                    "proxy": "",
                    "proxy_randomize_credentials": False
                }],
                "relayfee": 0.00001,
                "incrementalfee": 0.00001,
                "localaddresses": [],
                "warnings": ""
            }
        
        return {
            "version": 170000,
            "subversion": "/GSCCoin:1.0.0/",
            "protocolversion": 70015,
            "connections": 0,
            "networks": [],
            "warnings": "No network node available"
        }
    
    # Utility methods
    def help(self, params: List[Any]) -> str:
        """Get help information"""
        if params:
            method = params[0]
            if method in self.rpc_methods:
                return f"Help for {method}: See Bitcoin RPC documentation for similar method"
            else:
                raise JSONRPCError(RPCErrorCodes.METHOD_NOT_FOUND, f"Method '{method}' not found")
        
        return "Available methods: " + ", ".join(sorted(self.rpc_methods.keys()))
    
    def stop(self, params: List[Any]) -> str:
        """Stop the RPC server"""
        rpc_logger.info("RPC server stop requested")
        return "GSC Coin server stopping"
    
    def uptime(self, params: List[Any]) -> int:
        """Get server uptime"""
        return int(time.time() - getattr(self, 'start_time', time.time()))

class GSCRPCServer:
    """GSC Coin RPC Server with security and monitoring"""
    
    def __init__(self, blockchain, wallet_manager, host: str = '0.0.0.0', port: int = 8332):
        self.blockchain = blockchain
        self.wallet_manager = wallet_manager
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.start_time = time.time()
        self.running = False
    
    def start(self) -> bool:
        """Start RPC server"""
        try:
            # Create handler with blockchain and wallet manager
            def handler(*args, **kwargs):
                h = GSCRPCHandler(self.blockchain, self.wallet_manager, *args, **kwargs)
                h.start_time = self.start_time
                return h
            
            self.server = HTTPServer((self.host, self.port), handler)
            self.running = True
            
            # Start server in separate thread
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            rpc_logger.info(f"RPC Server started on http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            rpc_logger.error(f"Failed to start RPC server: {e}")
            return False
    
    def _run_server(self) -> None:
        """Run the server"""
        try:
            self.server.serve_forever()
        except Exception as e:
            if self.running:
                rpc_logger.error(f"RPC server error: {e}")
    
    def stop(self) -> None:
        """Stop RPC server"""
        self.running = False
        
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        if self.server_thread:
            self.server_thread.join(timeout=5)
        
        rpc_logger.info("RPC Server stopped")
    
    def is_running(self) -> bool:
        """Check if server is running"""
        return self.running and self.server_thread and self.server_thread.is_alive()

# Example usage and testing
if __name__ == "__main__":
    # Test the RPC server
    from blockchain_improved import GSCBlockchain
    from wallet_manager import WalletManager
    
    blockchain = GSCBlockchain()
    wallet_manager = WalletManager()
    
    rpc_server = GSCRPCServer(blockchain, wallet_manager)
    
    if rpc_server.start():
        print("GSC Coin RPC Server is running...")
        print("Test with: curl -X POST -H 'Content-Type: application/json' \\")
        print("  -d '{\"jsonrpc\":\"2.0\",\"method\":\"getblockchaininfo\",\"id\":1}' \\")
        print(f"  http://{rpc_server.host}:{rpc_server.port}/")
        
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            rpc_server.stop()
    else:
        print("Failed to start RPC server")
