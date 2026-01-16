#!/usr/bin/env python3
"""
GSC Coin Console Interface - Simple Version
Interactive console for managing GSC Blockchain with RPC-like commands
"""

import sys
import os
import time
import json
import argparse
import hashlib

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_command(command, args):
    """Run a single command"""
    try:
        # Import here to avoid circular imports
        from blockchain_improved import GSCBlockchain
        
        blockchain = GSCBlockchain()
        
        if command == "getblockchaininfo":
            latest_block = blockchain.get_latest_block()
            info = {
                "chain": "main",
                "blocks": len(blockchain.chain),
                "headers": len(blockchain.chain),
                "bestblockhash": latest_block.hash if latest_block else "",
                "difficulty": blockchain.difficulty,
                "mediantime": latest_block.timestamp if latest_block else 0,
                "verificationprogress": 1.0,
                "chainwork": "0000000000000000000000000000000000000000000000000000000000000000",
                "size_on_disk": os.path.getsize(blockchain.get_blockchain_file_path()) if os.path.exists(blockchain.get_blockchain_file_path()) else 0,
                "pruned": False,
                "softforks": [],
                "bip9_softforks": {}
            }
            print(json.dumps(info, indent=2))
            
        elif command == "getmininginfo":
            info = {
                "blocks": len(blockchain.chain),
                "currentblocksize": 0,
                "currentblocktx": len(blockchain.mempool),
                "difficulty": float(blockchain.difficulty),
                "networkhashps": 0,
                "pooledtx": len(blockchain.mempool),
                "chain": "main",
                "warnings": "",
                "is_mining": blockchain.is_mining,
                "mining_reward": blockchain.get_current_reward()
            }
            print(json.dumps(info, indent=2))
            
        elif command == "getpeerinfo":
            info = {
                "connected_peers": 0,
                "banned_peers": 0,
                "messages_sent": 0,
                "messages_received": 0,
                "bytes_sent": 0,
                "bytes_received": 0,
                "peers": []
            }
            print(json.dumps(info, indent=2))
            
        elif command == "getblockcount":
            count = len(blockchain.chain)
            print(count)
            
        elif command == "getbestblockhash":
            latest = blockchain.get_latest_block()
            hash_value = latest.hash if latest else ""
            print(hash_value)
            
        elif command == "getblock":
            if not args:
                print("Usage: getblock <hash_or_height>")
                return
            
            block_identifier = args[0]
            block = None
            
            # Try to find by height first
            try:
                height = int(block_identifier)
                if 0 <= height < len(blockchain.chain):
                    block = blockchain.chain[height]
            except ValueError:
                pass
            
            # Try to find by hash
            if not block:
                block = blockchain.get_block_by_hash(block_identifier)
            
            if not block:
                print(f"Block not found: {block_identifier}")
                return
            
            block_info = {
                "hash": block.hash,
                "confirmations": len(blockchain.chain) - block.index,
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
                "nextblockhash": blockchain.chain[block.index + 1].hash if block.index + 1 < len(blockchain.chain) else None,
                "strippedsize": 0,
                "size": 0,
                "weight": 0,
                "tx": [tx.tx_id for tx in block.transactions]
            }
            print(json.dumps(block_info, indent=2))
            
        elif command == "getblockhash":
            if not args:
                print("Usage: getblockhash <index>")
                return
            
            height = int(args[0])
            if height < 0 or height >= len(blockchain.chain):
                print(f"Block height out of range: {height}")
                return
            
            hash_value = blockchain.chain[height].hash
            print(hash_value)
            
        elif command == "getrawmempool":
            verbose = '--verbose' in args or '-v' in args
            
            if verbose:
                transactions = [tx.to_dict() for tx in blockchain.mempool]
            else:
                transactions = [tx.tx_id for tx in blockchain.mempool]
            
            info = {
                "size": len(blockchain.mempool),
                "bytes": 0,
                "usage": 0,
                "maxmempool": 100000000,
                "mempoolminfee": 0.00001,
                "minrelaytxfee": 0.00001,
                "transactions": transactions
            }
            print(json.dumps(info, indent=2))
            
        elif command == "getrawtransaction":
            if not args:
                print("Usage: getrawtransaction <txid> [verbose]")
                return
            
            tx_id = args[0]
            verbose = len(args) > 1 and args[1] in ['1', 'true', 'verbose']
            
            result = blockchain.get_transaction_by_hash(tx_id)
            if not result:
                print(f"Transaction not found: {tx_id}")
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
                    "blockhash": blockchain.chain[block_height].hash if block_height >= 0 else "",
                    "confirmations": (len(blockchain.chain) - block_height) if block_height >= 0 else 0,
                    "time": tx.timestamp,
                    "blocktime": blockchain.chain[block_height].timestamp if block_height >= 0 else tx.timestamp
                }
                print(json.dumps(tx_info, indent=2))
            else:
                print(json.dumps(tx.to_dict()))
                
        elif command == "decoderawtransaction":
            if not args:
                print("Usage: decoderawtransaction <hex>")
                return
            
            raw_tx = args[0]
            
            try:
                tx_data = json.loads(raw_tx)
                print(json.dumps(tx_data, indent=2))
            except json.JSONDecodeError:
                print("Invalid transaction hex format")
                
        elif command == "help":
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

🔧 Utility Commands:
  help                           - Show this help

Examples:
  python gsc_simple_console.py getblockchaininfo
  python gsc_simple_console.py getblock 0
  python gsc_simple_console.py getblockhash 0
  python gsc_simple_console.py getrawmempool --verbose
  python gsc_simple_console.py getrawtransaction abc123...
  python gsc_simple_console.py decoderawtransaction '{"sender":"..."}'
            """
            print(help_text)
            
        else:
            print(f"Unknown command: {command}")
            print("Type 'help' for available commands")
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main console entry point"""
    parser = argparse.ArgumentParser(description='GSC Coin Console Interface')
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Arguments for command')
    
    args = parser.parse_args()
    
    if args.command:
        run_command(args.command, args.args)
    else:
        run_command("help", [])

if __name__ == "__main__":
    main()
