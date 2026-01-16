#!/usr/bin/env python3
"""
Quick fix for GUI network address display
Adds the copy methods and updates network info display
"""

def add_copy_methods():
    """Add copy methods for network addresses"""
    
    copy_methods = '''
    def copy_local_ip(self):
        """Copy local IP address to clipboard"""
        try:
            if self.network_node:
                addresses = self.network_node.get_network_addresses()
                self.root.clipboard_clear()
                self.root.clipboard_append(addresses['local_ip'])
                messagebox.showinfo("Copied", f"Local IP copied: {addresses['local_ip']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy IP: {e}")
    
    def copy_p2p_address(self):
        """Copy P2P address to clipboard"""
        try:
            if self.network_node:
                addresses = self.network_node.get_network_addresses()
                self.root.clipboard_clear()
                self.root.clipboard_append(addresses['p2p_address'])
                messagebox.showinfo("Copied", f"P2P Address copied: {addresses['p2p_address']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy P2P address: {e}")
    
    def copy_rpc_address(self):
        """Copy RPC address to clipboard"""
        try:
            if self.network_node:
                addresses = self.network_node.get_network_addresses()
                self.root.clipboard_clear()
                self.root.clipboard_append(addresses['rpc_address'])
                messagebox.showinfo("Copied", f"RPC Address copied: {addresses['rpc_address']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy RPC address: {e}")
    
    def copy_node_id(self):
        """Copy Node ID to clipboard"""
        try:
            if self.network_node:
                addresses = self.network_node.get_network_addresses()
                self.root.clipboard_clear()
                self.root.clipboard_append(addresses['node_id'])
                messagebox.showinfo("Copied", f"Node ID copied: {addresses['node_id']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy Node ID: {e}")
'''
    
    return copy_methods

def update_network_info_method():
    """Updated network info method with address display"""
    
    method = '''
    def update_network_info(self):
        """Update network information display"""
        if not self.network_node:
            return
        
        try:
            # Get network addresses
            addresses = self.network_node.get_network_addresses()
            
            # Update connection info labels if they exist
            if hasattr(self, 'local_ip_label'):
                self.local_ip_label.config(text=addresses['local_ip'])
            if hasattr(self, 'p2p_address_label'):
                self.p2p_address_label.config(text=addresses['p2p_address'])
            if hasattr(self, 'rpc_address_label'):
                self.rpc_address_label.config(text=addresses['rpc_address'])
            if hasattr(self, 'node_id_label'):
                self.node_id_label.config(text=addresses['node_id'][:16] + "...")
            
            # Update peer count and status
            peer_count = len(self.network_node.peers)
            if hasattr(self, 'peer_count_label'):
                self.peer_count_label.config(text=str(peer_count))
            
            if hasattr(self, 'network_status_label'):
                if peer_count > 0:
                    self.network_status_label.config(text="🟢 Connected", foreground="green")
                else:
                    self.network_status_label.config(text="🔴 Disconnected", foreground="red")
            
            # Update peers list
            if hasattr(self, 'peers_listbox'):
                self.peers_listbox.delete(0, tk.END)
                for peer in sorted(self.network_node.peers):
                    self.peers_listbox.insert(tk.END, f"📡 {peer}")
            
            # Update network summary
            network_text = f"""Network Status: {'🟢 Online' if peer_count > 0 else '🔴 Offline'}
Connected Peers: {peer_count}
Your IP Address: {addresses['local_ip']}
P2P Address: {addresses['p2p_address']}
RPC Address: {addresses['rpc_address']}
Node ID: {addresses['node_id']}
Port: {self.network_node.port}
Chain Height: {len(self.blockchain.chain)}
Mempool Size: {len(self.blockchain.mempool)}

📋 Connection Instructions:
1. Share your P2P Address with others: {addresses['p2p_address']}
2. Others can connect using Manual Connect above
3. Use their P2P Address to connect to them

Peer List:
"""
            for peer in sorted(self.network_node.peers):
                network_text += f"  • {peer}\\n"
            
            if peer_count == 0:
                network_text += "  No peers connected - Share your P2P Address to get connections\\n"
            
            if hasattr(self, 'network_summary'):
                self.network_summary.delete(1.0, tk.END)
                self.network_summary.insert(1.0, network_text)
            
        except Exception as e:
            print(f"Error updating network info: {e}")
'''
    
    return method

if __name__ == "__main__":
    print("Network GUI fix methods ready")
    print("Copy methods:")
    print(add_copy_methods())
    print("\nUpdated network info method:")
    print(update_network_info_method())
