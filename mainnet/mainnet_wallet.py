"""
GSC Coin Mainnet Wallet Management
Production-ready wallet with enhanced security features
"""

import os
import json
import hashlib
import secrets
import base64
import time
import logging
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import mnemonic
from .config import Config
from .mainnet_blockchain import MainnetTransaction

logger = logging.getLogger(__name__)

class MainnetWallet:
    """Production-ready wallet with enhanced security"""
    
    def __init__(self, name: str, password: str = None):
        self.name = name
        self.address = ""
        self.private_key = None
        self.public_key = None
        self.encrypted_private_key = None
        self.salt = None
        self.is_encrypted = False
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.transaction_history = []
        
        # Security features
        self.failed_attempts = 0
        self.locked_until = 0
        self.backup_created = False
        
        if password:
            self.is_encrypted = True
            self._generate_keys()
            self._encrypt_private_key(password)
        else:
            self._generate_keys()
    
    def _generate_keys(self):
        """Generate RSA key pair for the wallet"""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        self.private_key = private_pem
        self.public_key = public_pem
        
        # Generate address from public key
        self.address = self._generate_address(public_pem)
        
        logger.info(f"Generated new wallet keys for {self.name}")
    
    def _generate_address(self, public_key_pem: bytes) -> str:
        """Generate wallet address from public key"""
        # Hash the public key
        digest = hashes.Hash(hashes.SHA256())
        digest.update(public_key_pem)
        hash1 = digest.finalize()
        
        # Hash again with RIPEMD160 (simplified with SHA256)
        digest2 = hashes.Hash(hashes.SHA256())
        digest2.update(hash1)
        hash2 = digest2.finalize()
        
        # Take first 20 bytes and encode as GSC address
        address_bytes = hash2[:20]
        address = "GSC" + base64.b32encode(address_bytes).decode('ascii').rstrip('=')
        
        return address
    
    def _encrypt_private_key(self, password: str):
        """Encrypt private key with password"""
        # Generate salt
        self.salt = secrets.token_bytes(32)
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Encrypt private key
        fernet = Fernet(key)
        self.encrypted_private_key = fernet.encrypt(self.private_key)
        
        # Clear plaintext private key
        self.private_key = None
        
        logger.info(f"Private key encrypted for wallet {self.name}")
    
    def unlock(self, password: str) -> bool:
        """Unlock encrypted wallet"""
        if not self.is_encrypted:
            return True
        
        # Check if wallet is locked due to failed attempts
        if time.time() < self.locked_until:
            remaining = int(self.locked_until - time.time())
            logger.warning(f"Wallet {self.name} is locked for {remaining} more seconds")
            return False
        
        try:
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Decrypt private key
            fernet = Fernet(key)
            self.private_key = fernet.decrypt(self.encrypted_private_key)
            
            # Reset failed attempts
            self.failed_attempts = 0
            self.last_accessed = time.time()
            
            logger.info(f"Wallet {self.name} unlocked successfully")
            return True
            
        except Exception as e:
            self.failed_attempts += 1
            
            # Lock wallet after 3 failed attempts
            if self.failed_attempts >= 3:
                self.locked_until = time.time() + (300 * self.failed_attempts)  # 5 min * attempts
                logger.warning(f"Wallet {self.name} locked due to failed attempts")
            
            logger.error(f"Failed to unlock wallet {self.name}: {e}")
            return False
    
    def lock(self):
        """Lock the wallet by clearing private key"""
        if self.is_encrypted:
            self.private_key = None
            logger.info(f"Wallet {self.name} locked")
    
    def sign_transaction(self, transaction: MainnetTransaction) -> str:
        """Sign a transaction with the wallet's private key"""
        if not self.private_key:
            raise ValueError("Wallet is locked or not initialized")
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            self.private_key,
            password=None
        )
        
        # Create transaction data to sign
        tx_data = f"{transaction.sender}{transaction.receiver}{transaction.amount}{transaction.fee}{transaction.timestamp}"
        
        # Sign the transaction
        signature = private_key.sign(
            tx_data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Return base64 encoded signature
        return base64.b64encode(signature).decode('ascii')
    
    def verify_signature(self, transaction: MainnetTransaction, signature: str, public_key_pem: bytes = None) -> bool:
        """Verify transaction signature"""
        try:
            # Use provided public key or wallet's public key
            if public_key_pem is None:
                public_key_pem = self.public_key
            
            # Load public key
            public_key = serialization.load_pem_public_key(public_key_pem)
            
            # Create transaction data
            tx_data = f"{transaction.sender}{transaction.receiver}{transaction.amount}{transaction.fee}{transaction.timestamp}"
            
            # Decode signature
            signature_bytes = base64.b64decode(signature.encode('ascii'))
            
            # Verify signature
            public_key.verify(
                signature_bytes,
                tx_data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def create_backup(self) -> dict:
        """Create wallet backup data"""
        backup_data = {
            'name': self.name,
            'address': self.address,
            'public_key': base64.b64encode(self.public_key).decode('ascii'),
            'created_at': self.created_at,
            'backup_created_at': time.time(),
            'version': 1
        }
        
        if self.is_encrypted:
            backup_data.update({
                'encrypted_private_key': base64.b64encode(self.encrypted_private_key).decode('ascii'),
                'salt': base64.b64encode(self.salt).decode('ascii'),
                'is_encrypted': True
            })
        else:
            backup_data.update({
                'private_key': base64.b64encode(self.private_key).decode('ascii'),
                'is_encrypted': False
            })
        
        self.backup_created = True
        logger.info(f"Backup created for wallet {self.name}")
        return backup_data
    
    def to_dict(self) -> dict:
        """Convert wallet to dictionary for storage"""
        wallet_data = {
            'name': self.name,
            'address': self.address,
            'public_key': base64.b64encode(self.public_key).decode('ascii'),
            'is_encrypted': self.is_encrypted,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'failed_attempts': self.failed_attempts,
            'locked_until': self.locked_until,
            'backup_created': self.backup_created,
            'transaction_history': self.transaction_history
        }
        
        if self.is_encrypted:
            wallet_data.update({
                'encrypted_private_key': base64.b64encode(self.encrypted_private_key).decode('ascii'),
                'salt': base64.b64encode(self.salt).decode('ascii')
            })
        else:
            wallet_data.update({
                'private_key': base64.b64encode(self.private_key).decode('ascii')
            })
        
        return wallet_data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MainnetWallet':
        """Create wallet from dictionary"""
        wallet = cls.__new__(cls)
        wallet.name = data['name']
        wallet.address = data['address']
        wallet.public_key = base64.b64decode(data['public_key'].encode('ascii'))
        wallet.is_encrypted = data['is_encrypted']
        wallet.created_at = data['created_at']
        wallet.last_accessed = data['last_accessed']
        wallet.failed_attempts = data.get('failed_attempts', 0)
        wallet.locked_until = data.get('locked_until', 0)
        wallet.backup_created = data.get('backup_created', False)
        wallet.transaction_history = data.get('transaction_history', [])
        
        if wallet.is_encrypted:
            wallet.encrypted_private_key = base64.b64decode(data['encrypted_private_key'].encode('ascii'))
            wallet.salt = base64.b64decode(data['salt'].encode('ascii'))
            wallet.private_key = None
        else:
            wallet.private_key = base64.b64decode(data['private_key'].encode('ascii'))
            wallet.encrypted_private_key = None
            wallet.salt = None
        
        return wallet

class MainnetWalletManager:
    """Production-ready wallet manager"""
    
    def __init__(self):
        self.wallets: Dict[str, MainnetWallet] = {}
        self.wallet_dir = os.path.join(Config.get_data_dir(), Config.WALLET_DIR)
        self.current_wallet = None
        
        # Ensure wallet directory exists
        os.makedirs(self.wallet_dir, exist_ok=True)
        
        # Load existing wallets
        self._load_wallets()
    
    def _load_wallets(self):
        """Load wallets from disk"""
        try:
            for filename in os.listdir(self.wallet_dir):
                if filename.endswith('.wallet'):
                    wallet_path = os.path.join(self.wallet_dir, filename)
                    with open(wallet_path, 'r') as f:
                        wallet_data = json.load(f)
                    
                    wallet = MainnetWallet.from_dict(wallet_data)
                    self.wallets[wallet.name] = wallet
                    
            logger.info(f"Loaded {len(self.wallets)} wallets")
            
        except Exception as e:
            logger.error(f"Failed to load wallets: {e}")
    
    def create_wallet(self, name: str, password: str = None) -> MainnetWallet:
        """Create a new wallet"""
        if name in self.wallets:
            raise ValueError(f"Wallet '{name}' already exists")
        
        # Create new wallet
        wallet = MainnetWallet(name, password)
        self.wallets[name] = wallet
        
        # Save wallet to disk
        self._save_wallet(wallet)
        
        logger.info(f"Created new wallet: {name}")
        return wallet
    
    def open_wallet(self, name: str, password: str = None) -> MainnetWallet:
        """Open an existing wallet"""
        if name not in self.wallets:
            raise ValueError(f"Wallet '{name}' not found")
        
        wallet = self.wallets[name]
        
        if wallet.is_encrypted:
            if not password:
                raise ValueError("Password required for encrypted wallet")
            
            if not wallet.unlock(password):
                raise ValueError("Failed to unlock wallet")
        
        self.current_wallet = wallet
        wallet.last_accessed = time.time()
        self._save_wallet(wallet)
        
        logger.info(f"Opened wallet: {name}")
        return wallet
    
    def close_wallet(self, name: str = None):
        """Close a wallet"""
        if name:
            if name in self.wallets:
                self.wallets[name].lock()
        else:
            if self.current_wallet:
                self.current_wallet.lock()
                self.current_wallet = None
        
        logger.info(f"Closed wallet: {name or 'current'}")
    
    def delete_wallet(self, name: str, password: str = None) -> bool:
        """Delete a wallet (requires password if encrypted)"""
        if name not in self.wallets:
            return False
        
        wallet = self.wallets[name]
        
        # Verify password for encrypted wallets
        if wallet.is_encrypted:
            if not password or not wallet.unlock(password):
                raise ValueError("Invalid password")
        
        # Remove wallet file
        wallet_path = os.path.join(self.wallet_dir, f"{name}.wallet")
        if os.path.exists(wallet_path):
            os.remove(wallet_path)
        
        # Remove from memory
        del self.wallets[name]
        
        if self.current_wallet and self.current_wallet.name == name:
            self.current_wallet = None
        
        logger.info(f"Deleted wallet: {name}")
        return True
    
    def _save_wallet(self, wallet: MainnetWallet):
        """Save wallet to disk"""
        wallet_path = os.path.join(self.wallet_dir, f"{wallet.name}.wallet")
        
        with open(wallet_path, 'w') as f:
            json.dump(wallet.to_dict(), f, indent=2)
    
    def list_wallets(self) -> List[str]:
        """List all wallet names"""
        return list(self.wallets.keys())
    
    def get_wallet_info(self, name: str) -> dict:
        """Get wallet information"""
        if name not in self.wallets:
            return None
        
        wallet = self.wallets[name]
        return {
            'name': wallet.name,
            'address': wallet.address,
            'is_encrypted': wallet.is_encrypted,
            'created_at': wallet.created_at,
            'last_accessed': wallet.last_accessed,
            'backup_created': wallet.backup_created,
            'is_locked': wallet.private_key is None and wallet.is_encrypted
        }
    
    def backup_wallet(self, name: str, backup_path: str, password: str = None) -> bool:
        """Create wallet backup"""
        if name not in self.wallets:
            return False
        
        wallet = self.wallets[name]
        
        # Verify password for encrypted wallets
        if wallet.is_encrypted:
            if not password or not wallet.unlock(password):
                raise ValueError("Invalid password")
        
        # Create backup
        backup_data = wallet.create_backup()
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        # Update wallet
        self._save_wallet(wallet)
        
        logger.info(f"Wallet {name} backed up to {backup_path}")
        return True
    
    def restore_wallet(self, backup_path: str, password: str = None) -> MainnetWallet:
        """Restore wallet from backup"""
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        name = backup_data['name']
        
        if name in self.wallets:
            raise ValueError(f"Wallet '{name}' already exists")
        
        # Create wallet from backup
        wallet = MainnetWallet.__new__(MainnetWallet)
        wallet.name = name
        wallet.address = backup_data['address']
        wallet.public_key = base64.b64decode(backup_data['public_key'].encode('ascii'))
        wallet.is_encrypted = backup_data['is_encrypted']
        wallet.created_at = backup_data['created_at']
        wallet.last_accessed = time.time()
        wallet.failed_attempts = 0
        wallet.locked_until = 0
        wallet.backup_created = True
        wallet.transaction_history = []
        
        if wallet.is_encrypted:
            wallet.encrypted_private_key = base64.b64decode(backup_data['encrypted_private_key'].encode('ascii'))
            wallet.salt = base64.b64decode(backup_data['salt'].encode('ascii'))
            wallet.private_key = None
            
            # Unlock if password provided
            if password:
                wallet.unlock(password)
        else:
            wallet.private_key = base64.b64decode(backup_data['private_key'].encode('ascii'))
            wallet.encrypted_private_key = None
            wallet.salt = None
        
        # Add to manager
        self.wallets[name] = wallet
        self._save_wallet(wallet)
        
        logger.info(f"Restored wallet: {name}")
        return wallet
    
    def change_password(self, name: str, old_password: str, new_password: str) -> bool:
        """Change wallet password"""
        if name not in self.wallets:
            return False
        
        wallet = self.wallets[name]
        
        if not wallet.is_encrypted:
            # Encrypt wallet with new password
            wallet._encrypt_private_key(new_password)
        else:
            # Unlock with old password
            if not wallet.unlock(old_password):
                return False
            
            # Re-encrypt with new password
            wallet._encrypt_private_key(new_password)
        
        # Save updated wallet
        self._save_wallet(wallet)
        
        logger.info(f"Password changed for wallet: {name}")
        return True
    
    def get_current_wallet(self) -> Optional[MainnetWallet]:
        """Get currently open wallet"""
        return self.current_wallet
