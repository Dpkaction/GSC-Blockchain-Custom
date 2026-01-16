#!/usr/bin/env python3
"""
GSC Coin Enhanced Wallet GUI
Modern interface with Bitcoin-like functionality and executable build support
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class GSCWalletGUI:
    """Enhanced GSC Coin Wallet GUI with Bitcoin-like functionality"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🪙 GSC Coin Wallet - Enhanced")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize blockchain components
        self.blockchain = None
        self.network_node = None
        self.wallet_manager = None
        self.mining_thread = None
        self.is_mining = False
        
        # Style configuration
        self.setup_styles()
        
        # Create main interface
        self.create_main_interface()
        
        # Initialize blockchain in background
        self.initialize_blockchain()
    
    def setup_styles(self):
        """Setup modern dark theme styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        bg_color = '#2b2b2b'
        fg_color = '#ffffff'
        button_color = '#4a90e2'
        success_color = '#27ae60'
        warning_color = '#f39c12'
        error_color = '#e74c3c'
        
        # Configure styles
        style.configure('Title.TLabel', background=bg_color, foreground=fg_color, font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', background=bg_color, foreground=fg_color, font=('Arial', 12, 'bold'))
        style.configure('Info.TLabel', background=bg_color, foreground='#cccccc', font=('Arial', 10))
        style.configure('Success.TLabel', background=bg_color, foreground=success_color, font=('Arial', 10, 'bold'))
        style.configure('Warning.TLabel', background=bg_color, foreground=warning_color, font=('Arial', 10, 'bold'))
        style.configure('Error.TLabel', background=bg_color, foreground=error_color, font=('Arial', 10, 'bold'))
        style.configure('Modern.TButton', background=button_color, foreground=fg_color, font=('Arial', 10, 'bold'))
        style.configure('Modern.TFrame', background=bg_color)
        style.configure('Modern.TLabelframe', background=bg_color, foreground=fg_color, font=('Arial', 10, 'bold'))
        style.configure('Modern.TLabelframe.Label', background=bg_color, foreground=fg_color, font=('Arial', 10, 'bold'))
    
    def create_main_interface(self):
        """Create the main wallet interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root, style='Modern.TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_wallet_tab()
        self.create_send_tab()
        self.create_receive_tab()
        self.create_mining_tab()
        self.create_network_tab()
        self.create_console_tab()
        self.create_settings_tab()
    
    def create_dashboard_tab(self):
        """Create dashboard tab with overview"""
        dashboard_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(dashboard_frame, text='📊 Dashboard')
        
        # Title
        title_label = ttk.Label(dashboard_frame, text="🪙 GSC Coin Dashboard", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Create info grid
        info_frame = ttk.Frame(dashboard_frame, style='Modern.TFrame')
        info_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Blockchain Info
        blockchain_frame = ttk.LabelFrame(info_frame, text="📊 Blockchain Information", style='Modern.TLabelframe')
        blockchain_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        
        self.block_count_label = ttk.Label(blockchain_frame, text="Blocks: Loading...", style='Info.TLabel')
        self.block_count_label.pack(anchor='w', padx=10, pady=5)
        
        self.difficulty_label = ttk.Label(blockchain_frame, text="Difficulty: Loading...", style='Info.TLabel')
        self.difficulty_label.pack(anchor='w', padx=10, pady=5)
        
        self.best_hash_label = ttk.Label(blockchain_frame, text="Best Hash: Loading...", style='Info.TLabel')
        self.best_hash_label.pack(anchor='w', padx=10, pady=5)
        
        # Network Info
        network_frame = ttk.LabelFrame(info_frame, text="🌐 Network Status", style='Modern.TLabelframe')
        network_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        
        self.peers_label = ttk.Label(network_frame, text="Connected Peers: 0", style='Info.TLabel')
        self.peers_label.pack(anchor='w', padx=10, pady=5)
        
        self.banned_label = ttk.Label(network_frame, text="Banned Peers: 0", style='Info.TLabel')
        self.banned_label.pack(anchor='w', padx=10, pady=5)
        
        self.status_label = ttk.Label(network_frame, text="Status: Initializing...", style='Info.TLabel')
        self.status_label.pack(anchor='w', padx=10, pady=5)
        
        # Mining Info
        mining_frame = ttk.LabelFrame(info_frame, text="⛏️ Mining Status", style='Modern.TLabelframe')
        mining_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        
        self.mining_status_label = ttk.Label(mining_frame, text="Mining: Stopped", style='Info.TLabel')
        self.mining_status_label.pack(anchor='w', padx=10, pady=5)
        
        self.hashrate_label = ttk.Label(mining_frame, text="Hash Rate: 0 H/s", style='Info.TLabel')
        self.hashrate_label.pack(anchor='w', padx=10, pady=5)
        
        self.blocks_mined_label = ttk.Label(mining_frame, text="Blocks Mined: 0", style='Info.TLabel')
        self.blocks_mined_label.pack(anchor='w', padx=10, pady=5)
        
        # Recent Blocks
        recent_frame = ttk.LabelFrame(info_frame, text="🧱 Recent Blocks", style='Modern.TLabelframe')
        recent_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')
        
        self.recent_blocks_text = scrolledtext.ScrolledText(recent_frame, height=10, width=40, 
                                                      bg='#1e1e1e', fg='#ffffff', 
                                                      font=('Consolas', 9))
        self.recent_blocks_text.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Configure grid weights
        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)
        info_frame.rowconfigure(0, weight=1)
        info_frame.rowconfigure(1, weight=1)
        
        # Update dashboard periodically
        self.update_dashboard()
    
    def create_wallet_tab(self):
        """Create wallet management tab"""
        wallet_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(wallet_frame, text='👛️ Wallet')
        
        # Title
        title_label = ttk.Label(wallet_frame, text="👛️ Wallet Management", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Wallet info frame
        info_frame = ttk.Frame(wallet_frame, style='Modern.TFrame')
        info_frame.pack(fill='x', padx=20, pady=10)
        
        # Current wallet
        current_frame = ttk.LabelFrame(info_frame, text="Current Wallet", style='Modern.TLabelframe')
        current_frame.pack(fill='x', pady=10)
        
        self.current_wallet_label = ttk.Label(current_frame, text="No wallet loaded", style='Info.TLabel')
        self.current_wallet_label.pack(anchor='w', padx=10, pady=5)
        
        # Balance frame
        balance_frame = ttk.LabelFrame(info_frame, text="Balance", style='Modern.TLabelframe')
        balance_frame.pack(fill='x', pady=10)
        
        self.balance_label = ttk.Label(balance_frame, text="Balance: 0.00000000 GSC", style='Header.TLabel')
        self.balance_label.pack(anchor='w', padx=10, pady=5)
        
        # Address frame
        address_frame = ttk.LabelFrame(info_frame, text="Your Addresses", style='Modern.TLabelframe')
        address_frame.pack(fill='both', expand=True, pady=10)
        
        self.address_listbox = tk.Listbox(address_frame, bg='#1e1e1e', fg='#ffffff', 
                                      font=('Consolas', 9), height=8)
        self.address_listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(wallet_frame, style='Modern.TFrame')
        button_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(button_frame, text="Create New Wallet", command=self.create_wallet, 
                 style='Modern.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Wallet", command=self.load_wallet, 
                 style='Modern.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Generate Address", command=self.generate_address, 
                 style='Modern.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.refresh_wallet, 
                 style='Modern.TButton').pack(side='left', padx=5)
    
    def create_send_tab(self):
        """Create send transaction tab"""
        send_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(send_frame, text='💸 Send')
        
        # Title
        title_label = ttk.Label(send_frame, text="💸 Send GSC", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Send form
        form_frame = ttk.Frame(send_frame, style='Modern.TFrame')
        form_frame.pack(fill='x', padx=20, pady=10)
        
        # From address
        from_frame = ttk.Frame(form_frame, style='Modern.TFrame')
        from_frame.pack(fill='x', pady=5)
        ttk.Label(from_frame, text="From:", style='Header.TLabel').pack(side='left', padx=5)
        self.from_address_var = tk.StringVar()
        self.from_address_combo = ttk.Combobox(from_frame, textvariable=self.from_address_var, 
                                          state='readonly', width=50)
        self.from_address_combo.pack(side='left', padx=5, fill='x', expand=True)
        
        # To address
        to_frame = ttk.Frame(form_frame, style='Modern.TFrame')
        to_frame.pack(fill='x', pady=5)
        ttk.Label(to_frame, text="To:", style='Header.TLabel').pack(side='left', padx=5)
        self.to_address_var = tk.StringVar()
        self.to_address_entry = ttk.Entry(to_frame, textvariable=self.to_address_var, width=50)
        self.to_address_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # Amount
        amount_frame = ttk.Frame(form_frame, style='Modern.TFrame')
        amount_frame.pack(fill='x', pady=5)
        ttk.Label(amount_frame, text="Amount:", style='Header.TLabel').pack(side='left', padx=5)
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(amount_frame, textvariable=self.amount_var, width=20)
        self.amount_entry.pack(side='left', padx=5)
        ttk.Label(amount_frame, text="GSC", style='Info.TLabel').pack(side='left', padx=5)
        
        # Fee
        fee_frame = ttk.Frame(form_frame, style='Modern.TFrame')
        fee_frame.pack(fill='x', pady=5)
        ttk.Label(fee_frame, text="Fee:", style='Header.TLabel').pack(side='left', padx=5)
        self.fee_var = tk.StringVar(value="0.0001")
        self.fee_entry = ttk.Entry(fee_frame, textvariable=self.fee_var, width=20)
        self.fee_entry.pack(side='left', padx=5)
        ttk.Label(fee_frame, text="GSC", style='Info.TLabel').pack(side='left', padx=5)
        
        # Send button
        send_button_frame = ttk.Frame(send_frame, style='Modern.TFrame')
        send_button_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Button(send_button_frame, text="Send Transaction", command=self.send_transaction,
                 style='Modern.TButton').pack()
        
        # Transaction history
        history_frame = ttk.LabelFrame(send_frame, text="📜 Transaction History", style='Modern.TLabelframe')
        history_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.history_text = scrolledtext.ScrolledText(history_frame, height=15, 
                                               bg='#1e1e1e', fg='#ffffff', 
                                               font=('Consolas', 9))
        self.history_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_receive_tab(self):
        """Create receive tab"""
        receive_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(receive_frame, text='📥 Receive')
        
        # Title
        title_label = ttk.Label(receive_frame, text="📥 Receive GSC", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # QR Code frame (placeholder)
        qr_frame = ttk.LabelFrame(receive_frame, text="📱 Your Address", style='Modern.TLabelframe')
        qr_frame.pack(fill='x', padx=20, pady=10)
        
        self.receive_address_var = tk.StringVar()
        self.receive_address_label = ttk.Label(qr_frame, textvariable=self.receive_address_var, 
                                          style='Info.TLabel', font=('Consolas', 12))
        self.receive_address_label.pack(padx=10, pady=20)
        
        # Copy button
        ttk.Button(qr_frame, text="Copy Address", command=self.copy_address,
                 style='Modern.TButton').pack(pady=10)
        
        # Address list
        address_frame = ttk.LabelFrame(receive_frame, text="📋 All Addresses", style='Modern.TLabelframe')
        address_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.receive_address_listbox = tk.Listbox(address_frame, bg='#1e1e1e', fg='#ffffff',
                                             font=('Consolas', 9), height=12)
        self.receive_address_listbox.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_mining_tab(self):
        """Create mining tab"""
        mining_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(mining_frame, text='⛏️ Mining')
        
        # Title
        title_label = ttk.Label(mining_frame, text="⛏️ Mining Control", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Mining control
        control_frame = ttk.Frame(mining_frame, style='Modern.TFrame')
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # Mining address
        address_frame = ttk.Frame(control_frame, style='Modern.TFrame')
        address_frame.pack(fill='x', pady=5)
        ttk.Label(address_frame, text="Mining Address:", style='Header.TLabel').pack(side='left', padx=5)
        self.mining_address_var = tk.StringVar()
        self.mining_address_combo = ttk.Combobox(address_frame, textvariable=self.mining_address_var,
                                              state='readonly', width=50)
        self.mining_address_combo.pack(side='left', padx=5, fill='x', expand=True)
        
        # Mining buttons
        button_frame = ttk.Frame(mining_frame, style='Modern.TFrame')
        button_frame.pack(fill='x', padx=20, pady=10)
        
        self.start_mining_button = ttk.Button(button_frame, text="▶️ Start Mining", 
                                          command=self.start_mining, style='Modern.TButton')
        self.start_mining_button.pack(side='left', padx=5)
        
        self.stop_mining_button = ttk.Button(button_frame, text="⏹️ Stop Mining", 
                                         command=self.stop_mining, style='Modern.TButton', 
                                         state='disabled')
        self.stop_mining_button.pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Generate Block", command=self.generate_single_block,
                 style='Modern.TButton').pack(side='left', padx=5)
        
        # Mining status
        status_frame = ttk.LabelFrame(mining_frame, text="📊 Mining Statistics", style='Modern.TLabelframe')
        status_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.mining_log = scrolledtext.ScrolledText(status_frame, height=15, 
                                               bg='#1e1e1e', fg='#ffffff', 
                                               font=('Consolas', 9))
        self.mining_log.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_network_tab(self):
        """Create network tab"""
        network_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(network_frame, text='🌐 Network')
        
        # Title
        title_label = ttk.Label(network_frame, text="🌐 Network Status", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Network info
        info_frame = ttk.Frame(network_frame, style='Modern.TFrame')
        info_frame.pack(fill='x', padx=20, pady=10)
        
        # Connection status
        status_frame = ttk.LabelFrame(info_frame, text="Connection Status", style='Modern.TLabelframe')
        status_frame.pack(fill='x', pady=5)
        
        self.network_status_label = ttk.Label(status_frame, text="Status: Disconnected", style='Info.TLabel')
        self.network_status_label.pack(anchor='w', padx=10, pady=5)
        
        self.port_label = ttk.Label(status_frame, text="Port: 8333", style='Info.TLabel')
        self.port_label.pack(anchor='w', padx=10, pady=5)
        
        # Peer management
        peer_frame = ttk.LabelFrame(info_frame, text="Peer Management", style='Modern.TLabelframe')
        peer_frame.pack(fill='both', expand=True, pady=5)
        
        # Connect to peer
        connect_frame = ttk.Frame(peer_frame, style='Modern.TFrame')
        connect_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(connect_frame, text="Connect to:", style='Header.TLabel').pack(side='left', padx=5)
        self.peer_address_var = tk.StringVar()
        self.peer_address_entry = ttk.Entry(connect_frame, textvariable=self.peer_address_var, width=30)
        self.peer_address_entry.pack(side='left', padx=5)
        ttk.Button(connect_frame, text="Connect", command=self.connect_to_peer,
                 style='Modern.TButton').pack(side='left', padx=5)
        
        # Peer list
        list_frame = ttk.Frame(peer_frame, style='Modern.TFrame')
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.peer_listbox = tk.Listbox(list_frame, bg='#1e1e1e', fg='#ffffff',
                                     font=('Consolas', 9), height=10)
        self.peer_listbox.pack(side='left', fill='both', expand=True)
        
        # Peer buttons
        peer_button_frame = ttk.Frame(list_frame, style='Modern.TFrame')
        peer_button_frame.pack(side='right', padx=5, fill='y')
        
        ttk.Button(peer_button_frame, text="Refresh", command=self.refresh_peers,
                 style='Modern.TButton').pack(pady=5)
        ttk.Button(peer_button_frame, text="Disconnect", command=self.disconnect_peer,
                 style='Modern.TButton').pack(pady=5)
        ttk.Button(peer_button_frame, text="Ban Peer", command=self.ban_peer,
                 style='Modern.TButton').pack(pady=5)
    
    def create_console_tab(self):
        """Create console tab with command dropdown"""
        console_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(console_frame, text='💻 Console')
        
        # Title
        title_label = ttk.Label(console_frame, text="💻 GSC Console", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Command selection
        command_frame = ttk.Frame(console_frame, style='Modern.TFrame')
        command_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(command_frame, text="Command:", style='Header.TLabel').pack(side='left', padx=5)
        self.command_var = tk.StringVar()
        self.command_combo = ttk.Combobox(command_frame, textvariable=self.command_var,
                                       values=[
                                           'getblockchaininfo',
                                           'getmininginfo', 
                                           'getpeerinfo',
                                           'getblockcount',
                                           'getbestblockhash',
                                           'getblock',
                                           'getblockhash',
                                           'getrawmempool',
                                           'getrawtransaction',
                                           'decoderawtransaction'
                                       ], state='readonly', width=25)
        self.command_combo.pack(side='left', padx=5)
        
        ttk.Label(command_frame, text="Arguments:", style='Header.TLabel').pack(side='left', padx=5)
        self.command_args_var = tk.StringVar()
        self.command_args_entry = ttk.Entry(command_frame, textvariable=self.command_args_var, width=30)
        self.command_args_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Button(command_frame, text="Execute", command=self.execute_console_command,
                 style='Modern.TButton').pack(side='left', padx=5)
        
        # Console output
        output_frame = ttk.LabelFrame(console_frame, text="📋 Output", style='Modern.TLabelframe')
        output_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.console_output = scrolledtext.ScrolledText(output_frame, height=20, 
                                                bg='#1e1e1e', fg='#00ff00', 
                                                font=('Consolas', 9))
        self.console_output.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(settings_frame, text='⚙️ Settings')
        
        # Title
        title_label = ttk.Label(settings_frame, text="⚙️ Settings", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Settings form
        form_frame = ttk.Frame(settings_frame, style='Modern.TFrame')
        form_frame.pack(fill='x', padx=20, pady=10)
        
        # Network settings
        network_frame = ttk.LabelFrame(form_frame, text="🌐 Network Settings", style='Modern.TLabelframe')
        network_frame.pack(fill='x', pady=10)
        
        # Port
        port_frame = ttk.Frame(network_frame, style='Modern.TFrame')
        port_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(port_frame, text="P2P Port:", style='Header.TLabel').pack(side='left', padx=5)
        self.p2p_port_var = tk.StringVar(value="8333")
        self.p2p_port_entry = ttk.Entry(port_frame, textvariable=self.p2p_port_var, width=10)
        self.p2p_port_entry.pack(side='left', padx=5)
        
        ttk.Label(port_frame, text="RPC Port:", style='Header.TLabel').pack(side='left', padx=5)
        self.rpc_port_var = tk.StringVar(value="8332")
        self.rpc_port_entry = ttk.Entry(port_frame, textvariable=self.rpc_port_var, width=10)
        self.rpc_port_entry.pack(side='left', padx=5)
        
        # Mining settings
        mining_frame = ttk.LabelFrame(form_frame, text="⛏️ Mining Settings", style='Modern.TLabelframe')
        mining_frame.pack(fill='x', pady=10)
        
        # Difficulty
        diff_frame = ttk.Frame(mining_frame, style='Modern.TFrame')
        diff_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(diff_frame, text="Difficulty:", style='Header.TLabel').pack(side='left', padx=5)
        self.difficulty_var = tk.StringVar(value="4")
        self.difficulty_entry = ttk.Entry(diff_frame, textvariable=self.difficulty_var, width=10)
        self.difficulty_entry.pack(side='left', padx=5)
        
        # Mining threads
        threads_frame = ttk.Frame(mining_frame, style='Modern.TFrame')
        threads_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(threads_frame, text="Mining Threads:", style='Header.TLabel').pack(side='left', padx=5)
        self.mining_threads_var = tk.StringVar(value="1")
        self.threads_spinbox = ttk.Spinbox(threads_frame, from_=1, to=8, 
                                          textvariable=self.mining_threads_var, width=10)
        self.threads_spinbox.pack(side='left', padx=5)
        
        # Apply button
        button_frame = ttk.Frame(settings_frame, style='Modern.TFrame')
        button_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Button(button_frame, text="Apply Settings", command=self.apply_settings,
                 style='Modern.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_settings,
                 style='Modern.TButton').pack(side='left', padx=5)
    
    def initialize_blockchain(self):
        """Initialize blockchain components in background"""
        def init_components():
            try:
                from blockchain_improved import GSCBlockchain
                from network_improved import GSCNetworkNode
                from wallet_manager import WalletManager
                
                self.blockchain = GSCBlockchain()
                self.network_node = GSCNetworkNode(self.blockchain)
                self.wallet_manager = WalletManager()
                
                # Update UI in main thread
                self.root.after(0, self.on_blockchain_initialized)
                
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Failed to initialize: {e}"))
        
        threading.Thread(target=init_components, daemon=True).start()
    
    def on_blockchain_initialized(self):
        """Called when blockchain is initialized"""
        self.update_dashboard()
        self.refresh_wallet()
        self.log_message("✅ GSC Blockchain initialized successfully")
    
    def update_dashboard(self):
        """Update dashboard with current information"""
        if not self.blockchain:
            return
        
        try:
            # Update blockchain info
            self.block_count_label.config(text=f"Blocks: {len(self.blockchain.chain)}")
            self.difficulty_label.config(text=f"Difficulty: {self.blockchain.difficulty}")
            
            latest = self.blockchain.get_latest_block()
            if latest:
                self.best_hash_label.config(text=f"Best Hash: {latest.hash[:16]}...")
            
            # Update network info
            if self.network_node:
                peers = len(self.network_node.peers) if hasattr(self.network_node, 'peers') else 0
                self.peers_label.config(text=f"Connected Peers: {peers}")
                self.status_label.config(text="Status: Running")
            
            # Update mining info
            mining_status = "Mining" if self.is_mining else "Stopped"
            self.mining_status_label.config(text=f"Mining: {mining_status}")
            
            # Update recent blocks
            self.update_recent_blocks()
            
        except Exception as e:
            self.log_message(f"Error updating dashboard: {e}")
        
        # Schedule next update
        self.root.after(5000, self.update_dashboard)
    
    def update_recent_blocks(self):
        """Update recent blocks display"""
        if not self.blockchain:
            return
        
        try:
            self.recent_blocks_text.delete(1.0, tk.END)
            
            # Show last 10 blocks
            recent_blocks = self.blockchain.chain[-10:]
            for block in reversed(recent_blocks):
                timestamp = datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')
                block_info = f"Block #{block.index}\n"
                block_info += f"Hash: {block.hash[:16]}...\n"
                block_info += f"Time: {timestamp}\n"
                block_info += f"TXs: {len(block.transactions)}\n"
                block_info += "-" * 40 + "\n"
                
                self.recent_blocks_text.insert(tk.END, block_info)
                
        except Exception as e:
            self.log_message(f"Error updating recent blocks: {e}")
    
    def execute_console_command(self):
        """Execute selected console command"""
        command = self.command_var.get()
        args = self.command_args_var.get().split() if self.command_args_var.get() else []
        
        if not command:
            return
        
        try:
            # Import console function
            from gsc_simple_console import run_command
            
            # Execute command and capture output
            import io
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            run_command(command, args)
            
            sys.stdout = old_stdout
            output = captured_output.getvalue()
            
            # Display output
            self.console_output.insert(tk.END, f"\n> {command} {' '.join(args)}\n")
            self.console_output.insert(tk.END, output)
            self.console_output.insert(tk.END, "\n" + "="*50 + "\n")
            self.console_output.see(tk.END)
            
        except Exception as e:
            self.console_output.insert(tk.END, f"\n❌ Error: {e}\n")
            self.console_output.see(tk.END)
    
    def log_message(self, message):
        """Log message to mining log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        if hasattr(self, 'mining_log'):
            self.mining_log.insert(tk.END, log_entry)
            self.mining_log.see(tk.END)
    
    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
    
    def show_success(self, message):
        """Show success message"""
        messagebox.showinfo("Success", message)
    
    # Placeholder methods for wallet operations
    def create_wallet(self):
        """Create new wallet"""
        self.show_success("Wallet creation feature coming soon!")
    
    def load_wallet(self):
        """Load existing wallet"""
        self.show_success("Wallet loading feature coming soon!")
    
    def generate_address(self):
        """Generate new address"""
        self.show_success("Address generation feature coming soon!")
    
    def refresh_wallet(self):
        """Refresh wallet information"""
        if self.wallet_manager and self.wallet_manager.current_wallet:
            addresses = self.wallet_manager.get_receiving_addresses()
            
            # Update address lists
            self.address_listbox.delete(0, tk.END)
            self.receive_address_listbox.delete(0, tk.END)
            
            for addr in addresses:
                self.address_listbox.insert(tk.END, addr)
                self.receive_address_listbox.insert(tk.END, addr)
            
            # Update comboboxes
            self.from_address_combo['values'] = addresses
            self.mining_address_combo['values'] = addresses
            
            if addresses:
                self.receive_address_var.set(addresses[0])
    
    def send_transaction(self):
        """Send transaction"""
        self.show_success("Transaction sending feature coming soon!")
    
    def copy_address(self):
        """Copy address to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.receive_address_var.get())
        self.show_success("Address copied to clipboard!")
    
    def start_mining(self):
        """Start mining"""
        self.show_success("Mining start feature coming soon!")
    
    def stop_mining(self):
        """Stop mining"""
        self.show_success("Mining stop feature coming soon!")
    
    def generate_single_block(self):
        """Generate single block"""
        self.show_success("Block generation feature coming soon!")
    
    def connect_to_peer(self):
        """Connect to peer"""
        self.show_success("Peer connection feature coming soon!")
    
    def refresh_peers(self):
        """Refresh peer list"""
        self.show_success("Peer refresh feature coming soon!")
    
    def disconnect_peer(self):
        """Disconnect peer"""
        self.show_success("Peer disconnect feature coming soon!")
    
    def ban_peer(self):
        """Ban peer"""
        self.show_success("Peer banning feature coming soon!")
    
    def apply_settings(self):
        """Apply settings"""
        self.show_success("Settings applied successfully!")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        self.p2p_port_var.set("8333")
        self.rpc_port_var.set("8332")
        self.difficulty_var.set("4")
        self.mining_threads_var.set("1")
        self.show_success("Settings reset to defaults!")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

def main():
    """Main entry point"""
    app = GSCWalletGUI()
    app.run()

if __name__ == "__main__":
    main()
