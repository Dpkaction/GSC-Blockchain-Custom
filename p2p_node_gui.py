#!/usr/bin/env python3
"""
Bitcoin P2P Node GUI
===================
Simple GUI to test Bitcoin-style P2P networking
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from bitcoin_p2p_node import BitcoinP2PNode

class P2PNodeGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bitcoin P2P Node Tester")
        self.root.geometry("800x600")
        
        self.node = None
        self.update_thread = None
        self.running = False
        
        self.setup_gui()
    
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Node control section
        control_frame = ttk.LabelFrame(main_frame, text="Node Control", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Port input
        port_frame = ttk.Frame(control_frame)
        port_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value="5000")
        self.port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        # Start/Stop buttons
        self.start_button = ttk.Button(port_frame, text="Start Node", command=self.start_node)
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        self.stop_button = ttk.Button(port_frame, text="Stop Node", command=self.stop_node, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status display
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="Stopped", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(status_frame, text="Node ID:").pack(side=tk.LEFT, padx=(20, 0))
        self.node_id_label = ttk.Label(status_frame, text="N/A")
        self.node_id_label.pack(side=tk.LEFT, padx=5)
        
        # Manual connection section
        connect_frame = ttk.LabelFrame(main_frame, text="Manual Connect", padding=10)
        connect_frame.pack(fill=tk.X, pady=(0, 10))
        
        connect_input_frame = ttk.Frame(connect_frame)
        connect_input_frame.pack(fill=tk.X)
        
        ttk.Label(connect_input_frame, text="IP:").pack(side=tk.LEFT)
        self.connect_ip_var = tk.StringVar(value="127.0.0.1")
        self.connect_ip_entry = ttk.Entry(connect_input_frame, textvariable=self.connect_ip_var, width=15)
        self.connect_ip_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(connect_input_frame, text="Port:").pack(side=tk.LEFT, padx=(10, 0))
        self.connect_port_var = tk.StringVar(value="5001")
        self.connect_port_entry = ttk.Entry(connect_input_frame, textvariable=self.connect_port_var, width=8)
        self.connect_port_entry.pack(side=tk.LEFT, padx=5)
        
        self.connect_button = ttk.Button(connect_input_frame, text="Connect", command=self.manual_connect, state=tk.DISABLED)
        self.connect_button.pack(side=tk.LEFT, padx=10)
        
        # Peer status section
        peer_frame = ttk.LabelFrame(main_frame, text="Connected Peers", padding=10)
        peer_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Peer count
        peer_count_frame = ttk.Frame(peer_frame)
        peer_count_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(peer_count_frame, text="Connected:").pack(side=tk.LEFT)
        self.peer_count_label = ttk.Label(peer_count_frame, text="0", font=('Arial', 12, 'bold'), foreground="blue")
        self.peer_count_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(peer_count_frame, text="Known:").pack(side=tk.LEFT, padx=(20, 0))
        self.known_count_label = ttk.Label(peer_count_frame, text="0", font=('Arial', 12, 'bold'), foreground="green")
        self.known_count_label.pack(side=tk.LEFT, padx=5)
        
        # Peer list
        self.peer_listbox = tk.Listbox(peer_frame, height=8)
        self.peer_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        peer_scroll = ttk.Scrollbar(peer_frame, command=self.peer_listbox.yview)
        peer_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.peer_listbox.config(yscrollcommand=peer_scroll.set)
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Network Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Redirect print to log
        import sys
        sys.stdout = LogRedirector(self.log_text)
    
    def start_node(self):
        try:
            port = int(self.port_var.get())
            self.node = BitcoinP2PNode(port=port)
            self.node.start()
            
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.connect_button.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.DISABLED)
            
            self.status_label.config(text="Running", foreground="green")
            self.node_id_label.config(text=self.node.node_id)
            
            # Start update thread
            self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
            self.update_thread.start()
            
            self.log("Node started successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start node: {e}")
    
    def stop_node(self):
        if self.node:
            self.node.stop()
            self.node = None
        
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.connect_button.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.NORMAL)
        
        self.status_label.config(text="Stopped", foreground="red")
        self.node_id_label.config(text="N/A")
        self.peer_count_label.config(text="0")
        self.known_count_label.config(text="0")
        
        self.peer_listbox.delete(0, tk.END)
        
        self.log("Node stopped")
    
    def manual_connect(self):
        if not self.node:
            return
        
        try:
            ip = self.connect_ip_var.get().strip()
            port = int(self.connect_port_var.get())
            
            if self.node.manual_connect(ip, port):
                self.log(f"Manual connection to {ip}:{port} initiated")
            else:
                self.log(f"Failed to connect to {ip}:{port}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {e}")
    
    def update_loop(self):
        """Update GUI with node status"""
        while self.running and self.node:
            try:
                status = self.node.get_status()
                
                # Update peer counts
                self.root.after(0, lambda: self.peer_count_label.config(text=str(status['connected_peers'])))
                self.root.after(0, lambda: self.known_count_label.config(text=str(status['known_peers'])))
                
                # Update peer list
                def update_peer_list():
                    self.peer_listbox.delete(0, tk.END)
                    for peer in status['peer_list']:
                        self.peer_listbox.insert(tk.END, f"🔗 {peer}")
                
                self.root.after(0, update_peer_list)
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                self.log(f"Update error: {e}")
                break
    
    def log(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        if self.node:
            self.stop_node()
        self.root.destroy()


class LogRedirector:
    """Redirect print statements to GUI log"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
    
    def write(self, message):
        if message.strip():  # Only log non-empty messages
            timestamp = time.strftime("%H:%M:%S")
            self.text_widget.insert(tk.END, f"[{timestamp}] {message}")
            self.text_widget.see(tk.END)
    
    def flush(self):
        pass


if __name__ == "__main__":
    app = P2PNodeGUI()
    app.run()
