# GSC Coin - Complete Technical Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Wallet Creation & Address Generation](#wallet-creation--address-generation)
4. [Blockchain Structure](#blockchain-structure)
5. [Consensus Mechanism](#consensus-mechanism)
6. [Mining System](#mining-system)
7. [Transaction Processing](#transaction-processing)
8. [Mempool Management](#mempool-management)
9. [Network Architecture](#network-architecture)
10. [Security Features](#security-features)
11. [Telegram Integration](#telegram-integration)
12. [GUI Interface Guide](#gui-interface-guide)
13. [API Reference](#api-reference)
14. [Installation & Setup](#installation--setup)
15. [Troubleshooting](#troubleshooting)

---

## Introduction

GSC Coin is a custom blockchain cryptocurrency implementation built in Python with a comprehensive wallet interface. It features proof-of-work consensus, P2P networking, secure transaction processing, and advanced security controls.

### Key Features
- **Custom Blockchain**: Built from scratch with proof-of-work consensus
- **Secure Wallet**: GUI-based wallet with address generation and management
- **Mining System**: Integrated mining with configurable difficulty
- **P2P Network**: Decentralized peer-to-peer communication
- **Access Control**: Restricted mining and mempool access
- **Telegram Integration**: Real-time transaction notifications
- **Import/Export**: Blockchain and mempool data management

### Technical Specifications
- **Total Supply**: 21.75 trillion GSC coins
- **Block Time**: Variable (based on mining difficulty)
- **Mining Algorithm**: SHA-256 Proof of Work
- **Address Format**: GSC + Base58 encoded public key
- **Network Protocol**: TCP-based P2P communication

---

## System Architecture

### Core Components

```
GSC Coin System
├── Blockchain Core (blockchain.py)
│   ├── Block Structure
│   ├── Transaction Processing
│   ├── Mining Logic
│   └── Consensus Rules
├── Wallet GUI (gsc_wallet_gui.py)
│   ├── User Interface
│   ├── Address Management
│   ├── Transaction Creation
│   └── Mining Controls
├── Network Layer (network.py)
│   ├── P2P Communication
│   ├── Peer Discovery
│   ├── Message Broadcasting
│   └── Synchronization
├── Security Layer
│   ├── Access Control
│   ├── Address Validation
│   └── Mining Restrictions
└── Integration Layer (telegram_bot.py)
    ├── Notification System
    ├── Transaction Alerts
    └── Block Announcements
```

### Data Flow Architecture

```
User Action → GUI Interface → Blockchain Core → Network Layer → Peers
     ↓              ↓              ↓              ↓           ↓
Transaction → Validation → Mempool → Broadcasting → Confirmation
     ↓              ↓              ↓              ↓           ↓
Mining → Block Creation → Consensus → Chain Update → Telegram Alert
```

---

## Wallet Creation & Address Generation

### Address Generation Process

GSC Coin uses a custom address generation system:

1. **Key Generation**: Generate a random private key
2. **Public Key Derivation**: Derive public key from private key
3. **Address Encoding**: Create GSC address using Base58 encoding
4. **Validation**: Verify address format and checksum

### Address Format
```
GSC + [Base58 Encoded Public Key]
Example: GSC1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4
```

### Wallet Structure
```python
Wallet {
    private_key: str,
    public_key: str,
    address: str,
    balance: float,
    transaction_history: List[Transaction]
}
```

### Security Features
- **Private Key Protection**: Keys stored securely in memory
- **Address Validation**: Checksum verification for all addresses
- **Backup Support**: Export/import wallet functionality
- **Paper Wallet**: Generate offline cold storage addresses

---

## Blockchain Structure

### Block Structure
```python
Block {
    index: int,                    # Block number in chain
    timestamp: float,              # Block creation time
    transactions: List[Transaction], # List of transactions
    previous_hash: str,            # Hash of previous block
    nonce: int,                    # Proof of work nonce
    hash: str,                     # Block hash
    miner: str,                    # Miner address
    difficulty: int,               # Mining difficulty
    reward: float                  # Block reward
}
```

### Transaction Structure
```python
Transaction {
    sender: str,                   # Sender address
    receiver: str,                 # Receiver address
    amount: float,                 # Transaction amount
    fee: float,                    # Transaction fee
    timestamp: float,              # Transaction time
    signature: str,                # Digital signature
    tx_id: str                     # Transaction ID
}
```

### Genesis Block
The blockchain starts with a genesis block containing:
- **Index**: 0
- **Previous Hash**: "0"
- **Genesis Address**: GSC1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4
- **Initial Supply**: Pre-mined coins for network bootstrap

---

## Consensus Mechanism

### Proof of Work (PoW)

GSC Coin uses SHA-256 based proof-of-work consensus:

#### Mining Process
1. **Transaction Collection**: Gather pending transactions from mempool
2. **Block Assembly**: Create new block with transactions
3. **Nonce Search**: Find nonce that produces valid hash
4. **Hash Validation**: Verify hash meets difficulty target
5. **Block Broadcasting**: Share valid block with network

#### Difficulty Adjustment
```python
Target = "0" * difficulty
Valid Hash = hash.startswith(target)
```

#### Difficulty Levels
- **Level 1**: 1 leading zero (easiest)
- **Level 2**: 2 leading zeros
- **Level 3**: 3 leading zeros
- **Level 4**: 4 leading zeros (default)
- **Level 8**: 8 leading zeros (hardest)

### Consensus Rules
1. **Longest Chain**: Accept chain with most accumulated work
2. **Valid Transactions**: All transactions must be valid
3. **Block Validation**: Blocks must meet difficulty requirements
4. **Double Spend Prevention**: Prevent spending same coins twice
5. **Balance Verification**: Ensure sufficient funds for transactions

---

## Mining System

### Mining Architecture

```
Mining Process Flow:
User → Mining Tab → Access Control → Address Verification → Mining Start
  ↓         ↓            ↓               ↓                    ↓
GUI → Mining Thread → Block Assembly → PoW Calculation → Block Found
  ↓         ↓            ↓               ↓                    ↓
Stats → Hash Rate → Nonce Counter → Difficulty Check → Network Broadcast
```

### Access Control System
Mining is restricted to authorized addresses only:

#### Required Address
```
GSC1705641e65321ef23ac5fb3d470f39627
```

#### Access Flow
1. **Click Mining Tab**: Shows access control interface
2. **Enter Address**: Input the required GSC address
3. **Unlock Mining**: Click "Unlock Mining" button
4. **Validation**: System verifies the entered address
5. **Access Granted**: Full mining interface becomes available

### Mining Rewards
- **Block Reward**: Fixed reward per mined block
- **Transaction Fees**: All fees from block transactions
- **Mandatory Address**: All rewards go to specified address

### Mining Statistics
The mining interface displays:
- **Status**: Current mining state (Idle/Mining)
- **Nonce**: Current nonce being tested
- **Hash Rate**: Hashes per second
- **Current Hash**: Latest hash attempt
- **Block Details**: Information about block being mined

---

## Transaction Processing

### Transaction Lifecycle

```
Transaction Flow:
Create → Sign → Validate → Mempool → Mining → Confirmation → Telegram Alert
   ↓      ↓       ↓         ↓        ↓         ↓             ↓
 GUI → Wallet → Blockchain → Pool → Block → Chain → Notification
```

### Transaction Validation
1. **Signature Verification**: Validate digital signature
2. **Balance Check**: Ensure sender has sufficient funds
3. **Address Validation**: Verify sender and receiver addresses
4. **Fee Calculation**: Calculate and validate transaction fee
5. **Double Spend Check**: Prevent duplicate spending

### Transaction Fees
- **Fee Structure**: Percentage-based or fixed fee
- **Fee Collection**: All fees go to mandatory mining address
- **Priority**: Higher fees get priority in block inclusion

### Transaction States
- **Pending**: In mempool awaiting confirmation
- **Confirmed**: Included in a mined block
- **Failed**: Invalid or rejected transaction

---

## Mempool Management

### Mempool Architecture
The mempool (memory pool) stores pending transactions:

```python
Mempool {
    transactions: Dict[str, Transaction],  # Pending transactions
    size: int,                            # Number of transactions
    total_fees: float,                    # Sum of all fees
    max_size: int                         # Maximum capacity
}
```

### Access Control System
Mempool access is restricted similar to mining:

#### Access Flow
1. **Click Mempool Tab**: Shows access control interface
2. **Enter Address**: Input `GSC1705641e65321ef23ac5fb3d470f39627`
3. **Unlock Mempool**: Click "Unlock Mempool" button
4. **Access Granted**: Full mempool interface becomes available

### Mempool Features
- **Transaction Viewing**: See all pending transactions
- **Import/Export**: Backup and restore mempool data
- **Statistics**: View mempool size and total fees
- **Refresh**: Update mempool display

### Transaction Priority
Transactions are prioritized by:
1. **Fee Amount**: Higher fees get priority
2. **Age**: Older transactions get preference
3. **Size**: Smaller transactions process faster

---

## Network Architecture

### P2P Network Structure

```
GSC Network Topology:
Node A ←→ Node B ←→ Node C
  ↕       ↕       ↕
Node D ←→ Node E ←→ Node F
  ↕       ↕       ↕
Node G ←→ Node H ←→ Node I
```

### Network Components
1. **Peer Discovery**: Find and connect to other nodes
2. **Message Broadcasting**: Share transactions and blocks
3. **Synchronization**: Keep blockchain in sync
4. **Connection Management**: Maintain peer connections

### Network Messages
- **Transaction**: Broadcast new transactions
- **Block**: Share newly mined blocks
- **Peer List**: Exchange peer information
- **Sync Request**: Request blockchain data
- **Ping/Pong**: Keep connections alive

### Network Features
- **Auto-Discovery**: Automatically find peers
- **Manual Connection**: Connect to specific peers
- **Connection Limits**: Maximum peer connections
- **Network Statistics**: View connection status

---

## Security Features

### Access Control System

GSC Coin implements a multi-layer security system:

#### Mining Access Control
- **Required Address**: `GSC1705641e65321ef23ac5fb3d470f39627`
- **Interface Lock**: Mining tab locked until address verification
- **Reward Enforcement**: All mining rewards go to mandatory address

#### Mempool Access Control
- **Same Address**: Uses identical address requirement
- **Interface Lock**: Mempool tab locked until address verification
- **Data Protection**: Prevents unauthorized mempool access

### Security Layers
1. **GUI Access Control**: Tab-level access restrictions
2. **Backend Enforcement**: Server-side address validation
3. **Network Security**: P2P communication protection
4. **Transaction Security**: Digital signature verification

### Address Validation
```python
def validate_address(address: str) -> bool:
    required = "GSC1705641e65321ef23ac5fb3d470f39627"
    return address.strip() == required
```

### Error Handling
- **Invalid Address**: Shows "❌ Invalid GSC Address" error
- **Access Denied**: Prevents unauthorized operations
- **Graceful Degradation**: System continues operating safely

---

## Telegram Integration

### Notification System

GSC Coin integrates with Telegram for real-time notifications:

#### Bot Configuration
- **Bot Token**: `8360297293:AAH8uHoBVMe09D5RguuRMRHb5_mcB3k7spo`
- **Bot Username**: `@gsc_vags_bot`
- **Chat Integration**: Sends messages to configured chat

### Notification Types

#### Transaction Notifications
```json
{
    "type": "transaction",
    "tx_id": "abc123...",
    "sender": "GSC1abc...",
    "receiver": "GSC1def...",
    "amount": 100.0,
    "fee": 0.1,
    "timestamp": 1642123456.789
}
```

#### Block Notifications
```json
{
    "type": "block",
    "block_index": 123,
    "block_hash": "000abc123...",
    "miner": "GSC1705641e65321ef23ac5fb3d470f39627",
    "transactions": 5,
    "reward": 50.0,
    "timestamp": 1642123456.789
}
```

### Integration Features
- **Real-time Alerts**: Instant transaction notifications
- **JSON Format**: Structured data for easy parsing
- **Error Handling**: Graceful failure if Telegram unavailable
- **Async Processing**: Non-blocking notification sending

---

## GUI Interface Guide

### Main Interface

The GSC Coin wallet provides a comprehensive GUI with multiple tabs:

#### Tab Overview
1. **Overview**: Wallet balance and transaction history
2. **Send**: Send GSC coins to other addresses
3. **Receive**: Generate receiving addresses
4. **Mining**: Mining controls (requires address unlock)
5. **Mempool**: Transaction pool management (requires address unlock)
6. **Blockchain**: Blockchain explorer and management
7. **Network**: P2P network status and controls

### Menu System

#### File Menu
- **Create Wallet**: Generate new wallet
- **Open Wallet**: Load existing wallet
- **Backup Wallet**: Export wallet data
- **Restore Wallet**: Import wallet backup
- **Exit**: Close application

#### Settings Menu
- **Encrypt Wallet**: Add password protection
- **Change Passphrase**: Update wallet password
- **Options**: Configure wallet settings

#### Tools Menu
- **Sign Message**: Create digital signatures
- **Verify Message**: Verify signatures
- **Paper Wallet**: Generate offline wallet
- **Console**: Debug console access

#### Window Menu
- **Minimize**: Minimize to system tray
- **Information**: System information
- **Network Traffic**: Network activity monitor

### Access Control Interface

#### Mining Tab Access
1. **Initial View**: "Mining Access Required" interface
2. **Address Input**: Text field for GSC address
3. **Unlock Button**: "Unlock Mining" button
4. **Status Display**: Success/error messages
5. **Full Interface**: Complete mining controls after unlock

#### Mempool Tab Access
1. **Initial View**: "Mempool Access Required" interface
2. **Address Input**: Text field for GSC address
3. **Unlock Button**: "Unlock Mempool" button
4. **Status Display**: Success/error messages
5. **Full Interface**: Complete mempool management after unlock

---

## API Reference

### Core Classes

#### Blockchain Class
```python
class Blockchain:
    def __init__(self):
        self.chain = []
        self.mempool = {}
        self.difficulty = 4
        self.reward = 50.0
        self.miner = MANDATORY_MINING_ADDRESS
    
    def create_genesis_block(self) -> Block
    def add_transaction_to_mempool(self, transaction: Transaction) -> bool
    def mine_block(self, difficulty: int, miner_address: str) -> dict
    def validate_transaction(self, transaction: Transaction) -> bool
    def get_balance(self, address: str) -> float
    def export_blockchain(self, filename: str) -> bool
    def import_blockchain(self, filename: str) -> bool
```

#### Transaction Class
```python
class Transaction:
    def __init__(self, sender: str, receiver: str, amount: float, fee: float):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.fee = fee
        self.timestamp = time.time()
        self.tx_id = self.calculate_hash()
    
    def calculate_hash(self) -> str
    def to_dict(self) -> dict
    def from_dict(cls, data: dict) -> 'Transaction'
```

#### Block Class
```python
class Block:
    def __init__(self, index: int, transactions: List[Transaction], 
                 previous_hash: str, miner: str):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.miner = miner
        self.nonce = 0
        self.hash = ""
    
    def calculate_hash(self) -> str
    def mine_block(self, difficulty: int) -> dict
    def to_dict(self) -> dict
```

### Network API

#### GSCNetworkNode Class
```python
class GSCNetworkNode:
    def __init__(self, host: str, port: int, blockchain: Blockchain):
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.peers = []
    
    def start_server(self) -> None
    def connect_to_peer(self, host: str, port: int) -> bool
    def broadcast_transaction(self, transaction: Transaction) -> None
    def broadcast_block(self, block: Block) -> None
    def sync_blockchain(self) -> None
```

### GUI API

#### GSCWalletGUI Class
```python
class GSCWalletGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.blockchain = Blockchain()
        self.network = GSCNetworkNode("localhost", 8333, self.blockchain)
        self.mining_unlocked = False
        self.mempool_unlocked = False
    
    def create_gui(self) -> None
    def unlock_mining(self) -> None
    def unlock_mempool(self) -> None
    def start_mining(self) -> None
    def send_transaction(self) -> None
    def update_displays(self) -> None
```

---

## Installation & Setup

### System Requirements
- **Python**: 3.7 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 512MB RAM
- **Storage**: 100MB free space
- **Network**: Internet connection for P2P networking

### Dependencies
```bash
pip install tkinter
pip install hashlib
pip install json
pip install threading
pip install socket
pip install requests  # For Telegram integration
```

### Installation Steps

1. **Download Source Code**
   ```bash
   git clone https://github.com/your-repo/gsc-coin.git
   cd gsc-coin
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Wallet**
   ```bash
   python gsc_wallet_gui.py
   ```

### Configuration

#### Network Configuration
Edit `config.json`:
```json
{
    "network": {
        "host": "localhost",
        "port": 8333,
        "max_peers": 10
    },
    "mining": {
        "difficulty": 4,
        "reward": 50.0
    },
    "telegram": {
        "bot_token": "your_bot_token",
        "chat_id": "your_chat_id"
    }
}
```

#### Security Configuration
Set mandatory mining address in `blockchain.py`:
```python
MANDATORY_MINING_ADDRESS = "GSC1705641e65321ef23ac5fb3d470f39627"
```

---

## Troubleshooting

### Common Issues

#### GUI Not Starting
**Problem**: Application fails to start
**Solution**: 
- Check Python version (3.7+)
- Install missing dependencies
- Verify tkinter installation

#### Mining Access Denied
**Problem**: Cannot access mining tab
**Solution**:
- Enter exact address: `GSC1705641e65321ef23ac5fb3d470f39627`
- Check for extra spaces or characters
- Restart application if needed

#### Network Connection Issues
**Problem**: Cannot connect to peers
**Solution**:
- Check firewall settings
- Verify port 8333 is open
- Try manual peer connection

#### Telegram Notifications Not Working
**Problem**: No Telegram alerts received
**Solution**:
- Verify bot token is correct
- Check internet connection
- Confirm bot is added to chat

### Error Messages

#### "Invalid GSC Address"
- **Cause**: Incorrect address entered for mining/mempool access
- **Solution**: Enter the exact required address

#### "No transactions in mempool to mine"
- **Cause**: Attempting to mine with empty mempool
- **Solution**: Create transactions first or wait for network transactions

#### "Connection refused"
- **Cause**: Network peer unavailable
- **Solution**: Try different peer or check network settings

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support Resources
- **Documentation**: This file
- **Source Code**: Available in repository
- **Issue Tracker**: Report bugs and feature requests
- **Community**: Join discussion forums

---

## Conclusion

GSC Coin represents a complete blockchain cryptocurrency implementation with advanced security features, user-friendly interface, and comprehensive functionality. The system provides:

- **Secure Wallet Management**: Complete wallet functionality with GUI
- **Restricted Access Control**: Mining and mempool access controls
- **Real-time Notifications**: Telegram integration for alerts
- **P2P Networking**: Decentralized network communication
- **Comprehensive Documentation**: Complete technical reference

This documentation serves as a complete reference for understanding, using, and developing with the GSC Coin blockchain system.

---

*GSC Coin - Secure, Accessible, Decentralized*
