# GSC Coin Mainnet - Production Blockchain

A production-ready cryptocurrency blockchain built with Python, featuring secure P2P networking, advanced wallet management, and comprehensive monitoring.

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start a mainnet node
python -m mainnet.mainnet_node

# Start mining to an address
python -m mainnet.mainnet_node --mine YOUR_GSC_ADDRESS
```

### Docker Deployment
```bash
# Build and run with Docker Compose
chmod +x deploy.sh
./deploy.sh
```

### Cloud Deployment
```bash
# Deploy to AWS, GCP, or Azure
python cloud_deploy.py aws --region us-east-1 --instances 3
python cloud_deploy.py gcp --region us-central1 --instances 3
python cloud_deploy.py azure --region eastus --instances 3
```

## 🏗️ Architecture

### Core Components

- **MainnetBlockchain**: Production blockchain with enhanced validation
- **MainnetNetworkNode**: P2P networking with compression and security
- **MainnetWallet**: Secure wallet with RSA encryption and backup
- **APIServer**: RESTful API for external integration
- **Monitoring**: Prometheus metrics and health checks

### Network Configuration

- **Mainnet**: Port 8333 (P2P), 8334 (RPC), 8335 (API)
- **Testnet**: Port 18333 (P2P), 18334 (RPC), 18335 (API)

## 📊 API Endpoints

### Blockchain Information
```bash
GET /api/v1/info                    # Blockchain info
GET /api/v1/blocks                  # Get blocks (paginated)
GET /api/v1/blocks/{index}          # Get specific block
GET /api/v1/balance/{address}       # Get address balance
GET /api/v1/mempool                 # Get mempool transactions
```

### Transaction Management
```bash
POST /api/v1/transactions           # Submit transaction
GET /api/v1/validate                # Validate blockchain
```

### Network & Monitoring
```bash
GET /api/v1/network                 # Network information
GET /api/v1/peers                   # Connected peers
GET /api/v1/stats                   # Comprehensive statistics
```

### Wallet Management
```bash
GET /api/v1/wallets                 # List wallets
POST /api/v1/wallets                # Create wallet
```

## 🔧 Configuration

### Environment Variables
```bash
GSC_NETWORK=mainnet                 # Network type (mainnet/testnet)
GSC_DATA_DIR=/data/.gsccoin         # Data directory
GSC_NODE_TYPE=regular               # Node type (seed/regular)
GSC_MINING_ADDRESS=YOUR_ADDRESS     # Mining reward address
```

### Network Parameters
- **Block Time**: 2 minutes (mainnet), 1 minute (testnet)
- **Block Reward**: 50 GSC (halving every 1,051,200 blocks - 4 years)
- **Total Supply**: 21.75 trillion GSC
- **Mining Difficulty**: Fixed at 5 (requires 4 leading zeros: 00000...)
- **Halving Schedule**: Every 4 years (1,051,200 blocks at 2-minute intervals)
- **Transaction Fee**: Minimum 0.1 GSC

## 🛡️ Security Features

### Wallet Security
- RSA-2048 encryption for private keys
- PBKDF2 key derivation (100,000 iterations)
- Automatic wallet locking after failed attempts
- Secure backup and restore functionality

### Network Security
- Message compression and integrity checks
- Peer connection limits and rate limiting
- Banned peer management
- SSL/TLS support for API endpoints

### Blockchain Security
- Proof-of-Work consensus mechanism
- Merkle tree transaction verification
- Chain validation and checkpoint system
- Double-spending prevention

## 📈 Monitoring & Metrics

### Prometheus Metrics
- Blockchain height and difficulty
- Network peer count and traffic
- System resource usage
- Transaction processing times
- Health status indicators

### Health Checks
- Blockchain validation status
- Network connectivity
- System resource thresholds
- Mempool size monitoring

### Grafana Dashboard
Access at `http://localhost:3000` (admin/gsc_admin_2026)

## 🌐 Production Deployment

### Infrastructure Requirements
- **CPU**: 2+ cores per node
- **RAM**: 4GB+ per node
- **Storage**: 100GB+ SSD
- **Network**: 1Gbps+ bandwidth
- **OS**: Ubuntu 20.04+ or similar

### Seed Nodes
- `seed1.gsccoin.network:8333`
- `seed2.gsccoin.network:8333`
- `seed3.gsccoin.network:8333`
- `seed4.gsccoin.network:8333`

### Load Balancing
Nginx configuration included for:
- API endpoint load balancing
- SSL termination
- Rate limiting
- Health checks

## 🔄 Backup & Recovery

### Blockchain Backup
```bash
# Automatic backup to gsc_blockchain.json
# Manual backup
cp ~/.gsccoin/mainnet_blockchain.json backup_location/
```

### Wallet Backup
```python
from mainnet import MainnetWalletManager

wm = MainnetWalletManager()
wm.backup_wallet("MyWallet", "backup.json", "password")
```

### Disaster Recovery
1. Stop all nodes
2. Restore blockchain data
3. Restore wallet files
4. Restart nodes
5. Verify chain integrity

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Integration Tests
```bash
python -m pytest tests/integration/
```

### Load Testing
```bash
python tests/load_test.py --nodes 3 --transactions 1000
```

## 📚 Development

### Project Structure
```
mainnet/
├── __init__.py              # Package initialization
├── config.py                # Network configuration
├── mainnet_blockchain.py    # Core blockchain logic
├── mainnet_network.py       # P2P networking
├── mainnet_wallet.py        # Wallet management
├── mainnet_node.py          # Node implementation
├── api_server.py            # REST API server
├── monitoring.py            # Metrics and health checks
├── cloud_deploy.py          # Cloud deployment tools
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Multi-node deployment
├── requirements.txt         # Python dependencies
└── deploy.sh               # Deployment script
```

### Adding Features
1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add comprehensive docstrings
- Include unit tests

## 🚨 Troubleshooting

### Common Issues

**Node won't start**
- Check port availability
- Verify data directory permissions
- Review logs in `~/.gsccoin/logs/`

**Low peer count**
- Check firewall settings
- Verify seed node connectivity
- Review network configuration

**High memory usage**
- Increase system RAM
- Optimize blockchain pruning
- Monitor mempool size

**Sync issues**
- Restart node
- Clear peer connections
- Verify blockchain integrity

### Log Locations
- Node logs: `~/.gsccoin/logs/node.log`
- Network logs: `~/.gsccoin/logs/network.log`
- API logs: `~/.gsccoin/logs/api.log`

## 📞 Support

### Community
- GitHub Issues: Report bugs and feature requests
- Discord: Real-time community support
- Documentation: Comprehensive guides and tutorials

### Professional Support
- Enterprise deployment assistance
- Custom feature development
- 24/7 monitoring and maintenance
- Security audits and compliance

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Core blockchain implementation
- ✅ P2P networking
- ✅ Wallet management
- ✅ REST API
- ✅ Docker deployment
- ✅ Cloud deployment tools

### Phase 2 (Q2 2026)
- Smart contract support
- Mobile wallet applications
- Exchange integrations
- Advanced mining pools
- Governance mechanisms

### Phase 3 (Q3 2026)
- Layer 2 scaling solutions
- Cross-chain bridges
- DeFi protocol integrations
- NFT marketplace
- Staking mechanisms

---

**GSC Coin - The Future of Digital Currency** 🚀

Built with ❤️ for the decentralized future.
