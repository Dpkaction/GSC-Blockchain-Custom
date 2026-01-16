"""
GSC Coin RPC Configuration
Network configuration for external IP connectivity
"""

import socket
import json
import os

class RPCConfig:
    """RPC Server Configuration Manager"""
    
    def __init__(self):
        self.config_file = "rpc_config.json"
        self.default_config = {
            "rpc_host": "0.0.0.0",  # Accept connections from all IPs
            "rpc_port": 8332,
            "rpc_allow_ip": ["*"],  # Allow all IPs (use with caution)
            "rpc_timeout": 30,
            "rpc_max_connections": 100,
            "rpc_auth_required": False,
            "rpc_username": "",
            "rpc_password": "",
            "enable_cors": True,
            "log_requests": True,
            "rate_limit_enabled": True,
            "rate_limit_requests": 30,
            "rate_limit_window": 60
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading RPC config: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """Save configuration to file"""
        try:
            config_to_save = config or self.config
            with open(self.config_file, 'w') as f:
                json.dump(config_to_save, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving RPC config: {e}")
            return False
    
    def get_local_ip(self):
        """Get local network IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def get_public_ip(self):
        """Get public IP address (requires internet)"""
        try:
            import urllib.request
            response = urllib.request.urlopen('https://api.ipify.org', timeout=5)
            return response.read().decode('utf-8')
        except:
            return "Unknown"
    
    def get_network_info(self):
        """Get comprehensive network information"""
        return {
            "local_ip": self.get_local_ip(),
            "public_ip": self.get_public_ip(),
            "rpc_host": self.config["rpc_host"],
            "rpc_port": self.config["rpc_port"],
            "local_url": f"http://127.0.0.1:{self.config['rpc_port']}",
            "network_url": f"http://{self.get_local_ip()}:{self.config['rpc_port']}",
            "external_url": f"http://{self.get_public_ip()}:{self.config['rpc_port']}"
        }
    
    def is_ip_allowed(self, ip):
        """Check if IP is allowed to connect"""
        if "*" in self.config["rpc_allow_ip"]:
            return True
        return ip in self.config["rpc_allow_ip"]
    
    def add_allowed_ip(self, ip):
        """Add IP to allowed list"""
        if ip not in self.config["rpc_allow_ip"]:
            self.config["rpc_allow_ip"].append(ip)
            self.save_config()
    
    def remove_allowed_ip(self, ip):
        """Remove IP from allowed list"""
        if ip in self.config["rpc_allow_ip"]:
            self.config["rpc_allow_ip"].remove(ip)
            self.save_config()
    
    def test_connectivity(self):
        """Test network connectivity"""
        results = {}
        
        # Test local connectivity
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', self.config["rpc_port"]))
            s.close()
            results["local"] = result == 0
        except:
            results["local"] = False
        
        # Test network connectivity
        try:
            local_ip = self.get_local_ip()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            result = s.connect_ex((local_ip, self.config["rpc_port"]))
            s.close()
            results["network"] = result == 0
        except:
            results["network"] = False
        
        return results
    
    def get_firewall_info(self):
        """Get firewall configuration info"""
        return {
            "port": self.config["rpc_port"],
            "windows_firewall_command": f"netsh advfirewall firewall add rule name=\"GSC Coin RPC\" dir=in action=allow protocol=TCP localport={self.config['rpc_port']}",
            "linux_ufw_command": f"sudo ufw allow {self.config['rpc_port']}/tcp",
            "router_port_forward": f"Forward external port {self.config['rpc_port']} to internal IP {self.get_local_ip()}:{self.config['rpc_port']}"
        }

# Global configuration instance
rpc_config = RPCConfig()
