"""
GSC Coin Mainnet Package
Production-ready GSC blockchain implementation
"""

from .config import Config, MainnetConfig, TestnetConfig
from .mainnet_blockchain import MainnetBlockchain, MainnetTransaction, MainnetBlock
from .mainnet_network import MainnetNetworkNode, NetworkMessage, PeerConnection

__version__ = "1.0.0"
__all__ = [
    'Config',
    'MainnetConfig', 
    'TestnetConfig',
    'MainnetBlockchain',
    'MainnetTransaction',
    'MainnetBlock',
    'MainnetNetworkNode',
    'NetworkMessage',
    'PeerConnection'
]
