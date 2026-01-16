#!/usr/bin/env python3
"""
GSC Coin Console Interface
Interactive console for managing GSC Blockchain with all RPC commands
"""

import sys
import os
import time
import json
import argparse
from typing import Dict, List, Any, Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class GSCConsole:
    """Interactive console for GSC Blockchain management"""
    
    def __init__(self):
        self.blockchain = None
        self.network_node = None
        self.wallet_manager = None
        self.rpc_server = None
        self.running = False
        
    def initialize(self):
        """Initialize blockchain components"""
        try:
            print("🔧 Initializing GSC Blockchain components...")
            
            from blockchain_improved import GSCBlockchain
            from network_improved import GSCNetworkNode
            from wallet_manager import WalletManager
            from rpc_server_improved import GSCRPCServer
            
            self.blockchain = GSCBlockchain()
            self.network_node = GSCNetworkNode(self.blockchain)
            self.wallet_manager = WalletManager()
            self.rpc_server = GSCRPCServer(self.blockchain, self.wallet_manager)
            
            print("✅ Components initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            return False
    
    def start_services(self):
        """Start network and RPC services"""
        try:
            print("🚀 Starting services...")
            
            # Start network node
            if self.network_node.start_server():
                print("✅ Network node started on port 8333")
            else:
                print("⚠️ Network node failed to start")
            
            # Start RPC server
            if self.rpc_server.start():
                print("✅ RPC server started on http://localhost:8332")
            else:
                print("⚠️ RPC server failed to start")
                
            return True
            
        except Exception as e:
            print(f"❌ Failed to start services: {e}")
            return False
    
    def format_output(self, data: Any, title: str = "") -> None:
        """Format output for better readability"""
        if title:
            print(f"\n📊 {title}")
            print("=" * (len(title) + 4))
        
        if isinstance(data, dict):
            print(json.dumps(data, indent=2))
        elif isinstance(data, list):
            for i, item in enumerate(data, 1):
                print(f"{i}. {item}")
        else:
            print(data)
    
    # Blockchain Commands
    def getblockchaininfo(self, args: List[str]) -> None:
        """Get blockchain information"""
        try:
            latest_block = self.blockchain.get_latest_block()
            
            info = {
                "chain": "main",
                "blocks": len(self.blockchain.chain),
                "headers": len(self.blockchain.chain),
                "bestblockhash": latest_block.hash if latest_block else "",
                "difficulty": self.blockchain.difficulty,
                "mediantime": latest_block.timestamp if latest_block else 0,
                "verificationprogress": 1.0,
                "chainwork": "0000000000000000000000000000000000000000000000000000000000000000",
                "size_on_disk": os.path.getsize(self.blockchain.get_blockchain_file_path()) if os.path.exists(self.blockchain.get_blockchain_file_path()) else 0,
                "pruned": False,
                "softforks": [],
                "bip9_softforks": {}
            }
            
            self.format_output(info, "Blockchain Information")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def getmininginfo(self, args: List[str]) -> None:
        """Get mining information"""
        try:
            info = {
                "blocks": len(self.blockchain.chain),
                "currentblocksize": 0,
                "currentblocktx": len(self.blockchain.mempool),
                "difficulty": float(self.blockchain.difficulty),
                "networkhashps": 0,
                "pooledtx": len(self.blockchain.mempool),
                "chain": "main",
                "warnings": "",
                "is_mining": self.blockchain.is_mining,
                "mining_reward": self.blockchain.get_current_reward()
            }
            
            self.format_output(info, "Mining Information")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def getpeerinfo(self, args: List[str]) -> None:
        """Get peer information"""
        try:
            if not self.network_node:
                self.format_output({"error": "Network node not available"}, "Peer Information")
                return
            
            peers = self.network_node.get_peer_list()
            network_info = self.network_node.get_network_info()
            
            peer_info = {
                "connected_peers": network_info['connected_peers'],
                "banned_peers": network_info['banned_peers'],
                "messages_sent": network_info['messages_sent'],
                "messages_received": network_info['messages_received'],
                "bytes_sent": network_info['bytes_sent'],
                "bytes_received": network_info['bytes_received'],
                "peers": peers
            }
            
            self.format_output(peer_info, "Peer Information")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def getblockcount(self, args: List[str]) -> None:
        """Get block count"""
        try:
            count = len(self.blockchain.chain)
            self.format_output(count, "Block Count")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def getbestblockhash(self, args: List[str]) -> None:
        """Get best block hash"""
        try:
            latest = self.blockchain.get_latest_block()
            hash_value = latest.hash if latest else ""
            self.format_output(hash_value, "Best Block Hash")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def getblock(self, args: List[str]) -> None:
        """Get block by hash or height"""
        try:
            if not args:
                print("❌ Usage: getblock <hash_or_height>")
                return
            
            block_identifier = args[0]
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
                block = self.blockchain.get_block_by_hash(block_identifier)
            
            if not block:
                print(f"❌ Block not found: {block_identifier}")
                return
            
            block_info = {
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
            
            self.format_output(block_info, f"Block {block_identifier}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def getblockhash(self, args: List[str]) -> None:
        """Get block hash by height"""
        try:
            if not args:
                print("❌ Usage: getblockhash <index>")
                return
            
            height = int(args[0])
            if height < 0 or height >= len(self.blockchain.chain):
                print(f"❌ Block height out of range: {height}")
                return
            
            hash_value = self.blockchain.chain[height].hash
            self.format_output(hash_value, f"Block Hash at Height {height}")
            
        except ValueError:
            print("❌ Invalid height parameter")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Transaction Commands
    def getrawmempool(self, args: List[str]) -> None:
        """Get raw mempool"""
        try:
            verbose = '--verbose' in args or '-v' in args
            
            if verbose:
                transactions = [tx.to_dict() for tx in self.blockchain.mempool]
            else:
                transactions = [tx.tx_id for tx in self.blockchain.mempool]
            
            info = {
                "size": len(self.blockchain.mempool),
                "bytes": 0,
                "usage": 0,
                "maxmempool": 100000000,
                "mempoolminfee": 0.00001,
                "minrelaytxfee": 0.00001,
                "transactions": transactions
            }
            
            self.format_output(info, "Mempool Information")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def getrawtransaction(self, args: List[str]) -> None:
        """Get raw transaction"""
        try:
            if not args:
                print("❌ Usage: getrawtransaction <txid> [verbose]")
                return
            
            tx_id = args[0]
            verbose = len(args) > 1 and args[1] in ['1', 'true', 'verbose']
            
            result = self.blockchain.get_transaction_by_hash(tx_id)
            if not result:
                print(f"❌ Transaction not found: {tx_id}")
                return
            
            tx, block_height = result
            
            if verbose:
                tx_info = {
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
                self.format_output(tx_info, f"Transaction {tx_id}")
            else:
                self.format_output(json.dumps(tx.to_dict()), f"Raw Transaction {tx_id}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def decoderawtransaction(self, args: List[str]) -> None:
        """Decode raw transaction"""
        try:
            if not args:
                print("❌ Usage: decoderawtransaction <hex>")
                return
            
            raw_tx = args[0]
            
            try:
                tx_data = json.loads(raw_tx)
                self.format_output(tx_data, "Decoded Transaction")
            except json.JSONDecodeError:
                print("❌ Invalid transaction hex format")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # General Commands
    def help(self, args: List[str]) -> None:
        """Show help information"""
        help_text = """
🪙 GSC Coin Console Commands

📊 Blockchain Info Commands:
  getblockchaininfo              - Get blockchain information
  getmininginfo                 - Get mining information  
  getpeerinfo                    - Get peer information
  getblockcount                  - Get block count
  getbestblockhash               - Get best block hash
  getblock <hash|height>         - Get block by hash or height
  getblockhash <index>           - Get block hash by height

📝 Transaction Commands:
  getrawmempool [--verbose]     - Get raw mempool
  getrawtransaction <txid>       - Get raw transaction
  decoderawtransaction <hex>     - Decode raw transaction

⛏️ Mining Commands:
  startmining <address>          - Start mining to address
  stopmining                     - Stop mining
  generatetoaddress <n> <addr>  - Generate blocks to address

👛️ Wallet Commands:
  getbalance [address]           - Get balance
  sendtoaddress <addr> <amount>  - Send to address
  getnewaddress                  - Get new address
  listaddresses                  - List addresses

🌐 Network Commands:
  startnetwork                   - Start network node
  stopnetwork                    - Stop network node
  connecttopeer <host:port>     - Connect to peer
  disconnectpeer <host:port>    - Disconnect peer

🔧 Utility Commands:
  status                         - Show system status
  clear                          - Clear screen
  exit/quit                      - Exit console

Examples:
  > getblockchaininfo
  > getblock 0
  > getblockhash 0
  > getrawmempool --verbose
  > getrawtransaction abc123...
  > decoderawtransaction '{"sender":"..."}'
  > startmining GSC_ADDRESS
  > sendtoaddress GSC_ADDRESS 10.5
        """
        
        print(help_text)
    
    def status(self, args: List[str]) -> None:
        """Show system status"""
        try:
            status_info = {
                "blockchain": {
                    "blocks": len(self.blockchain.chain),
                    "mempool_size": len(self.blockchain.mempool),
                    "difficulty": self.blockchain.difficulty,
                    "is_mining": self.blockchain.is_mining
                },
                "network": {
                    "connected_peers": len(self.network_node.peers) if self.network_node else 0,
                    "banned_peers": len(self.network_node.banned_peers) if self.network_node else 0
                },
                "wallet": {
                    "current_wallet": self.wallet_manager.current_wallet if self.wallet_manager else None,
                    "loaded": self.wallet_manager.current_wallet is not None if self.wallet_manager else False
                },
                "rpc": {
                    "running": self.rpc_server.is_running() if self.rpc_server else False
                }
            }
            
            self.format_output(status_info, "System Status")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def clear(self, args: List[str]) -> None:
        """Clear screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    # Mining Commands
    def startmining(self, args: List[str]) -> None:
        """Start mining"""
        try:
            if not args:
                print("❌ Usage: startmining <address>")
                return
            
            address = args[0]
            
            if self.blockchain.is_mining:
                print("⚠️ Mining is already running")
                return
            
            print(f"⛏️ Starting mining to {address}...")
            
            def mine_callback(stats):
                if stats['nonce'] % 1000 == 0:
                    print(f"� Mining... Nonce: {stats['nonce']}, Hash rate: {stats.get('hash_rate', 0):.2f} H/s")
            
            # Start mining in background thread
            import threading
            mining_thread = threading.Thread(
                target=self.blockchain.mine_pending_transactions,
                args=(address,),
                kwargs={'callback': mine_callback}
            )
            mining_thread.daemon = True
            mining_thread.start()
            
            print("✅ Mining started")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def stopmining(self, args: List[str]) -> None:
        """Stop mining"""
        try:
            if not self.blockchain.is_mining:
                print("⚠️ Mining is not running")
                return
            
            self.blockchain.is_mining = False
            print("✅ Mining stopped")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def generatetoaddress(self, args: List[str]) -> None:
        """Generate blocks to address"""
        try:
            if len(args) < 2:
                print("❌ Usage: generatetoaddress <nblocks> <address>")
                return
            
            nblocks = int(args[0])
            address = args[1]
            
            print(f"⛏️ Generating {nblocks} blocks to {address}...")
            
            block_hashes = []
            for i in range(nblocks):
                # Create transaction
                from blockchain_improved import Transaction
                tx = Transaction(
                    sender="GSC_FOUNDATION_RESERVE",
                    receiver=address,
                    amount=25.0,
                    fee=0.1,
                    timestamp=time.time()
                )
                self.blockchain.add_transaction_to_mempool(tx)
                
                # Mine block
                block = self.blockchain.mine_pending_transactions(address)
                if block:
                    block_hashes.append(block.hash)
                    print(f"✅ Generated block {i+1}/{nblocks}: {block.hash[:16]}...")
                else:
                    print(f"❌ Failed to generate block {i+1}")
                    break
            
            self.format_output(block_hashes, f"Generated {len(block_hashes)} Blocks")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Wallet Commands
    def getbalance(self, args: List[str]) -> None:
        """Get balance"""
        try:
            if args:
                address = args[0]
                balance = self.blockchain.get_balance(address)
                self.format_output({address: balance}, f"Balance for {address}")
            else:
                if self.wallet_manager and self.wallet_manager.current_wallet:
                    addresses = self.wallet_manager.get_receiving_addresses()
                    total_balance = sum(self.blockchain.get_balance(addr) for addr in addresses)
                    balances = {addr: self.blockchain.get_balance(addr) for addr in addresses}
                    balances['total'] = total_balance
                    self.format_output(balances, f"Wallet Balances")
                else:
                    print("❌ No wallet loaded")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def sendtoaddress(self, args: List[str]) -> None:
        """Send to address"""
        try:
            if len(args) < 2:
                print("❌ Usage: sendtoaddress <address> <amount>")
                return
            
            address = args[0]
            amount = float(args[1])
            
            if not self.wallet_manager or not self.wallet_manager.current_wallet:
                print("❌ No wallet loaded")
                return
            
            sending_addresses = self.wallet_manager.get_sending_addresses()
            if not sending_addresses:
                print("❌ No sending addresses available")
                return
            
            sender = sending_addresses[0]
            
            from blockchain_improved import Transaction
            tx = Transaction(
                sender=sender,
                receiver=address,
                amount=amount,
                fee=0.0001,
                timestamp=time.time()
            )
            
            if self.blockchain.add_transaction_to_mempool(tx):
                print(f"✅ Sent {amount} GSC to {address}")
                print(f"Transaction ID: {tx.tx_id}")
            else:
                print("❌ Transaction failed - insufficient funds or invalid")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def getnewaddress(self, args: List[str]) -> None:
        """Get new address"""
        try:
            if not self.wallet_manager or not self.wallet_manager.current_wallet:
                print("❌ No wallet loaded")
                return
            
            addresses = self.wallet_manager.get_receiving_addresses()
            if addresses:
                self.format_output(addresses[0], "New Address")
            else:
                print("❌ No addresses available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def listaddresses(self, args: List[str]) -> None:
        """List addresses"""
        try:
            if not self.wallet_manager or not self.wallet_manager.current_wallet:
                print("❌ No wallet loaded")
                return
            
            receiving = self.wallet_manager.get_receiving_addresses()
            sending = self.wallet_manager.get_sending_addresses()
            
            addresses = {
                "receiving_addresses": receiving,
                "sending_addresses": sending,
                "total_addresses": len(receiving) + len(sending)
            }
            
            self.format_output(addresses, "Wallet Addresses")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Network Commands
    def startnetwork(self, args: List[str]) -> None:
        """Start network node"""
        try:
            if self.network_node and self.network_node.running:
                print("⚠️ Network is already running")
                return
            
            if self.network_node.start_server():
                print("✅ Network node started")
            else:
                print("❌ Failed to start network node")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def stopnetwork(self, args: List[str]) -> None:
        """Stop network node"""
        try:
            if not self.network_node or not self.network_node.running:
                print("⚠️ Network is not running")
                return
            
            self.network_node.stop_server()
            print("✅ Network node stopped")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def connecttopeer(self, args: List[str]) -> None:
        """Connect to peer"""
        try:
            if not args:
                print("❌ Usage: connecttopeer <host:port>")
                return
            
            peer = args[0]
            if ':' not in peer:
                peer += ":8333"
            
            host, port = peer.split(':')
            
            if self.network_node.connect_to_peer(host, int(port)):
                print(f"✅ Connected to peer: {peer}")
            else:
                print(f"❌ Failed to connect to peer: {peer}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def disconnectpeer(self, args: List[str]) -> None:
        """Disconnect peer"""
        try:
            if not args:
                print("❌ Usage: disconnectpeer <host:port>")
                return
            
            peer = args[0]
            
            if peer in self.network_node.peers:
                self.network_node.peers.discard(peer)
                print(f"✅ Disconnected from peer: {peer}")
            else:
                print(f"❌ Peer not connected: {peer}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def run_interactive(self):
        """Run interactive console"""
        self.running = True
        
        print("\n🪙 GSC Coin Console - Interactive Mode")
        print("Type 'help' for available commands or 'exit' to quit")
        print("=" * 60)
        
        while self.running:
            try:
                command = input("\nGSC> ").strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                # Route to appropriate command handler
                if cmd in ['exit', 'quit']:
                    break
                elif cmd == 'help':
                    self.help(args)
                elif cmd == 'clear':
                    self.clear(args)
                elif cmd == 'status':
                    self.status(args)
                elif cmd == 'getblockchaininfo':
                    self.getblockchaininfo(args)
                elif cmd == 'getmininginfo':
                    self.getmininginfo(args)
                elif cmd == 'getpeerinfo':
                    self.getpeerinfo(args)
                elif cmd == 'getblockcount':
                    self.getblockcount(args)
                elif cmd == 'getbestblockhash':
                    self.getbestblockhash(args)
                elif cmd == 'getblock':
                    self.getblock(args)
                elif cmd == 'getblockhash':
                    self.getblockhash(args)
                elif cmd == 'getrawmempool':
                    self.getrawmempool(args)
                elif cmd == 'getrawtransaction':
                    self.getrawtransaction(args)
                elif cmd == 'decoderawtransaction':
                    self.decoderawtransaction(args)
                elif cmd == 'startmining':
                    self.startmining(args)
                elif cmd == 'stopmining':
                    self.stopmining(args)
                elif cmd == 'generatetoaddress':
                    self.generatetoaddress(args)
                elif cmd == 'getbalance':
                    self.getbalance(args)
                elif cmd == 'sendtoaddress':
                    self.sendtoaddress(args)
                elif cmd == 'getnewaddress':
                    self.getnewaddress(args)
                elif cmd == 'listaddresses':
                    self.listaddresses(args)
                elif cmd == 'startnetwork':
                    self.startnetwork(args)
                elif cmd == 'stopnetwork':
                    self.stopnetwork(args)
                elif cmd == 'connecttopeer':
                    self.connecttopeer(args)
                elif cmd == 'disconnectpeer':
                    self.disconnectpeer(args)
                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as e:
                print(f"❌ Error executing command: {e}")
        
        print("\n👋 Goodbye!")

def main():
    """Main console entry point"""
    parser = argparse.ArgumentParser(description='GSC Coin Console Interface')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--command', '-c', help='Execute single command')
    parser.add_argument('--args', nargs='*', help='Arguments for command')
    
    args = parser.parse_args()
    
    console = GSCConsole()
    
    if not console.initialize():
        print("❌ Failed to initialize console")
        sys.exit(1)
    
    if args.interactive:
        console.run_interactive()
    elif args.command:
        # Execute single command
        cmd = args.command.lower()
        cmd_args = args.args or []
        
        # Map command to method
        command_map = {
            'getblockchaininfo': console.getblockchaininfo,
            'getmininginfo': console.getmininginfo,
            'getpeerinfo': console.getpeerinfo,
            'getblockcount': console.getblockcount,
            'getbestblockhash': console.getbestblockhash,
            'getblock': console.getblock,
            'getblockhash': console.getblockhash,
            'getrawmempool': console.getrawmempool,
            'getrawtransaction': console.getrawtransaction,
            'decoderawtransaction': console.decoderawtransaction,
            'status': console.status,
            'help': console.help
        }
        
        if cmd in command_map:
            command_map[cmd](cmd_args)
        else:
            print(f"❌ Unknown command: {cmd}")
    else:
        # Default to interactive mode
        console.run_interactive()

if __name__ == "__main__":
    main()
