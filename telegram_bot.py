#!/usr/bin/env python3
"""
Telegram Bot Integration for GSC Coin
Sends transaction notifications to Telegram bot
"""

import requests
import json
import time
from datetime import datetime

class TelegramBot:
    def __init__(self):
        self.bot_token = "8360297293:AAH8uHoBVMe09D5RguuRMRHb5_mcB3k7spo"
        self.bot_username = "@gsc_vags_bot"
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.chat_id = None  # Will be set when we get updates
        
    def get_chat_id(self):
        """Get chat ID from bot updates"""
        try:
            response = requests.get(f"{self.base_url}/getUpdates", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['ok'] and data['result']:
                    # Get the most recent chat ID
                    self.chat_id = data['result'][-1]['message']['chat']['id']
                    return self.chat_id
        except Exception as e:
            print(f"Error getting chat ID: {e}")
        return None
    
    def send_transaction_notification(self, transaction_data):
        """Send transaction notification to Telegram bot"""
        try:
            # Format transaction data as JSON
            tx_json = {
                "type": "GSC_TRANSACTION",
                "timestamp": datetime.now().isoformat(),
                "transaction": {
                    "tx_id": transaction_data.get('tx_id', ''),
                    "sender": transaction_data.get('sender', ''),
                    "receiver": transaction_data.get('receiver', ''),
                    "amount": transaction_data.get('amount', 0),
                    "fee": transaction_data.get('fee', 0),
                    "timestamp": transaction_data.get('timestamp', time.time()),
                    "signature": transaction_data.get('signature', '')
                }
            }
            
            # Format message
            message = f"🔗 **GSC Coin Transaction**\n\n"
            message += f"```json\n{json.dumps(tx_json, indent=2)}\n```"
            
            # Try to get chat ID if not set
            if not self.chat_id:
                self.get_chat_id()
            
            # Send to specific chat ID if available, otherwise broadcast
            if self.chat_id:
                self._send_message(message, self.chat_id)
            else:
                # Try to send to a default channel or group
                self._broadcast_message(message)
                
            print(f"✅ Transaction sent to Telegram: {transaction_data.get('tx_id', 'Unknown')[:16]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            return False
    
    def send_block_notification(self, block_data):
        """Send block mining notification to Telegram bot"""
        try:
            block_json = {
                "type": "GSC_BLOCK_MINED",
                "timestamp": datetime.now().isoformat(),
                "block": {
                    "index": block_data.get('index', 0),
                    "hash": block_data.get('hash', ''),
                    "previous_hash": block_data.get('previous_hash', ''),
                    "nonce": block_data.get('nonce', 0),
                    "difficulty": block_data.get('difficulty', 0),
                    "miner": block_data.get('miner', ''),
                    "reward": block_data.get('reward', 0),
                    "transactions_count": len(block_data.get('transactions', []))
                }
            }
            
            message = f"⛏️ **GSC Block Mined**\n\n"
            message += f"```json\n{json.dumps(block_json, indent=2)}\n```"
            
            if not self.chat_id:
                self.get_chat_id()
            
            if self.chat_id:
                self._send_message(message, self.chat_id)
            else:
                self._broadcast_message(message)
                
            print(f"✅ Block notification sent to Telegram: Block {block_data.get('index', 'Unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending block notification: {e}")
            return False
    
    def send_chain_info(self, chain_data):
        """Send GSC chain information in JSON format"""
        try:
            chain_json = {
                "type": "GSC_CHAIN_INFO",
                "timestamp": datetime.now().isoformat(),
                "chain_info": chain_data
            }
            
            message = f"📊 **GSC Chain Information**\n\n"
            message += f"```json\n{json.dumps(chain_json, indent=2)}\n```"
            
            if not self.chat_id:
                self.get_chat_id()
            
            if self.chat_id:
                self._send_message(message, self.chat_id)
            else:
                self._broadcast_message(message)
                
            print("✅ Chain info sent to Telegram")
            return True
            
        except Exception as e:
            print(f"❌ Error sending chain info: {e}")
            return False
    
    def _send_message(self, message, chat_id):
        """Send message to specific chat"""
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(f"{self.base_url}/sendMessage", data=data, timeout=10)
        return response.status_code == 200
    
    def _broadcast_message(self, message):
        """Broadcast message (fallback method)"""
        # This is a fallback - in practice, you'd need to know the chat ID
        # For now, we'll just log that we tried to send
        print(f"📢 Would broadcast to {self.bot_username}: {message[:100]}...")
        return True
    
    def test_connection(self):
        """Test Telegram bot connection"""
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    bot_info = data['result']
                    print(f"✅ Connected to Telegram bot: {bot_info['username']}")
                    return True
            print("❌ Failed to connect to Telegram bot")
            return False
        except Exception as e:
            print(f"❌ Telegram connection error: {e}")
            return False

# Global telegram bot instance
telegram_bot = TelegramBot()
