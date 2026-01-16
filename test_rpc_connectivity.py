"""
GSC Coin RPC Connectivity Test
Test RPC server connectivity from different IPs and networks
"""

import json
import requests
import socket
import time
from rpc_config import rpc_config

class RPCConnectivityTester:
    """Test RPC server connectivity"""
    
    def __init__(self, host='127.0.0.1', port=8332):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
    
    def test_basic_connectivity(self):
        """Test basic HTTP connectivity"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_rpc_call(self, method="getblockchaininfo", params=None):
        """Test JSON-RPC call"""
        if params is None:
            params = []
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.json()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_network_connectivity(self):
        """Test network-level connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            return {
                "success": result == 0,
                "port_open": result == 0,
                "error": f"Connection failed with code {result}" if result != 0 else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def comprehensive_test(self):
        """Run comprehensive connectivity tests"""
        print(f"Testing RPC connectivity to {self.base_url}")
        print("=" * 60)
        
        # Test 1: Network connectivity
        print("1. Testing network connectivity...")
        network_result = self.test_network_connectivity()
        if network_result["success"]:
            print("   ✅ Port is open and accepting connections")
        else:
            print(f"   ❌ Network connectivity failed: {network_result['error']}")
            return False
        
        # Test 2: Basic HTTP connectivity
        print("2. Testing HTTP connectivity...")
        http_result = self.test_basic_connectivity()
        if http_result["success"]:
            print("   ✅ HTTP server responding")
            print(f"   📊 Server info: {http_result['response'].get('name', 'Unknown')}")
        else:
            print(f"   ❌ HTTP connectivity failed: {http_result['error']}")
            return False
        
        # Test 3: RPC functionality
        print("3. Testing RPC functionality...")
        rpc_result = self.test_rpc_call()
        if rpc_result["success"]:
            print("   ✅ RPC calls working")
            blockchain_info = rpc_result["response"].get("result", {})
            print(f"   📊 Blockchain height: {blockchain_info.get('blocks', 0)}")
            print(f"   📊 Best block hash: {blockchain_info.get('bestblockhash', 'N/A')[:16]}...")
        else:
            print(f"   ❌ RPC functionality failed: {rpc_result['error']}")
            return False
        
        # Test 4: Multiple RPC methods
        print("4. Testing multiple RPC methods...")
        methods_to_test = [
            ("getblockcount", []),
            ("getmempoolinfo", []),
            ("getnetworkinfo", [])
        ]
        
        for method, params in methods_to_test:
            result = self.test_rpc_call(method, params)
            if result["success"]:
                print(f"   ✅ {method}: OK")
            else:
                print(f"   ❌ {method}: {result['error']}")
        
        print("\n🎉 All connectivity tests passed!")
        return True

def test_external_connectivity():
    """Test connectivity from external perspective"""
    network_info = rpc_config.get_network_info()
    
    print("GSC Coin RPC External Connectivity Test")
    print("=" * 50)
    print(f"Local IP: {network_info['local_ip']}")
    print(f"Public IP: {network_info['public_ip']}")
    print(f"RPC Port: {network_info['rpc_port']}")
    print()
    
    # Test localhost
    print("Testing localhost connectivity...")
    local_tester = RPCConnectivityTester('127.0.0.1', network_info['rpc_port'])
    local_success = local_tester.comprehensive_test()
    
    print("\n" + "=" * 50)
    
    # Test network IP
    if network_info['local_ip'] != '127.0.0.1':
        print("Testing network IP connectivity...")
        network_tester = RPCConnectivityTester(network_info['local_ip'], network_info['rpc_port'])
        network_success = network_tester.comprehensive_test()
    else:
        network_success = True
        print("Network IP same as localhost, skipping...")
    
    print("\n" + "=" * 50)
    print("CONNECTIVITY SUMMARY")
    print("=" * 50)
    print(f"Localhost (127.0.0.1): {'✅ WORKING' if local_success else '❌ FAILED'}")
    print(f"Network ({network_info['local_ip']}): {'✅ WORKING' if network_success else '❌ FAILED'}")
    
    if local_success and network_success:
        print("\n🎉 RPC server is properly configured for external access!")
        print("\nConnection URLs:")
        print(f"  Local: {network_info['local_url']}")
        print(f"  Network: {network_info['network_url']}")
        print(f"  External: {network_info['external_url']}")
        print("\nFirewall Configuration:")
        firewall_info = rpc_config.get_firewall_info()
        print(f"  Windows: {firewall_info['windows_firewall_command']}")
        print(f"  Linux: {firewall_info['linux_ufw_command']}")
        print(f"  Router: {firewall_info['router_port_forward']}")
    else:
        print("\n❌ RPC server connectivity issues detected!")
        print("Check firewall settings and network configuration.")
    
    return local_success and network_success

if __name__ == "__main__":
    test_external_connectivity()
