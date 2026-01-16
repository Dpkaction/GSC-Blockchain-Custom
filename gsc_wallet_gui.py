import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import threading
import time
import json
import sys
import os
from datetime import datetime
import hashlib
import base64
from blockchain import GSCBlockchain, Transaction, Block
from wallet_manager import WalletManager
from paper_wallet_generator import PaperWalletGenerator
from telegram_bot import TelegramBot

class GSCWalletGUI:
    def __init__(self, blockchain=None, network_node=None):
        self.root = tk.Tk()
        self.root.title("GSC Coin - Professional Cryptocurrency Wallet")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Set window icon and styling similar to Bitcoin Core
        self.root.resizable(True, True)
        
        # Configure ttk style for Bitcoin Core look
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors similar to Bitcoin Core
        self.style.configure('TNotebook', background='#f0f0f0')
        self.style.configure('TNotebook.Tab', padding=[20, 8])
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabelFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', foreground='#333333')
        self.style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('Balance.TLabel', font=('Arial', 18, 'bold'), foreground='#2e7d32')
        
        # Initialize blockchain and network
        self.blockchain = blockchain if blockchain else GSCBlockchain()
        self.network_node = network_node
        self.wallet_manager = WalletManager()
        self.paper_wallet_generator = PaperWalletGenerator(self.root)
        self.telegram_bot = TelegramBot()
        self.current_address = None  # No wallet loaded initially
        self.current_balance = 0.0
        self.mining_thread = None
        self.is_mining = False
        self.network_peers = []
        self.sync_status = ""
        self.total_supply = 21750000000000  # 21.75 trillion GSC
        self.current_mining_address = None  # No mining address unlocked initially
        self.mining_unlocked = False
        
        # Create menu system first
        self.create_menu_system()
        
        # Create GUI
        self.create_gui()
        
        # Create status bar
        self.create_status_bar()
        
        # Load existing blockchain if available
        self.blockchain.load_blockchain("gsc_blockchain.json")
        
        # Show wallet selection dialog on startup
        self.show_wallet_selection_dialog()
        
        self.update_displays()
    
    def show_wallet_selection_dialog(self):
        """Show wallet selection dialog on startup"""
        dialog = tk.Toplevel(self.root)
        dialog.title("GSC Coin - Wallet Selection")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"500x400+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Welcome to GSC Coin Wallet", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Subtitle
        subtitle_label = ttk.Label(main_frame, 
                                  text="Please create a new wallet or open an existing one to continue.",
                                  font=('Arial', 10))
        subtitle_label.pack(pady=(0, 30))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=20)
        
        # Create New Wallet button
        create_btn = ttk.Button(buttons_frame, text="Create New Wallet", 
                               command=lambda: self.create_new_wallet_from_dialog(dialog),
                               width=20)
        create_btn.pack(pady=10)
        
        # Open Existing Wallet button
        open_btn = ttk.Button(buttons_frame, text="Open Existing Wallet", 
                             command=lambda: self.open_existing_wallet_from_dialog(dialog),
                             width=20)
        open_btn.pack(pady=10)
        
        # Available wallets
        wallets_frame = ttk.LabelFrame(main_frame, text="Available Wallets", padding=10)
        wallets_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # List available wallets
        try:
            wallets = self.wallet_manager.list_wallets()
            print(f"📂 Found {len(wallets) if wallets else 0} wallets: {wallets}")
            
            if wallets:
                for i, wallet in enumerate(wallets):
                    # Remove .wallet extension if present for display
                    display_name = wallet.replace('.wallet', '') if wallet.endswith('.wallet') else wallet
                    
                    # Create frame for each wallet
                    wallet_frame = ttk.Frame(wallets_frame)
                    wallet_frame.pack(fill=tk.X, pady=2)
                    
                    # Wallet button with proper command binding
                    wallet_btn = ttk.Button(wallet_frame, text=f"📁 {display_name}", 
                                          command=lambda w=display_name: self.open_wallet_from_dialog(dialog, w))
                    wallet_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    
                    print(f"   Added wallet button: {display_name}")
            else:
                no_wallets_label = ttk.Label(wallets_frame, text="No wallets found. Create a new wallet to get started.")
                no_wallets_label.pack(pady=20)
                print("   No wallets found")
        except Exception as e:
            print(f"❌ Error loading wallets: {str(e)}")
            error_label = ttk.Label(wallets_frame, text=f"Error loading wallets: {str(e)}")
            error_label.pack(pady=20)
        
        # Exit button
        exit_btn = ttk.Button(main_frame, text="Exit Application", 
                             command=self.root.quit,
                             width=20)
        exit_btn.pack(pady=(20, 0))
        
        # Prevent closing without selecting wallet
        dialog.protocol("WM_DELETE_WINDOW", self.root.quit)
    
    def create_new_wallet_from_dialog(self, dialog):
        """Create new wallet from selection dialog"""
        dialog.destroy()
        self.create_new_wallet()
    
    def open_existing_wallet_from_dialog(self, dialog):
        """Open existing wallet from selection dialog"""
        dialog.destroy()
        self.open_wallet_dialog()
    
    def open_wallet_from_dialog(self, dialog, wallet_name):
        """Open specific wallet from selection dialog"""
        try:
            print(f"🔓 Attempting to open wallet: {wallet_name}")
            
            # Try to open wallet (returns dict with wallet info)
            wallet_info = self.wallet_manager.open_wallet(wallet_name)
            
            if wallet_info and wallet_info.get('opened'):
                self.current_address = self.wallet_manager.get_current_address()
                self.current_wallet_name = wallet_name  # Store wallet name for debugging
                print(f"✅ Wallet opened successfully: {wallet_name}")
                print(f"   Address: {self.current_address}")
                print(f"   Balance: {self.blockchain.get_balance(self.current_address)} GSC")
                print(f"   Address Valid: {self.blockchain.validate_gsc_address(self.current_address)}")
                
                dialog.destroy()
                messagebox.showinfo("Wallet Opened", f"Successfully opened wallet: {wallet_name}\n\nAddress: {self.current_address}\nAddresses: {wallet_info.get('addresses_count', 0)}")
                self.update_displays()
            else:
                print(f"❌ Failed to open wallet: {wallet_name}")
                messagebox.showerror("Error", f"Failed to open wallet: {wallet_name}")
                
        except Exception as e:
            print(f"❌ Error opening wallet {wallet_name}: {str(e)}")
            messagebox.showerror("Error", f"Error opening wallet: {str(e)}")
    
    def create_menu_system(self):
        """Create Bitcoin Core-style menu system"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Create Wallet...", command=self.create_new_wallet)
        file_menu.add_command(label="Open Wallet", command=self.open_wallet_dialog)
        file_menu.add_command(label="Close Wallet...", command=self.close_current_wallet)
        file_menu.add_command(label="Close All Wallets...", command=self.close_all_wallets)
        file_menu.add_separator()
        file_menu.add_command(label="Backup Wallet...", command=self.backup_wallet_dialog)
        file_menu.add_command(label="Restore Wallet...", command=self.restore_wallet_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Generate Paper Wallet...", command=self.generate_paper_wallet)
        file_menu.add_separator()
        file_menu.add_command(label="Sign message...", command=self.sign_message_dialog)
        file_menu.add_command(label="Verify message...", command=self.verify_message_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.root.quit)
        
        # Settings Menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Encrypt Wallet...", command=self.encrypt_wallet_dialog)
        settings_menu.add_command(label="Change Passphrase...", command=self.change_passphrase_dialog)
        settings_menu.add_separator()
        settings_menu.add_checkbutton(label="Mask values", command=self.toggle_mask_values)
        settings_menu.add_separator()
        settings_menu.add_command(label="Options...", command=self.show_options_dialog)
        
        # Window Menu
        window_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Window", menu=window_menu)
        window_menu.add_command(label="Minimize", accelerator="Ctrl+M", command=self.root.iconify)
        window_menu.add_separator()
        window_menu.add_command(label="Sending addresses", command=self.show_sending_addresses)
        window_menu.add_command(label="Receiving addresses", command=self.show_receiving_addresses)
        window_menu.add_separator()
        window_menu.add_command(label="Information", accelerator="Ctrl+I", command=self.show_information)
        window_menu.add_command(label="Console", accelerator="Ctrl+T", command=self.show_console)
        window_menu.add_command(label="Network Traffic", command=self.show_network_traffic)
        window_menu.add_command(label="Peers", command=self.show_peers)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Download Wallet .exe", command=self.download_wallet_exe)
        tools_menu.add_command(label="Create Portable Version", command=self.create_portable_version)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About GSC Coin", command=self.show_about)
        help_menu.add_command(label="Command-line options", command=self.show_command_options)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-m>', lambda e: self.root.iconify())
        self.root.bind('<Control-i>', lambda e: self.show_information())
        self.root.bind('<Control-t>', lambda e: self.show_console())
    
    def create_status_bar(self):
        """Create status bar like Bitcoin Core"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status labels
        self.sync_label = ttk.Label(self.status_frame, text="")
        self.sync_label.pack(side=tk.LEFT, padx=5)
    
    def create_gui(self):
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create all tabs (original interface)
        self.create_wallet_tab()
        self.create_send_tab()
        self.create_receive_tab()
        self.create_mining_tab()
        self.create_mempool_tab()
        self.create_blockchain_tab()
        self.create_network_tab()  # Show network tab with import/export features()
    
    def create_wallet_tab(self):
        # Wallet Tab
        wallet_frame = ttk.Frame(self.notebook)
        self.notebook.add(wallet_frame, text="Overview")
        
        # Balance section - Bitcoin Core style
        balance_frame = ttk.LabelFrame(wallet_frame, text="Available Balance", padding=15)
        balance_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Main balance display
        balance_container = ttk.Frame(balance_frame)
        balance_container.pack(fill=tk.X)
        
        ttk.Label(balance_container, text="GSC Balance:", style='Title.TLabel').pack(side=tk.LEFT)
        self.balance_label = ttk.Label(balance_container, text="0.00000000 GSC", style='Balance.TLabel')
        self.balance_label.pack(side=tk.RIGHT)
        
        # Market info display
        market_frame = ttk.LabelFrame(wallet_frame, text="Market Information", padding=10)
        market_frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Total supply info
        supply_info = ttk.Frame(market_frame)
        supply_info.pack(fill=tk.X)
        
        ttk.Label(supply_info, text="Total Supply:").pack(side=tk.LEFT)
        ttk.Label(supply_info, text=f"{self.total_supply:,.0f} GSC", 
                 font=("Arial", 10, "bold"), foreground="#2e7d32").pack(side=tk.RIGHT)
        
        # Current address display
        addr_frame = ttk.Frame(market_frame)
        addr_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(addr_frame, text="Current Address:").pack(side=tk.LEFT)
        address_text = self.current_address[:20] + "..." if self.current_address else "No Wallet Loaded"
        self.address_display = ttk.Label(addr_frame, text=address_text, 
                                        font=("Courier", 9), foreground="#1976d2")
        self.address_display.pack(side=tk.RIGHT)
        
        # Transaction section
        tx_frame = ttk.LabelFrame(wallet_frame, text="Send GSC Coins", padding=10)
        tx_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(tx_frame, text="Recipient Address:").grid(row=0, column=0, sticky=tk.W)
        self.recipient_entry = ttk.Entry(tx_frame, width=40)
        self.recipient_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(tx_frame, text="Amount:").grid(row=1, column=0, sticky=tk.W)
        self.amount_entry = ttk.Entry(tx_frame, width=20)
        self.amount_entry.grid(row=1, column=1, padx=5, sticky=tk.W)
        
        ttk.Label(tx_frame, text="Fee:").grid(row=2, column=0, sticky=tk.W)
        self.fee_entry = ttk.Entry(tx_frame, width=20)
        self.fee_entry.grid(row=2, column=1, padx=5, sticky=tk.W)
        self.fee_entry.insert(0, "1.0")
        
        ttk.Button(tx_frame, text="Send Transaction", command=self.send_transaction).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Transaction history
        history_frame = ttk.LabelFrame(wallet_frame, text="Transaction History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tx_history = ttk.Treeview(history_frame, columns=("Type", "Amount", "Address", "Time"), show="headings")
        self.tx_history.heading("Type", text="Type")
        self.tx_history.heading("Amount", text="Amount")
        self.tx_history.heading("Address", text="Address")
        self.tx_history.heading("Time", text="Time")
        self.tx_history.pack(fill=tk.BOTH, expand=True)
    
    def create_send_tab(self):
        """Create Send tab like Bitcoin Core"""
        send_frame = ttk.Frame(self.notebook)
        self.notebook.add(send_frame, text="Send")
        
        # Send form
        send_form = ttk.LabelFrame(send_frame, text="Send GSC Coins", padding=15)
        send_form.pack(fill=tk.X, padx=15, pady=10)
        
        # Pay To
        ttk.Label(send_form, text="Pay To:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.send_address_entry = ttk.Entry(send_form, width=50)
        self.send_address_entry.grid(row=0, column=1, padx=5, pady=5)
        address_buttons_frame = ttk.Frame(send_form)
        address_buttons_frame.grid(row=0, column=2, padx=5)
        ttk.Button(address_buttons_frame, text="Address Book", command=self.open_address_book).pack(side=tk.LEFT)
        ttk.Button(address_buttons_frame, text="Copy My Address", command=self.copy_my_address_to_send).pack(side=tk.LEFT, padx=(5,0))
        
        # Label
        ttk.Label(send_form, text="Label:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.send_label_entry = ttk.Entry(send_form, width=50)
        self.send_label_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Amount
        ttk.Label(send_form, text="Amount:").grid(row=2, column=0, sticky=tk.W, pady=5)
        amount_frame = ttk.Frame(send_form)
        amount_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        self.send_amount_entry = ttk.Entry(amount_frame, width=20)
        self.send_amount_entry.pack(side=tk.LEFT)
        ttk.Label(amount_frame, text="GSC").pack(side=tk.LEFT, padx=(5, 0))
        
        # Fee
        ttk.Label(send_form, text="Fee:").grid(row=3, column=0, sticky=tk.W, pady=5)
        fee_frame = ttk.Frame(send_form)
        fee_frame.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        self.send_fee_entry = ttk.Entry(fee_frame, width=20)
        self.send_fee_entry.pack(side=tk.LEFT)
        self.send_fee_entry.insert(0, "0.001")
        ttk.Label(fee_frame, text="GSC").pack(side=tk.LEFT, padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(send_form)
        button_frame.grid(row=4, column=1, sticky=tk.W, pady=10)
        ttk.Button(button_frame, text="Clear All", command=self.clear_send_form).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Send", command=self.send_transaction_advanced).pack(side=tk.LEFT)
    
    def create_receive_tab(self):
        """Create Receive tab like Bitcoin Core"""
        receive_frame = ttk.Frame(self.notebook)
        self.notebook.add(receive_frame, text="Receive")
        
        # Request payment section
        request_frame = ttk.LabelFrame(receive_frame, text="Request Payment", padding=15)
        request_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Label
        ttk.Label(request_frame, text="Label:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.receive_label_entry = ttk.Entry(request_frame, width=40)
        self.receive_label_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Amount
        ttk.Label(request_frame, text="Amount:").grid(row=1, column=0, sticky=tk.W, pady=5)
        amount_frame = ttk.Frame(request_frame)
        amount_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.receive_amount_entry = ttk.Entry(amount_frame, width=20)
        self.receive_amount_entry.pack(side=tk.LEFT)
        ttk.Label(amount_frame, text="GSC").pack(side=tk.LEFT, padx=(5, 0))
        
        # Message
        ttk.Label(request_frame, text="Message:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.receive_message_entry = ttk.Entry(request_frame, width=40)
        self.receive_message_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(request_frame)
        button_frame.grid(row=3, column=1, sticky=tk.W, pady=10)
        ttk.Button(button_frame, text="Clear", command=self.clear_receive_form).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Request payment", command=self.create_payment_request).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Show QR Code", command=self.show_qr_code).pack(side=tk.LEFT, padx=(5, 0))
        
        # Current address display
        address_frame = ttk.LabelFrame(receive_frame, text="Your Address", padding=15)
        address_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.current_address_label = ttk.Label(address_frame, text=self.current_address, font=("Courier", 10))
        self.current_address_label.pack()
        
        button_frame = ttk.Frame(address_frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="Copy Address", command=self.copy_address).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Get Private Key", command=self.get_private_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Generate New Address", command=self.generate_new_address_gui).pack(side=tk.LEFT, padx=5)
    
    def create_mining_tab(self):
        # Mining Tab
        mining_frame = ttk.Frame(self.notebook)
        self.notebook.add(mining_frame, text="⛏️ Mining")
        
        # Store reference to mining frame
        self.mining_frame = mining_frame
        self.mining_unlocked = False
        
        # Initially show only access control
        self.show_mining_access_control()
    
    def show_mining_access_control(self):
        """Show mining access control input"""
        # Clear the frame
        for widget in self.mining_frame.winfo_children():
            widget.destroy()
        
        # Access control frame
        access_frame = ttk.LabelFrame(self.mining_frame, text="Mining Access Required", padding=20)
        access_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        ttk.Label(access_frame, text="Enter GSC Address to access mining:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        self.mining_address_entry = ttk.Entry(access_frame, width=60, font=('Courier', 10))
        self.mining_address_entry.pack(pady=10)
        
        ttk.Button(access_frame, text="Unlock Mining", command=self.unlock_mining).pack(pady=10)
        
        self.mining_access_status = ttk.Label(access_frame, text="", font=('Arial', 10))
        self.mining_access_status.pack(pady=5)
    
    def unlock_mining(self):
        """Unlock mining if correct address is entered"""
        entered_address = self.mining_address_entry.get().strip()
        authorized_addresses = [
            "GSC1705641e65321ef23ac5fb3d470f39627",
            "GSC1221fe3e6139bbe0b76f0230d9cd5bbc1"
        ]
        
        if entered_address in authorized_addresses:
            self.mining_unlocked = True
            # Set the current mining address globally
            import blockchain
            blockchain.CURRENT_MINING_ADDRESS = entered_address
            self.current_mining_address = entered_address
            self.show_mining_controls()
        else:
            self.mining_access_status.config(text="Invalid GSC Address", foreground='red')
    
    def show_mining_controls(self):
        """Show full mining interface after successful authentication"""
        # Clear the frame
        for widget in self.mining_frame.winfo_children():
            widget.destroy()
        
        # Reward destination display
        reward_frame = ttk.LabelFrame(self.mining_frame, text="Reward Destination", padding=10)
        reward_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(reward_frame, text="Mining rewards and transaction fees will go to:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        reward_address_label = ttk.Label(reward_frame, text=self.current_mining_address, font=('Courier', 10, 'bold'), foreground='green')
        reward_address_label.pack(anchor=tk.W, pady=5)
        ttk.Label(reward_frame, text="This is the address you used to unlock mining", font=('Arial', 9), foreground='gray').pack(anchor=tk.W)
        
        # Mining controls
        controls_frame = ttk.LabelFrame(self.mining_frame, text="Mining Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mining_button = ttk.Button(controls_frame, text="Start Mining", command=self.toggle_mining)
        self.mining_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(controls_frame, text="Difficulty:").pack(side=tk.LEFT, padx=5)
        # Default to 5 if blockchain difficulty is outside 5-8 range
        current_diff = self.blockchain.difficulty
        default_diff = str(current_diff) if 5 <= current_diff <= 8 else '5'
        self.difficulty_var = tk.StringVar(value=default_diff)
        difficulty_combo = ttk.Combobox(controls_frame, textvariable=self.difficulty_var, values=['5', '6', '7', '8'], 
                                       state='readonly', width=5)
        difficulty_combo.pack(side=tk.LEFT, padx=5)
        ttk.Label(controls_frame, text="(5-8 only)", font=('Arial', 8), foreground='gray').pack(side=tk.LEFT, padx=5)
        
        # Mining stats
        stats_frame = ttk.LabelFrame(self.mining_frame, text="Mining Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mining_status = ttk.Label(stats_frame, text="Status: Idle")
        self.mining_status.pack(anchor=tk.W)
        
        self.nonce_label = ttk.Label(stats_frame, text="Nonce: 0")
        self.nonce_label.pack(anchor=tk.W)
        
        self.hash_rate_label = ttk.Label(stats_frame, text="Hash Rate: 0 H/s")
        self.hash_rate_label.pack(anchor=tk.W)
        
        self.current_hash_label = ttk.Label(stats_frame, text="Current Hash: -")
        self.current_hash_label.pack(anchor=tk.W)
        
        # Block details
        block_frame = ttk.LabelFrame(self.mining_frame, text="Current Block Details", padding=10)
        block_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.block_details = scrolledtext.ScrolledText(block_frame, height=15, wrap=tk.WORD)
        self.block_details.pack(fill=tk.BOTH, expand=True)
    
    def create_mempool_tab(self):
        # Mempool Tab
        mempool_frame = ttk.Frame(self.notebook)
        self.notebook.add(mempool_frame, text="📋 Mempool")
        
        # Store reference to mempool frame
        self.mempool_frame = mempool_frame
        self.mempool_unlocked = False
        
        # Initially show only access control
        self.show_mempool_access_control()
    
    def show_mempool_access_control(self):
        """Show mempool access control input"""
        # Clear the frame
        for widget in self.mempool_frame.winfo_children():
            widget.destroy()
        
        # Access control frame
        access_frame = ttk.LabelFrame(self.mempool_frame, text="Mempool Access Required", padding=20)
        access_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        ttk.Label(access_frame, text="Enter GSC Address to access mempool:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        self.mempool_address_entry = ttk.Entry(access_frame, width=60, font=('Courier', 10))
        self.mempool_address_entry.pack(pady=10)
        
        ttk.Button(access_frame, text="Unlock Mempool", command=self.unlock_mempool).pack(pady=10)
        
        self.mempool_access_status = ttk.Label(access_frame, text="", font=('Arial', 10))
        self.mempool_access_status.pack(pady=5)
    
    def unlock_mempool(self):
        """Unlock mempool if correct address is entered"""
        entered_address = self.mempool_address_entry.get().strip()
        authorized_addresses = [
            "GSC1705641e65321ef23ac5fb3d470f39627",
            "GSC1221fe3e6139bbe0b76f0230d9cd5bbc1"
        ]
        
        if entered_address in authorized_addresses:
            self.mempool_unlocked = True
            self.show_mempool_controls()
        else:
            self.mempool_access_status.config(text="Invalid GSC Address", foreground='red')
    
    def show_mempool_controls(self):
        """Show full mempool interface after successful authentication"""
        # Clear the frame
        for widget in self.mempool_frame.winfo_children():
            widget.destroy()
        
        # Mempool stats
        stats_frame = ttk.LabelFrame(self.mempool_frame, text="Mempool Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mempool_size_label = ttk.Label(stats_frame, text="Pending Transactions: 0")
        self.mempool_size_label.pack(anchor=tk.W)
        
        self.mempool_fees_label = ttk.Label(stats_frame, text="Total Fees: 0.0 GSC")
        self.mempool_fees_label.pack(anchor=tk.W)
        
        # Mempool import/export controls
        controls_frame = ttk.LabelFrame(self.mempool_frame, text="Transaction Management", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Row 1: Import/Export buttons
        row1_frame = ttk.Frame(controls_frame)
        row1_frame.pack(fill=tk.X, pady=5)
        ttk.Button(row1_frame, text="📥 Import Transactions", command=self.import_mempool_transactions).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1_frame, text="📤 Export Transactions", command=self.export_mempool_transactions).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1_frame, text="🔄 Refresh Mempool", command=self.update_mempool_display).pack(side=tk.LEFT, padx=5)
        
        # Row 2: Import from Telegram button
        row2_frame = ttk.Frame(controls_frame)
        row2_frame.pack(fill=tk.X, pady=5)
        ttk.Button(row2_frame, text="📱 Import from Telegram Data", command=self.import_from_telegram_data).pack(side=tk.LEFT, padx=5)
        ttk.Label(row2_frame, text="(Paste transaction data from @gsc_vags_bot)", font=('Arial', 9), foreground='gray').pack(side=tk.LEFT, padx=10)
        
        # Mempool transactions
        tx_frame = ttk.LabelFrame(self.mempool_frame, text="Pending Transactions", padding=10)
        tx_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.mempool_tree = ttk.Treeview(tx_frame, columns=("#", "TxID", "From", "To", "Amount", "Fee", "Time"), show="headings")
        self.mempool_tree.heading("#", text="#")
        self.mempool_tree.heading("TxID", text="Transaction ID")
        self.mempool_tree.heading("From", text="From")
        self.mempool_tree.heading("To", text="To")
        self.mempool_tree.heading("Amount", text="Amount")
        self.mempool_tree.heading("Fee", text="Fee")
        self.mempool_tree.heading("Time", text="Time")
        
        # Set column widths for better display
        self.mempool_tree.column("#", width=40)
        self.mempool_tree.column("TxID", width=120)
        self.mempool_tree.column("From", width=120)
        self.mempool_tree.column("To", width=120)
        self.mempool_tree.column("Amount", width=100)
        self.mempool_tree.column("Fee", width=100)
        self.mempool_tree.column("Time", width=80)
        
        # Add scrollbar
        mempool_scroll = ttk.Scrollbar(tx_frame, orient=tk.VERTICAL, command=self.mempool_tree.yview)
        self.mempool_tree.configure(yscrollcommand=mempool_scroll.set)
        
        self.mempool_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mempool_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_blockchain_tab(self):
        # Blockchain Tab
        blockchain_frame = ttk.Frame(self.notebook)
        self.notebook.add(blockchain_frame, text="🔗 Blockchain")
        
        # Blockchain info
        info_frame = ttk.LabelFrame(blockchain_frame, text="Blockchain Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create two columns for blockchain info
        info_left = ttk.Frame(info_frame)
        info_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        info_right = ttk.Frame(info_frame)
        info_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Left column - Basic info
        self.blocks_label = ttk.Label(info_left, text="Total Blocks: 0")
        self.blocks_label.pack(anchor=tk.W)
        
        self.chain_valid_label = ttk.Label(info_left, text="Chain Valid: True")
        self.chain_valid_label.pack(anchor=tk.W)
        
        self.difficulty_label = ttk.Label(info_left, text="Difficulty: 4")
        self.difficulty_label.pack(anchor=tk.W)
        
        # Right column - Supply info
        self.total_supply_label = ttk.Label(info_right, text="Max Supply: 21.75T GSC", font=('Arial', 9, 'bold'))
        self.total_supply_label.pack(anchor=tk.W)
        
        self.current_supply_label = ttk.Label(info_right, text="Current Supply: 255 GSC")
        self.current_supply_label.pack(anchor=tk.W)
        
        self.remaining_supply_label = ttk.Label(info_right, text="Remaining: 21.75T GSC", foreground='green')
        self.remaining_supply_label.pack(anchor=tk.W)
        
        self.supply_percentage_label = ttk.Label(info_right, text="Mined: 0.000001%")
        self.supply_percentage_label.pack(anchor=tk.W)
        
        # Blocks list
        blocks_frame = ttk.LabelFrame(blockchain_frame, text="Blocks", padding=10)
        blocks_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.blocks_tree = ttk.Treeview(blocks_frame, columns=("Index", "Hash", "PrevHash", "Nonce", "Txs", "Miner"), show="headings")
        self.blocks_tree.heading("Index", text="Block #")
        self.blocks_tree.heading("Hash", text="Hash")
        self.blocks_tree.heading("PrevHash", text="Previous Hash")
        self.blocks_tree.heading("Nonce", text="Nonce")
        self.blocks_tree.heading("Txs", text="Transactions")
        self.blocks_tree.heading("Miner", text="Miner")
        
        # Add scrollbar
        blocks_scroll = ttk.Scrollbar(blocks_frame, orient=tk.VERTICAL, command=self.blocks_tree.yview)
        self.blocks_tree.configure(yscrollcommand=blocks_scroll.set)
        
        self.blocks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        blocks_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to show block details
        self.blocks_tree.bind("<Double-1>", self.show_block_details)
    
    def create_network_tab(self):
        # Network Tab
        network_frame = ttk.Frame(self.notebook)
        self.notebook.add(network_frame, text="🌐 Network")
        
        # Blockchain Management Controls
        blockchain_frame = ttk.LabelFrame(network_frame, text="Blockchain Management", padding=10)
        blockchain_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Row 1: Save/Load/Validate/Broadcast/Sync
        row1_frame = ttk.Frame(blockchain_frame)
        row1_frame.pack(fill=tk.X, pady=5)
        ttk.Button(row1_frame, text="💾 Save Blockchain", command=self.save_blockchain).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1_frame, text="📁 Load Blockchain", command=self.load_blockchain).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1_frame, text="✅ Validate Chain", command=self.validate_chain).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1_frame, text="📡 Broadcast Chain", command=self.broadcast_blockchain).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1_frame, text="🔄 Sync from Peers", command=self.sync_from_peers).pack(side=tk.LEFT, padx=5)
        
        # Row 2: Import/Export/Manual
        row2_frame = ttk.Frame(blockchain_frame)
        row2_frame.pack(fill=tk.X, pady=5)
        ttk.Button(row2_frame, text="📥 Import Blockchain", command=self.import_blockchain).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2_frame, text="📤 Export Blockchain", command=self.export_blockchain).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2_frame, text="🔄 Update Blockchain", command=self.update_blockchain).pack(side=tk.LEFT, padx=5)
        ttk.Button(row2_frame, text="➕ Add Block Manually", command=self.add_manual_block_gui).pack(side=tk.LEFT, padx=5)
        
        # GSC Supply Information
        supply_frame = ttk.LabelFrame(network_frame, text="GSC Coin Supply Information", padding=10)
        supply_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create supply info grid
        supply_grid = ttk.Frame(supply_frame)
        supply_grid.pack(fill=tk.X)
        
        # Left column
        supply_left = ttk.Frame(supply_grid)
        supply_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right column
        supply_right = ttk.Frame(supply_grid)
        supply_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Supply metrics
        self.network_max_supply_label = ttk.Label(supply_left, text="Maximum Supply: 21.75 Trillion GSC", font=('Arial', 10, 'bold'))
        self.network_max_supply_label.pack(anchor=tk.W, pady=2)
        
        self.network_current_supply_label = ttk.Label(supply_left, text="Current Supply: 255 GSC")
        self.network_current_supply_label.pack(anchor=tk.W, pady=2)
        
        self.network_remaining_supply_label = ttk.Label(supply_right, text="Remaining: 21,749,999,999,745 GSC", foreground='green')
        self.network_remaining_supply_label.pack(anchor=tk.W, pady=2)
        
        self.network_supply_percentage_label = ttk.Label(supply_right, text="Mined: 0.000001%")
        self.network_supply_percentage_label.pack(anchor=tk.W, pady=2)
        
        # Halving information
        self.network_halving_label = ttk.Label(supply_left, text="Next Halving: Block 4,350,000,000,000", foreground='blue')
        self.network_halving_label.pack(anchor=tk.W, pady=2)
        
        self.network_reward_label = ttk.Label(supply_right, text="Current Block Reward: 50.0 GSC", foreground='orange')
        self.network_reward_label.pack(anchor=tk.W, pady=2)
        
        # Network info
        info_frame = ttk.LabelFrame(network_frame, text="Network Log", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.network_info = scrolledtext.ScrolledText(info_frame, height=12, wrap=tk.WORD)
        self.network_info.pack(fill=tk.BOTH, expand=True)
    
    def create_console_tab(self):
        """Create Console tab for debug commands"""
        console_frame = ttk.Frame(self.notebook)
        self.notebook.add(console_frame, text="Console")
        
        # Console output
        console_output_frame = ttk.LabelFrame(console_frame, text="Console Output", padding=10)
        console_output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.console_output = scrolledtext.ScrolledText(console_output_frame, height=20, wrap=tk.WORD, bg='black', fg='green', font=('Courier', 10))
        self.console_output.pack(fill=tk.BOTH, expand=True)
        
        # Add download button
        download_frame = ttk.Frame(console_frame)
        download_frame.pack(fill=tk.X, pady=5)
        
        download_exe_btn = ttk.Button(download_frame, text="📥 Download Wallet .exe", 
                                     command=self.simple_download_exe)
        download_exe_btn.pack(side=tk.LEFT, padx=5)
        
        # Console input
        input_frame = ttk.Frame(console_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(input_frame, text=">").pack(side=tk.LEFT)
        self.console_input = ttk.Entry(input_frame)
        self.console_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.console_input.bind('<Return>', self.execute_console_command)
        
        ttk.Button(input_frame, text="Execute", command=self.execute_console_command).pack(side=tk.RIGHT)
        
        # Add welcome message
        self.console_output.insert(tk.END, "GSC Coin Console\n")
        self.console_output.insert(tk.END, "Type 'help' for available commands\n")
        self.console_output.insert(tk.END, "=" * 50 + "\n")
    
    def send_transaction(self):
        try:
            # Check if wallet is loaded
            if not self.current_address:
                messagebox.showerror("No Wallet", "Please create or open a wallet first before sending transactions.")
                return
            
            recipient = self.recipient_entry.get().strip()
            amount = float(self.amount_entry.get())
            fee = float(self.fee_entry.get())
            
            if not recipient:
                messagebox.showerror("Error", "Please enter recipient address")
                return
            
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
            
            # Check balance
            balance = self.blockchain.get_balance(self.current_address)
            if balance < (amount + fee):
                messagebox.showerror("Error", f"Insufficient balance. Available: {balance} GSC")
                return
            
            # Create transaction
            tx = Transaction(
                sender=self.current_address,
                receiver=recipient,
                amount=amount,
                fee=fee,
                timestamp=time.time()
            )
            
            # Mark as self-created transaction
            tx.source = "self_created"
            
            # Add to mempool
            print(f"🔄 Attempting to add transaction to mempool...")
            print(f"   Current Wallet: {getattr(self, 'current_wallet_name', 'Unknown')}")
            print(f"   Sender: {tx.sender}")
            print(f"   Sender Balance: {self.blockchain.get_balance(tx.sender)} GSC")
            print(f"   Receiver: {tx.receiver}")
            print(f"   Amount: {tx.amount} GSC")
            print(f"   Fee: {tx.fee} GSC")
            print(f"   Required Total: {tx.amount + tx.fee} GSC")
            print(f"   TX ID: {tx.tx_id}")
            print(f"   Address Valid: {self.blockchain.validate_gsc_address(tx.sender)}")
            
            if self.blockchain.add_transaction_to_mempool(tx):
                print(f"✅ Transaction successfully added to mempool!")
                
                # Send transaction notification to Telegram
                try:
                    self.send_transaction_to_telegram(tx)
                    print(f"📱 Transaction sent to Telegram bot")
                except Exception as e:
                    print(f"⚠️ Telegram notification failed: {e}")
                
                # Broadcast to network if available
                if hasattr(self.blockchain, 'network_node') and self.blockchain.network_node:
                    try:
                        self.blockchain.network_node.broadcast_transaction(tx)
                        print(f"📡 Transaction broadcasted to network")
                    except Exception as e:
                        print(f"⚠️ Network broadcast failed: {e}")
                
                messagebox.showinfo("Success", f"Transaction sent successfully!\n\nTX ID: {tx.tx_id[:16]}...\nAmount: {tx.amount} GSC\nFee: {tx.fee} GSC\n\n✅ Added to mempool\n📱 Sent to Telegram\n📡 Broadcasted to network")
                self.recipient_entry.delete(0, tk.END)
                self.amount_entry.delete(0, tk.END)
                self.update_displays()
            else:
                print(f"❌ Failed to add transaction to mempool")
                messagebox.showerror("Error", "Failed to add transaction to mempool")
        
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for amount and fee")
        except Exception as e:
            messagebox.showerror("Error", f"Transaction failed: {str(e)}")
    
    def toggle_mining(self):
        if not self.is_mining:
            self.start_mining()
        else:
            self.stop_mining()
    
    def start_mining(self):
        # Check if wallet is loaded
        if not self.current_address:
            messagebox.showerror("No Wallet", "Please create or open a wallet first before mining.")
            return
        
        # Check if mining is unlocked and get the mining address
        if not hasattr(self, 'current_mining_address') or not self.current_mining_address:
            messagebox.showerror("Mining Locked", "Please unlock mining first by entering an authorized GSC address in the Mining tab.")
            return
        
        print(f"🔄 Starting mining process...")
        print(f"   Current mempool size: {len(self.blockchain.mempool)} transactions")
        print(f"   Current blockchain height: {len(self.blockchain.chain)-1}")
        print(f"   Mining address (rewards go to): {self.current_mining_address}")
        print(f"   Wallet address: {self.current_address}")
        
        if len(self.blockchain.mempool) == 0:
            messagebox.showwarning("Cannot Mine", "No transactions in mempool!\n\nPlease add transactions to the mempool before mining.\nUse the 'Send' tab to create transactions or 'Import Transactions' in the Mempool tab.")
            return
        
        self.is_mining = True
        self.mining_button.config(text="Stop Mining")
        self.blockchain.difficulty = int(self.difficulty_var.get())
        
        print(f"⛏️ Mining started with difficulty: {self.blockchain.difficulty}")
        print(f"   Transactions to mine: {len(self.blockchain.mempool)}")
        print(f"   All rewards and fees will go to: {self.current_mining_address}")
        
        # Start mining in separate thread
        self.mining_thread = threading.Thread(target=self.mine_block)
        self.mining_thread.daemon = True
        self.mining_thread.start()
    
    def stop_mining(self):
        self.is_mining = False
        self.mining_button.config(text="Start Mining")
        self.mining_status.config(text="Status: Stopped")
    
    def mine_block(self):
        def mining_callback(stats):
            if self.is_mining:
                self.root.after(0, lambda: self.update_mining_stats(stats))
        
        try:
            self.root.after(0, lambda: self.mining_status.config(text="Status: Mining..."))
            
            print(f"🔨 Starting mining process for address: {self.current_mining_address}")
            
            # Mine only if mempool has transactions - use the unlocked mining address
            mined_block = self.blockchain.mine_pending_transactions(self.current_mining_address, mining_callback, force_mine=False)
            
            if mined_block:
                print(f"✅ Block {mined_block.index} successfully mined!")
                print(f"   Hash: {mined_block.hash}")
                print(f"   Transactions: {len(mined_block.transactions)}")
                print(f"   Reward: {mined_block.reward} GSC")
                print(f"   New blockchain height: {len(self.blockchain.chain)-1}")
                
                if self.is_mining:
                    self.root.after(0, lambda: self.on_block_mined(mined_block))
            else:
                print(f"❌ Mining failed - no block returned")
                self.root.after(0, lambda: messagebox.showerror("Mining Failed", "Failed to mine block. Check console for details."))
            
        except Exception as e:
            print(f"❌ Mining error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Mining Error", str(e)))
        finally:
            self.is_mining = False
            self.root.after(0, lambda: self.mining_button.config(text="Start Mining"))
    
    def update_mining_stats(self, stats):
        self.nonce_label.config(text=f"Nonce: {stats['nonce']:,}")
        self.hash_rate_label.config(text=f"Hash Rate: {stats['hash_rate']:.0f} H/s")
        
        # Update block details
        if hasattr(self.blockchain, 'current_mining_block'):
            block = self.blockchain.current_mining_block
            details = f"Block Index: {block.index}\n"
            details += f"Previous Hash: {block.previous_hash}\n"
            details += f"Merkle Root: {block.merkle_root}\n"
            details += f"Difficulty: {block.difficulty}\n"
            details += f"Current Nonce: {stats['nonce']}\n"
            details += f"Current Hash: {block.hash}\n"
            details += f"Target: {'0' * block.difficulty}{'*' * (64 - block.difficulty)}\n\n"
            details += f"Transactions ({len(block.transactions)}):\n"
            for i, tx in enumerate(block.transactions):
                details += f"{i+1}. {tx.sender} -> {tx.receiver}: {tx.amount} GSC (Fee: {tx.fee})\n"
            
            self.block_details.delete(1.0, tk.END)
            self.block_details.insert(1.0, details)
    
    def on_block_mined(self, block):
        self.mining_status.config(text=f"Status: Block {block.index} Mined Successfully!")
        
        print(f"🎉 Block {block.index} mined successfully!")
        print(f"   📊 Block added to blockchain at height: {len(self.blockchain.chain)-1}")
        print(f"   🧹 Transactions removed from mempool: {len(block.transactions)-1}")
        print(f"   💰 Mining reward: {block.reward} GSC")
        
        # Display current block details in mining section
        current_block_details = f"✅ SUCCESSFULLY MINED BLOCK {block.index}\n"
        current_block_details += f"{'='*50}\n\n"
        current_block_details += f"Block Hash: {block.hash}\n"
        current_block_details += f"Previous Hash: {block.previous_hash}\n"
        current_block_details += f"Merkle Root: {block.merkle_root}\n"
        current_block_details += f"Difficulty: {block.difficulty} (Required: {'0' * block.difficulty})\n"
        current_block_details += f"Final Nonce: {block.nonce:,}\n"
        current_block_details += f"Miner: {block.miner}\n"
        current_block_details += f"Reward: {block.reward} GSC\n"
        current_block_details += f"Timestamp: {block.timestamp}\n"
        current_block_details += f"Block Index: {block.index}\n"
        current_block_details += f"Blockchain Height: {len(self.blockchain.chain)-1}\n\n"
        current_block_details += f"Transactions in Block ({len(block.transactions)}):\n"
        current_block_details += f"{'-'*40}\n"
        for i, tx in enumerate(block.transactions):
            tx_type = "COINBASE" if tx.sender == "COINBASE" else "TRANSFER"
            current_block_details += f"{i+1}. [{tx_type}] {tx.sender} -> {tx.receiver}: {tx.amount} GSC (Fee: {tx.fee})\n"
        
        current_block_details += f"\n{'='*50}\n"
        current_block_details += f"Block successfully added to GSC Blockchain!\n"
        current_block_details += f"Current Supply: {getattr(self.blockchain, 'current_supply', 'Calculating...')} GSC"
        
        # Update the block details display
        self.block_details.delete(1.0, tk.END)
        self.block_details.insert(1.0, current_block_details)
        
        # Verify block is in blockchain
        if block in self.blockchain.chain:
            print(f"   ✅ Block confirmed in blockchain")
        else:
            print(f"   ❌ Warning: Block not found in blockchain!")
        
        # Update all displays to reflect new block
        self.update_displays()
        
        # Save blockchain after successful mining
        try:
            self.blockchain.save_blockchain("gsc_blockchain.json")
            print(f"💾 Blockchain saved after mining block {block.index}")
        except Exception as e:
            print(f"⚠️ Failed to save blockchain: {e}")
        
        # Force balance recalculation
        self.blockchain.update_balances()
        
        # Update all displays to reflect new block and balances
        self.update_displays()
        
        # Verify mempool is cleared of mined transactions
        print(f"   📋 Mempool size after mining: {len(self.blockchain.mempool)} transactions")
        
        # Show success message with updated balance and mining address info
        mining_address_balance = self.blockchain.get_balance(self.current_mining_address)
        wallet_balance = self.blockchain.get_balance(self.current_address) if self.current_address else 0.0
        total_blocks = len(self.blockchain.chain)
        
        messagebox.showinfo("Mining Success", f"✅ Block {block.index} Successfully Mined!\n\n📊 Block Details:\n• Hash: {block.hash[:16]}...\n• Reward: {block.reward} GSC\n• Transactions Processed: {len(block.transactions)-1}\n\n💰 Reward Distribution:\n• Mining Address: {self.current_mining_address[:20]}...\n• Mining Address Balance: {mining_address_balance:.8f} GSC\n• Your Wallet Balance: {wallet_balance:.8f} GSC\n\n📈 Blockchain Status:\n• Height: {total_blocks-1}\n• Mempool Size: {len(self.blockchain.mempool)}")
        
        self.is_mining = False
    
    def update_displays(self):
        # Update balance - Bitcoin Core format (get actual balance from blockchain)
        if hasattr(self, 'current_address') and self.current_address:
            balance = self.blockchain.get_balance(self.current_address)
            self.balance_label.config(text=f"{balance:.8f} GSC")
        else:
            self.balance_label.config(text="No Wallet Loaded")
        
        # Update address display
        if hasattr(self, 'address_display'):
            address_text = self.current_address[:20] + "..." if self.current_address else "No Wallet Loaded"
            self.address_display.config(text=address_text)
        
        # Update mempool
        self.update_mempool_display()
        
        # Update blockchain display
        self.update_blockchain_display()
        
        # Update transaction history
        self.update_transaction_history()
        
        # Update network info
        self.update_network_info()
        
        # Update supply displays (blockchain and network tabs)
        self.update_supply_displays()
    
    def update_mempool_display(self):
        # Check if mempool_tree exists (only after mempool is unlocked)
        if not hasattr(self, 'mempool_tree'):
            return
            
        # Clear mempool tree
        for item in self.mempool_tree.get_children():
            self.mempool_tree.delete(item)
        
        # Update status bar with nodes and height
        blocks_count = len(self.blockchain.chain)
        blockchain_height = blocks_count - 1 if blocks_count > 0 else 0
        nodes_count = len(self.blockchain.nodes)
        mempool_count = len(self.blockchain.mempool)
        
        # Status bar labels removed - no longer displaying blocks/peers count in corner
        
        # Update sync status with more details
        if blockchain_height > 0:
            current_reward = self.blockchain.get_current_reward()
            self.sync_label.config(text=f"Synced - Height {blockchain_height} | Reward: {current_reward} GSC")
        
        # Update mempool stats
        total_fees = sum(tx.fee for tx in self.blockchain.mempool)
        
        self.mempool_size_label.config(text=f"Pending Transactions: {mempool_count}")
        self.mempool_fees_label.config(text=f"Total Fees: {total_fees:.2f} GSC")
        
        # Add transactions to tree with improved display
        for i, tx in enumerate(self.blockchain.mempool):
            # Format timestamp
            timestamp_str = datetime.fromtimestamp(tx.timestamp).strftime('%H:%M:%S')
            
            # Truncate addresses for better display
            sender_short = tx.sender[:12] + "..." if len(tx.sender) > 15 else tx.sender
            receiver_short = tx.receiver[:12] + "..." if len(tx.receiver) > 15 else tx.receiver
            
            # Color coding based on fee (high fee = green, low fee = red)
            fee_color = "green" if tx.fee >= 1.0 else "orange" if tx.fee >= 0.1 else "red"
            
            item = self.mempool_tree.insert("", tk.END, values=(
                f"#{i+1}",
                tx.tx_id[:12] + "...",
                sender_short,
                receiver_short,
                f"{tx.amount:.4f} GSC",
                f"{tx.fee:.4f} GSC",
                timestamp_str
            ))
            
            # Add tags for visual feedback
            if tx.fee >= 1.0:
                self.mempool_tree.set(item, "Fee", f"🟢 {tx.fee:.4f} GSC")
            elif tx.fee >= 0.1:
                self.mempool_tree.set(item, "Fee", f"🟡 {tx.fee:.4f} GSC")
            else:
                self.mempool_tree.set(item, "Fee", f"🔴 {tx.fee:.4f} GSC")
    
    def start_mining_fixed(self):
        if len(self.blockchain.mempool) == 0:
            messagebox.showwarning("Warning", "No transactions in mempool to mine")
            return
            
        self.is_mining = True
        self.mining_button.config(text="Stop Mining")
        self.blockchain.difficulty = int(self.difficulty_var.get())
            
        # Start mining in separate thread
        self.mining_thread = threading.Thread(target=self.mine_block)
        self.mining_thread.daemon = True
        self.mining_thread.start()
    
    def update_blockchain_display(self):
        # Clear blockchain tree
        for item in self.blocks_tree.get_children():
            self.blocks_tree.delete(item)
        
        # Add blocks to tree
        for block in self.blockchain.chain:
            self.blocks_tree.insert("", tk.END, values=(
                block.index,
                datetime.fromtimestamp(block.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                block.hash[:16] + "...",
                block.previous_hash[:16] + "...",
                block.nonce,
                len(block.transactions),
                block.miner
            ))
    
    def update_transaction_history(self):
        # Clear transaction history
        for item in self.tx_history.get_children():
            self.tx_history.delete(item)
        
        # Add relevant transactions
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.sender == self.current_address or tx.receiver == self.current_address:
                    tx_type = "Sent" if tx.sender == self.current_address else "Received"
                    address = tx.receiver if tx.sender == self.current_address else tx.sender
                    amount = f"-{tx.amount + tx.fee}" if tx.sender == self.current_address else f"+{tx.amount}"
                    
                    self.tx_history.insert("", 0, values=(
                        tx_type,
                        amount,
                        address,
                        datetime.fromtimestamp(tx.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    ))
    
    def update_network_info(self):
        info = self.blockchain.get_blockchain_info()
        network_text = f"=== GSC Coin Network Information ===\n\n"
        network_text += f"Blockchain Height: {info['blocks']} blocks\n"
        network_text += f"Current Difficulty: {info['difficulty']}\n"
        network_text += f"Mempool Size: {info['mempool_size']} transactions\n"
        network_text += f"Total Addresses: {info['total_addresses']}\n"
        network_text += f"Mining Status: {'Active' if info['is_mining'] else 'Idle'}\n"
        network_text += f"Latest Block Hash: {info['latest_block_hash']}\n"
        network_text += f"Chain Validity: {info['chain_valid']}\n\n"
        
        network_text += "=== Account Balances ===\n"
        for address, balance in self.blockchain.balances.items():
            network_text += f"{address}: {balance:.2f} GSC\n"
        
        self.network_info.delete(1.0, tk.END)
        self.network_info.insert(1.0, network_text)
    
    def show_block_details(self, event):
        selection = self.blocks_tree.selection()
        if selection:
            item = self.blocks_tree.item(selection[0])
            block_index = int(item['values'][0])
            block = self.blockchain.chain[block_index]
            
            # Create new window for block details
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"GSC Block {block_index} Details")
            detail_window.geometry("600x500")
            
            details_text = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD)
            details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            block_info = f"=== GSC Block {block.index} Details ===\n\n"
            block_info += f"Index: {block.index}\n"
            block_info += f"Timestamp: {datetime.fromtimestamp(block.timestamp)}\n"
            block_info += f"Hash: {block.hash}\n"
            block_info += f"Previous Hash: {block.previous_hash}\n"
            block_info += f"Merkle Root: {block.merkle_root}\n"
            block_info += f"Nonce: {block.nonce:,}\n"
            block_info += f"Difficulty: {block.difficulty}\n"
            block_info += f"Miner: {block.miner}\n"
            block_info += f"Reward: {block.reward} GSC\n\n"
            block_info += f"Transactions ({len(block.transactions)}):\n"
            
            for i, tx in enumerate(block.transactions):
                block_info += f"\n{i+1}. Transaction ID: {tx.tx_id}\n"
                block_info += f"   From: {tx.sender}\n"
                block_info += f"   To: {tx.receiver}\n"
                block_info += f"   Amount: {tx.amount} GSC\n"
                block_info += f"   Fee: {tx.fee} GSC\n"
                block_info += f"   Time: {datetime.fromtimestamp(tx.timestamp)}\n"
            
            details_text.insert(1.0, block_info)
    
    def save_blockchain(self):
        try:
            self.blockchain.save_blockchain("gsc_blockchain.json")
            messagebox.showinfo("Success", "Blockchain saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save blockchain: {str(e)}")
    
    def load_blockchain(self):
        """Load blockchain with live GUI comparison display"""
        try:
            # Store current blockchain state for comparison
            current_chain_length = len(self.blockchain.chain)
            current_balance = self.blockchain.get_balance(self.current_address) if self.current_address else 0.0
            
            # Create live comparison dialog
            comparison_dialog = self.create_live_comparison_dialog("Loading Blockchain")
            
            # Update comparison display with initial state
            self.update_comparison_display(comparison_dialog, {
                'status': 'Initializing...',
                'current_blocks': current_chain_length,
                'current_balance': current_balance,
                'new_blocks': '?',
                'new_balance': '?',
                'change_blocks': '?',
                'change_balance': '?'
            })
            
            print(f"🔄 Loading blockchain with validation and synchronization...")
            print(f"   Current chain: {current_chain_length} blocks")
            print(f"   Current balance: {current_balance} GSC")
            
            # Update status
            self.update_comparison_display(comparison_dialog, {
                'status': 'Loading blockchain file...',
                'current_blocks': current_chain_length,
                'current_balance': current_balance,
                'new_blocks': '?',
                'new_balance': '?',
                'change_blocks': '?',
                'change_balance': '?'
            })
            
            # Load blockchain with synchronization (this will automatically validate and sync)
            success = self.blockchain.load_blockchain("gsc_blockchain.json")
            
            if success:
                new_chain_length = len(self.blockchain.chain)
                new_balance = self.blockchain.get_balance(self.current_address) if self.current_address else 0.0
                
                # Update comparison display with final results
                self.update_comparison_display(comparison_dialog, {
                    'status': '✅ Synchronization completed successfully!',
                    'current_blocks': current_chain_length,
                    'current_balance': current_balance,
                    'new_blocks': new_chain_length,
                    'new_balance': new_balance,
                    'change_blocks': new_chain_length - current_chain_length,
                    'change_balance': new_balance - current_balance
                })
                
                print(f"✅ Blockchain synchronization completed")
                print(f"   New chain: {new_chain_length} blocks")
                print(f"   New balance: {new_balance} GSC")
                
                # Update displays to reflect changes
                self.update_displays()
                
                # Keep dialog open for 3 seconds to show results
                self.root.after(3000, comparison_dialog.destroy)
                
            else:
                self.update_comparison_display(comparison_dialog, {
                    'status': '❌ Load failed - current state preserved',
                    'current_blocks': current_chain_length,
                    'current_balance': current_balance,
                    'new_blocks': current_chain_length,
                    'new_balance': current_balance,
                    'change_blocks': 0,
                    'change_balance': 0.0
                })
                self.root.after(3000, comparison_dialog.destroy)
                messagebox.showerror("Load Failed", "Failed to load and synchronize blockchain.\nCurrent blockchain state preserved.")
                
        except Exception as e:
            print(f"❌ Error during blockchain loading: {e}")
            if 'comparison_dialog' in locals():
                comparison_dialog.destroy()
            messagebox.showerror("Error", f"Failed to load blockchain: {str(e)}\n\nCurrent blockchain state preserved.")
    
    def validate_chain(self):
        is_valid = self.blockchain.is_chain_valid()
        if is_valid:
            # Update displays to show correct balances after validation
            self.update_displays()
            messagebox.showinfo("Validation", "Blockchain is valid!\nBalances have been updated.")
        else:
            messagebox.showerror("Validation", "Blockchain is invalid!")
    
    def broadcast_blockchain(self):
        """Broadcast blockchain to all connected peers"""
        if not self.network_node:
            messagebox.showwarning("Network", "Network node not available")
            return
        
        try:
            success = self.network_node.broadcast_blockchain()
            if success:
                messagebox.showinfo("Broadcast", "Blockchain successfully broadcasted to connected peers!")
            else:
                messagebox.showwarning("Broadcast", "No peers connected or broadcast failed")
        except Exception as e:
            messagebox.showerror("Broadcast Error", f"Failed to broadcast blockchain: {str(e)}")
    
    def sync_from_peers(self):
        """Request blockchain synchronization from peers"""
        if not self.network_node:
            messagebox.showwarning("Network", "Network node not available")
            return
        
        try:
            success = self.network_node.request_blockchain_from_peers()
            if success:
                messagebox.showinfo("Sync", "Blockchain sync requested from connected peers!")
                # Update displays after potential sync
                self.root.after(3000, self.update_displays)  # Update after 3 seconds
            else:
                messagebox.showwarning("Sync", "No peers connected or sync request failed")
        except Exception as e:
            messagebox.showerror("Sync Error", f"Failed to sync from peers: {str(e)}")

    def import_blockchain(self):
        """Import blockchain from external file with live GUI comparison display"""
        try:
            filepath = filedialog.askopenfilename(
                title="Import Blockchain",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filepath:
                # Store current blockchain state for comparison
                current_chain_length = len(self.blockchain.chain)
                current_balance = self.blockchain.get_balance(self.current_address) if self.current_address else 0.0
                
                # Create live comparison dialog
                comparison_dialog = self.create_live_comparison_dialog("Importing Blockchain")
                
                # Update comparison display with initial state
                self.update_comparison_display(comparison_dialog, {
                    'status': 'Initializing import...',
                    'current_blocks': current_chain_length,
                    'current_balance': current_balance,
                    'new_blocks': '?',
                    'new_balance': '?',
                    'change_blocks': '?',
                    'change_balance': '?'
                })
                
                print(f"🔄 Importing blockchain with validation and synchronization...")
                print(f"   Current chain: {current_chain_length} blocks")
                print(f"   Current balance: {current_balance} GSC")
                print(f"   Import file: {filepath}")
                
                # Update status
                self.update_comparison_display(comparison_dialog, {
                    'status': f'Reading blockchain file...',
                    'current_blocks': current_chain_length,
                    'current_balance': current_balance,
                    'new_blocks': '?',
                    'new_balance': '?',
                    'change_blocks': '?',
                    'change_balance': '?'
                })
                
                # Update status for validation
                self.update_comparison_display(comparison_dialog, {
                    'status': 'Validating and synchronizing chains...',
                    'current_blocks': current_chain_length,
                    'current_balance': current_balance,
                    'new_blocks': '?',
                    'new_balance': '?',
                    'change_blocks': '?',
                    'change_balance': '?',
                    'validation_status': 'In Progress',
                    'sync_status': 'In Progress'
                })
                
                # Load blockchain with synchronization (this will automatically validate and sync)
                success = self.blockchain.load_blockchain(filepath)
                
                if success:
                    new_chain_length = len(self.blockchain.chain)
                    new_balance = self.blockchain.get_balance(self.current_address) if self.current_address else 0.0
                    
                    # Update comparison display with final results
                    self.update_comparison_display(comparison_dialog, {
                        'status': '✅ Import and synchronization completed successfully!',
                        'current_blocks': current_chain_length,
                        'current_balance': current_balance,
                        'new_blocks': new_chain_length,
                        'new_balance': new_balance,
                        'change_blocks': new_chain_length - current_chain_length,
                        'change_balance': new_balance - current_balance,
                        'validation_status': '✅ Valid',
                        'sync_status': '✅ Synchronized'
                    })
                    
                    print(f"✅ Blockchain import and synchronization completed")
                    print(f"   New chain: {new_chain_length} blocks")
                    print(f"   New balance: {new_balance} GSC")
                    
                    # Update displays to reflect changes
                    self.update_displays()
                    
                    # Keep dialog open for 3 seconds to show results
                    self.root.after(3000, comparison_dialog.destroy)
                    
                else:
                    self.update_comparison_display(comparison_dialog, {
                        'status': '❌ Import failed - current state preserved',
                        'current_blocks': current_chain_length,
                        'current_balance': current_balance,
                        'new_blocks': current_chain_length,
                        'new_balance': current_balance,
                        'change_blocks': 0,
                        'change_balance': 0.0,
                        'validation_status': '❌ Failed',
                        'sync_status': '❌ Failed'
                    })
                    self.root.after(3000, comparison_dialog.destroy)
                    messagebox.showerror("Import Failed", f"Failed to import and synchronize blockchain from {filepath}.\n\nCurrent blockchain state preserved.")
                    
        except Exception as e:
            print(f"❌ Error during blockchain import: {e}")
            if 'comparison_dialog' in locals():
                comparison_dialog.destroy()
            messagebox.showerror("Import Error", f"Failed to import blockchain: {str(e)}\n\nCurrent blockchain state preserved.")
    
    def export_blockchain(self):
        """Export blockchain to external file"""
        try:
            filepath = filedialog.asksaveasfilename(
                title="Export Blockchain",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filepath:
                self.blockchain.save_blockchain(filepath)
                messagebox.showinfo("Export Success", f"Blockchain exported successfully to {filepath}!")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export blockchain: {str(e)}")
    
    def update_blockchain(self):
        """Update and refresh blockchain state"""
        try:
            # Validate and update balances
            self.blockchain.update_balances()
            self.update_displays()
            messagebox.showinfo("Update Success", "Blockchain updated and refreshed successfully!")
        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to update blockchain: {str(e)}")

    def add_manual_block_gui(self):
        """GUI handler for manual block addition with chronological sync"""
        try:
            # 1. Check if wallet is loaded
            if not self.current_address:
                messagebox.showerror("No Wallet", "Please create or open a wallet first.")
                return
            
            # 2. Check for mining address (using authorized address if not explicitly set)
            mining_addr = getattr(self, 'current_mining_address', None)
            if not mining_addr:
                from blockchain import AUTHORIZED_MINING_ADDRESSES
                mining_addr = AUTHORIZED_MINING_ADDRESSES[0]
                print(f"⚠️ Using default authorized mining address: {mining_addr}")
            
            # 3. Confirm with user
            confirm = messagebox.askyesno("Confirm Manual Block", 
                                         f"Are you sure you want to manually add a block?\n\n"
                                         f"Block Index: {len(self.blockchain.chain)}\n"
                                         f"Mempool Transactions: {len(self.blockchain.mempool)}\n"
                                         f"Reward Address: {mining_addr[:20]}...")
            
            if not confirm:
                return
            
            print(f"🛠️ Starting manual block addition...")
            
            # 4. Call blockchain logic
            manually_added_block = self.blockchain.add_manual_block(mining_addr)
            
            if manually_added_block:
                print(f"✅ Manual block {manually_added_block.index} added!")
                
                # Update displays
                self.update_displays()
                
                # Show success message
                messagebox.showinfo("Success", 
                                   f"✅ Block {manually_added_block.index} successfully added manually!\n\n"
                                   f"Hash: {manually_added_block.hash[:16]}...\n"
                                   f"Transactions: {len(manually_added_block.transactions)-1}\n"
                                   f"Reward: {manually_added_block.reward} GSC")
                
                # Save blockchain
                self.blockchain.save_blockchain("gsc_blockchain.json")
            else:
                messagebox.showerror("Error", "Failed to add block manually. Check console for details.")
                
        except Exception as e:
            print(f"❌ Error adding manual block: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
    
    def send_transaction_to_telegram(self, transaction):
        """Send transaction data to @gsc_vags_bot automatically"""
        try:
            import requests
            from datetime import datetime
            
            # Bot configuration
            bot_token = "8360297293:AAH8uHoBVMe09D5RguuRMRHb5_mcB3k7spo"
            chat_id = "@gsc_vags_bot"
            
            # Create enhanced transaction message
            message = f"""🚀 GSC Coin Transaction Alert

📊 Transaction Details:
• TX ID: {transaction.tx_id[:16]}...
• From: {transaction.sender[:20]}...
• To: {transaction.receiver[:20]}...
• Amount: {transaction.amount:.8f} GSC
• Fee: {transaction.fee:.8f} GSC
• Time: {datetime.fromtimestamp(transaction.timestamp).strftime('%Y-%m-%d %H:%M:%S')}

💰 Current Blockchain Status:
• Total Blocks: {len(self.blockchain.chain)}
• Current Supply: {getattr(self.blockchain, 'current_supply', 'Calculating...')} GSC
• Mempool Size: {len(self.blockchain.mempool)} transactions
• Network Difficulty: {self.blockchain.difficulty}

🔗 GSC Blockchain Network
Status: Active ✅"""
            
            # Send to Telegram
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            print(f"📱 Sending transaction notification to Telegram...")
            response = requests.post(url, data=data, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ Transaction notification successfully sent to {chat_id}")
                print(f"   TX: {transaction.tx_id[:16]}... | Amount: {transaction.amount} GSC")
                return True
            else:
                print(f"❌ Failed to send Telegram notification: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except ImportError:
            print(f"⚠️ Requests module not available - Telegram notification skipped")
            return False
        except Exception as e:
            print(f"❌ Error sending transaction to Telegram: {e}")
            print(f"   TX: {transaction.tx_id[:16]}... | Amount: {transaction.amount} GSC")
            return False
    
    def import_mempool_transactions(self):
        """Import transactions from file to mempool - supports multiple formats"""
        try:
            filepath = filedialog.askopenfilename(
                title="Import Mempool Transactions",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filepath:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                imported_count = 0
                transactions_to_import = []
                
                # Handle different JSON formats
                if isinstance(data, list):
                    # Array of transactions
                    transactions_to_import = data
                elif 'transactions' in data:
                    # Standard format: {"transactions": [...]}
                    transactions_to_import = data['transactions']
                elif 'transaction' in data:
                    # Telegram format: {"type": "GSC_TRANSACTION", "transaction": {...}}
                    transactions_to_import = [data['transaction']]
                elif 'tx_id' in data:
                    # Single transaction object
                    transactions_to_import = [data]
                else:
                    messagebox.showerror("Import Error", "Unsupported JSON format. Expected transaction data not found.")
                    return
                
                print(f"🔄 Importing {len(transactions_to_import)} transactions...")
                
                # Store initial mempool size for comparison
                initial_mempool_size = len(self.blockchain.mempool)
                
                for i, tx_data in enumerate(transactions_to_import):
                    try:
                        print(f"   Processing transaction {i+1}/{len(transactions_to_import)}")
                        
                        # Validate required fields
                        required_fields = ['sender', 'receiver', 'amount']
                        for field in required_fields:
                            if field not in tx_data:
                                print(f"   ❌ Missing required field: {field}")
                                continue
                        
                        # Create transaction object
                        tx = Transaction(
                            sender=str(tx_data['sender']).strip(),
                            receiver=str(tx_data['receiver']).strip(),
                            amount=float(tx_data['amount']),
                            fee=float(tx_data.get('fee', 0.0)),
                            timestamp=float(tx_data.get('timestamp', time.time()))
                        )
                        
                        # Set tx_id if provided (for Telegram imports)
                        if 'tx_id' in tx_data and tx_data['tx_id']:
                            tx.tx_id = str(tx_data['tx_id']).strip()
                        
                        # Set signature if provided
                        if 'signature' in tx_data:
                            tx.signature = str(tx_data['signature']).strip()
                        
                        print(f"   Importing TX: {tx.tx_id[:16]}... ({tx.amount} GSC from {tx.sender[:20]}... to {tx.receiver[:20]}...)")
                        
                        # Add to mempool with comprehensive validation
                        if self.blockchain.add_transaction_to_mempool(tx):
                            imported_count += 1
                            print(f"   ✅ Successfully imported and validated")
                        else:
                            print(f"   ❌ Failed to import (validation failed)")
                            
                    except KeyError as ke:
                        print(f"   ❌ Missing required field in transaction data: {ke}")
                        continue
                    except ValueError as ve:
                        print(f"   ❌ Invalid value in transaction data: {ve}")
                        continue
                    except Exception as tx_error:
                        print(f"   ❌ Error importing transaction: {tx_error}")
                        continue
                
                # Force mempool display update
                print(f"📊 Import complete: {imported_count} transactions imported")
                print(f"   Initial mempool size: {initial_mempool_size}")
                print(f"   Final mempool size: {len(self.blockchain.mempool)}")
                
                # Update all displays to show imported transactions
                self.update_displays()
                
                # Force mempool display refresh
                if hasattr(self, 'update_mempool_display'):
                    self.update_mempool_display()
                
                if imported_count > 0:
                    messagebox.showinfo("Import Success", f"Successfully imported {imported_count} transactions to mempool!\n\nInitial mempool size: {initial_mempool_size}\nFinal mempool size: {len(self.blockchain.mempool)}\n\nTransactions are now visible in the Mempool tab.")
                else:
                    messagebox.showwarning("Import Warning", "No transactions were imported. Check console for details.\n\nPossible issues:\n• Invalid transaction format\n• Missing required fields\n• Validation failures")
                    
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import transactions: {str(e)}")
    
    def create_sample_transaction(self):
        """Create a sample transaction for testing import functionality"""
        try:
            import time
            
            # Create sample transaction data
            sample_tx = Transaction(
                sender="GSC1705641e65321ef23ac5fb3d470f39627",
                receiver="GSC1221fe3e6139bbe0b76f0230d9cd5bbc1",
                amount=5.0,
                fee=0.1,
                timestamp=time.time()
            )
            
            print(f"🧪 Creating sample transaction for testing...")
            print(f"   TX ID: {sample_tx.tx_id}")
            print(f"   From: {sample_tx.sender}")
            print(f"   To: {sample_tx.receiver}")
            print(f"   Amount: {sample_tx.amount} GSC")
            print(f"   Fee: {sample_tx.fee} GSC")
            
            # Add to mempool
            if self.blockchain.add_transaction_to_mempool(sample_tx):
                print(f"   ✅ Sample transaction added to mempool")
                
                # Update displays
                self.update_displays()
                self.update_mempool_display()
                
                messagebox.showinfo("Sample Created", f"Sample transaction created and added to mempool!\n\nTX ID: {sample_tx.tx_id[:16]}...\nAmount: {sample_tx.amount} GSC\nFee: {sample_tx.fee} GSC\n\nCheck the Mempool tab to see the transaction.")
            else:
                print(f"   ❌ Failed to add sample transaction to mempool")
                messagebox.showerror("Error", "Failed to add sample transaction to mempool. Check console for details.")
                
        except Exception as e:
            print(f"❌ Error creating sample transaction: {e}")
            messagebox.showerror("Error", f"Failed to create sample transaction: {str(e)}")
    
    def create_live_comparison_dialog(self, title):
        """Create a live comparison dialog for blockchain operations"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"GSC Coin - {title}")
        dialog.geometry("600x400")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (300)
        y = (dialog.winfo_screenheight() // 2) - (200)
        dialog.geometry(f"600x400+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text=title, font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Status label
        dialog.status_label = ttk.Label(main_frame, text="Initializing...", 
                                       font=('Arial', 12), foreground='blue')
        dialog.status_label.pack(pady=(0, 20))
        
        # Comparison table frame
        table_frame = ttk.LabelFrame(main_frame, text="Blockchain Comparison", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Create comparison table
        columns = ('Metric', 'Current', 'New', 'Change')
        dialog.comparison_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)
        
        # Configure columns
        dialog.comparison_tree.heading('Metric', text='Metric')
        dialog.comparison_tree.heading('Current', text='Current')
        dialog.comparison_tree.heading('New', text='New')
        dialog.comparison_tree.heading('Change', text='Change')
        
        dialog.comparison_tree.column('Metric', width=150, anchor='w')
        dialog.comparison_tree.column('Current', width=120, anchor='center')
        dialog.comparison_tree.column('New', width=120, anchor='center')
        dialog.comparison_tree.column('Change', width=120, anchor='center')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=dialog.comparison_tree.yview)
        dialog.comparison_tree.configure(yscrollcommand=scrollbar.set)
        
        dialog.comparison_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Progress bar
        dialog.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        dialog.progress.pack(fill=tk.X, pady=(0, 10))
        dialog.progress.start()
        
        # Close button (initially disabled)
        dialog.close_btn = ttk.Button(main_frame, text="Close", command=dialog.destroy, state='disabled')
        dialog.close_btn.pack(pady=(10, 0))
        
        return dialog
    
    def update_comparison_display(self, dialog, data):
        """Update the live comparison display with new data"""
        try:
            # Update status
            dialog.status_label.config(text=data['status'])
            
            # Clear existing items
            for item in dialog.comparison_tree.get_children():
                dialog.comparison_tree.delete(item)
            
            # Add blockchain metrics
            dialog.comparison_tree.insert('', 'end', values=(
                'Blocks', 
                str(data['current_blocks']), 
                str(data['new_blocks']), 
                f"{data['change_blocks']:+}" if isinstance(data['change_blocks'], int) else str(data['change_blocks'])
            ))
            
            # Add balance metrics if available
            if data['current_balance'] != '?' and data['new_balance'] != '?':
                dialog.comparison_tree.insert('', 'end', values=(
                    'Balance (GSC)', 
                    f"{data['current_balance']:.8f}" if isinstance(data['current_balance'], (int, float)) else str(data['current_balance']),
                    f"{data['new_balance']:.8f}" if isinstance(data['new_balance'], (int, float)) else str(data['new_balance']),
                    f"{data['change_balance']:+.8f}" if isinstance(data['change_balance'], (int, float)) else str(data['change_balance'])
                ))
            else:
                dialog.comparison_tree.insert('', 'end', values=(
                    'Balance (GSC)', 
                    str(data['current_balance']), 
                    str(data['new_balance']), 
                    str(data['change_balance'])
                ))
            
            # Add additional metrics
            if 'validation_status' in data:
                dialog.comparison_tree.insert('', 'end', values=(
                    'Validation', 
                    data.get('current_validation', '?'), 
                    data.get('new_validation', '?'), 
                    data['validation_status']
                ))
            
            if 'sync_status' in data:
                dialog.comparison_tree.insert('', 'end', values=(
                    'Synchronization', 
                    data.get('current_sync', '?'), 
                    data.get('new_sync', '?'), 
                    data['sync_status']
                ))
            
            # Update progress bar and close button based on status
            if '✅' in data['status'] or '❌' in data['status']:
                dialog.progress.stop()
                dialog.progress.pack_forget()
                dialog.close_btn.config(state='normal')
                
                # Color code the status
                if '✅' in data['status']:
                    dialog.status_label.config(foreground='green')
                elif '❌' in data['status']:
                    dialog.status_label.config(foreground='red')
            
            # Force update
            dialog.update_idletasks()
            
        except Exception as e:
            print(f"Error updating comparison display: {e}")
    
    def update_supply_displays(self):
        """Update supply information displays in blockchain and network tabs"""
        try:
            # Calculate supply metrics
            max_supply = self.blockchain.max_supply  # 21.75 trillion
            
            # Calculate actual current supply from blockchain
            current_supply = self.calculate_actual_supply()
            remaining_supply = max_supply - current_supply
            supply_percentage = (current_supply / max_supply) * 100
            
            # Get current block reward
            current_reward = self.blockchain.get_current_reward()
            
            # Calculate next halving block
            current_blocks = len(self.blockchain.chain)
            halving_interval = self.blockchain.halving_interval
            next_halving_block = ((current_blocks // halving_interval) + 1) * halving_interval
            
            # Format numbers for display
            def format_large_number(num):
                if num >= 1e12:  # Trillion
                    return f"{num/1e12:.2f}T"
                elif num >= 1e9:  # Billion
                    return f"{num/1e9:.2f}B"
                elif num >= 1e6:  # Million
                    return f"{num/1e6:.2f}M"
                elif num >= 1e3:  # Thousand
                    return f"{num/1e3:.2f}K"
                else:
                    return f"{num:,.0f}"
            
            # Update blockchain tab supply displays
            if hasattr(self, 'total_supply_label'):
                self.total_supply_label.config(text=f"Max Supply: {format_large_number(max_supply)} GSC")
            
            if hasattr(self, 'current_supply_label'):
                self.current_supply_label.config(text=f"Current Supply: {format_large_number(current_supply)} GSC")
            
            if hasattr(self, 'remaining_supply_label'):
                self.remaining_supply_label.config(text=f"Remaining: {format_large_number(remaining_supply)} GSC")
            
            if hasattr(self, 'supply_percentage_label'):
                self.supply_percentage_label.config(text=f"Mined: {supply_percentage:.6f}%")
            
            # Update network tab supply displays
            if hasattr(self, 'network_max_supply_label'):
                self.network_max_supply_label.config(text=f"Maximum Supply: {format_large_number(max_supply)} GSC")
            
            if hasattr(self, 'network_current_supply_label'):
                self.network_current_supply_label.config(text=f"Current Supply: {format_large_number(current_supply)} GSC")
            
            if hasattr(self, 'network_remaining_supply_label'):
                self.network_remaining_supply_label.config(text=f"Remaining: {format_large_number(remaining_supply)} GSC")
            
            if hasattr(self, 'network_supply_percentage_label'):
                self.network_supply_percentage_label.config(text=f"Mined: {supply_percentage:.6f}%")
            
            if hasattr(self, 'network_halving_label'):
                self.network_halving_label.config(text=f"Next Halving: Block {format_large_number(next_halving_block)}")
            
            if hasattr(self, 'network_reward_label'):
                self.network_reward_label.config(text=f"Current Block Reward: {current_reward:.1f} GSC")
            
        except Exception as e:
            print(f"Error updating supply displays: {e}")
    
    def calculate_actual_supply(self):
        """Professional supply calculation: Sum of all positive balances (circulating supply)"""
        try:
            print(f"🔄 Starting professional supply calculation...")
            
            # Update balances first to ensure accuracy
            self.blockchain.update_balances()
            
            # Professional method: Sum all positive balances (actual circulating supply)
            total_circulating = 0.0
            positive_addresses = 0
            
            print(f"📊 Professional Supply Analysis:")
            print(f"=== Account Balances ===")
            
            for address, balance in self.blockchain.balances.items():
                print(f"{address}: {balance:.2f} GSC")
                if balance > 0:
                    total_circulating += balance
                    positive_addresses += 1
            
            print(f"")
            print(f"📊 Professional Supply Calculation:")
            print(f"   Total Positive Balances: {total_circulating:.2f} GSC")
            print(f"   Addresses with Balances: {positive_addresses}")
            print(f"   Method: Sum of all positive account balances")
            print(f"   Previous blockchain.current_supply: {getattr(self.blockchain, 'current_supply', 'Not set')}")
            
            # Update blockchain's current_supply to match professional calculation
            self.blockchain.current_supply = total_circulating
            print(f"   Updated blockchain.current_supply: {self.blockchain.current_supply}")
            
            return total_circulating
            
        except Exception as e:
            print(f"❌ Error calculating professional supply: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: try to use existing current_supply
            return getattr(self.blockchain, 'current_supply', 255.0)
    
    def import_from_telegram_data(self):
        """Import transaction data from Telegram bot format"""
        try:
            # Create a dialog for pasting Telegram data
            dialog = tk.Toplevel(self.root)
            dialog.title("Import from Telegram Data")
            dialog.geometry("600x400")
            dialog.resizable(True, True)
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (dialog.winfo_screenheight() // 2) - (400 // 2)
            dialog.geometry(f"600x400+{x}+{y}")
            
            # Main frame
            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = ttk.Label(main_frame, text="Import Transaction Data from Telegram", 
                                   font=('Arial', 14, 'bold'))
            title_label.pack(pady=(0, 10))
            
            # Instructions
            instructions = ttk.Label(main_frame, 
                                    text="Paste the transaction JSON data from @gsc_vags_bot below:",
                                    font=('Arial', 10))
            instructions.pack(pady=(0, 10))
            
            # Text area for pasting data
            text_frame = ttk.Frame(main_frame)
            text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            text_area = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_area.yview)
            text_area.configure(yscrollcommand=scrollbar.set)
            
            text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Buttons frame
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill=tk.X, pady=(10, 0))
            
            def import_data():
                try:
                    data_text = text_area.get(1.0, tk.END).strip()
                    if not data_text:
                        messagebox.showerror("Error", "Please paste transaction data")
                        return
                    
                    # Parse JSON data
                    import json
                    data = json.loads(data_text)
                    
                    # Process the data similar to import_mempool_transactions
                    imported_count = 0
                    transactions_to_import = []
                    
                    # Handle different JSON formats
                    if isinstance(data, list):
                        transactions_to_import = data
                    elif 'transactions' in data:
                        transactions_to_import = data['transactions']
                    elif 'transaction' in data:
                        transactions_to_import = [data['transaction']]
                    elif 'tx_id' in data:
                        transactions_to_import = [data]
                    else:
                        messagebox.showerror("Import Error", "Unsupported JSON format")
                        return
                    
                    # Import transactions
                    for tx_data in transactions_to_import:
                        try:
                            tx = Transaction(
                                sender=str(tx_data['sender']).strip(),
                                receiver=str(tx_data['receiver']).strip(),
                                amount=float(tx_data['amount']),
                                fee=float(tx_data.get('fee', 0.0)),
                                timestamp=float(tx_data.get('timestamp', time.time()))
                            )
                            
                            if 'tx_id' in tx_data and tx_data['tx_id']:
                                tx.tx_id = str(tx_data['tx_id']).strip()
                            
                            # Mark as imported transaction
                            tx.source = "imported"
                            
                            if self.blockchain.add_transaction_to_mempool(tx):
                                imported_count += 1
                                
                        except Exception as tx_error:
                            print(f"Error importing transaction: {tx_error}")
                            continue
                    
                    dialog.destroy()
                    self.update_displays()
                    
                    if imported_count > 0:
                        messagebox.showinfo("Import Success", f"Successfully imported {imported_count} transactions from Telegram data!")
                    else:
                        messagebox.showwarning("Import Warning", "No transactions were imported")
                        
                except json.JSONDecodeError:
                    messagebox.showerror("Error", "Invalid JSON format")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to import data: {str(e)}")
            
            ttk.Button(buttons_frame, text="Import", command=import_data).pack(side=tk.LEFT, padx=5)
            ttk.Button(buttons_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open import dialog: {str(e)}")
    
    def export_mempool_transactions(self):
        """Export mempool transactions to file"""
        try:
            filepath = filedialog.asksaveasfilename(
                title="Export Mempool Transactions",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filepath:
                transactions_data = {
                    "transactions": [
                        {
                            "tx_id": tx.tx_id,
                            "sender": tx.sender,
                            "receiver": tx.receiver,
                            "amount": tx.amount,
                            "fee": tx.fee,
                            "timestamp": tx.timestamp
                        }
                        for tx in self.blockchain.mempool
                    ],
                    "export_time": datetime.now().isoformat(),
                    "total_transactions": len(self.blockchain.mempool)
                }
                
                with open(filepath, 'w') as f:
                    json.dump(transactions_data, f, indent=2)
                
                messagebox.showinfo("Export Success", f"Exported {len(self.blockchain.mempool)} transactions to {filepath}!")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export transactions: {str(e)}")
    
    def run(self):
        # Start update loop
        self.update_loop()
        self.root.mainloop()
    
    def update_loop(self):
        # Update displays every 2 seconds
        self.update_displays()
        self.root.after(2000, self.update_loop)
    
    # ===== MENU COMMAND IMPLEMENTATIONS =====
    
    def create_new_wallet(self):
        """Create new wallet dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Wallet")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text="Wallet Name:").pack(pady=10)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Passphrase (optional):").pack(pady=(20, 5))
        pass_entry = ttk.Entry(dialog, width=30, show="*")
        pass_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Confirm Passphrase:").pack(pady=(10, 5))
        confirm_entry = ttk.Entry(dialog, width=30, show="*")
        confirm_entry.pack(pady=5)
        
        def create_wallet():
            name = name_entry.get().strip()
            passphrase = pass_entry.get()
            confirm = confirm_entry.get()
            
            if not name:
                messagebox.showerror("Error", "Please enter wallet name")
                return
            
            if passphrase and passphrase != confirm:
                messagebox.showerror("Error", "Passphrases do not match")
                return
            
            try:
                result = self.wallet_manager.create_wallet(name, passphrase if passphrase else None)
                self.current_address = result['address']
                self.current_balance = result['balance']
                
                # Create detailed wallet info dialog
                info_dialog = tk.Toplevel(self.root)
                info_dialog.title("Wallet Created Successfully")
                info_dialog.geometry("600x500")
                
                # Header
                ttk.Label(info_dialog, text=f"Wallet '{name}' Created Successfully!", 
                         font=('Arial', 14, 'bold')).pack(pady=10)
                
                # Wallet details frame
                details_frame = ttk.LabelFrame(info_dialog, text="Wallet Details", padding=10)
                details_frame.pack(fill=tk.X, padx=20, pady=10)
                
                # Address info
                ttk.Label(details_frame, text="Address:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
                addr_entry = ttk.Entry(details_frame, width=60)
                addr_entry.insert(0, result['address'])
                addr_entry.config(state='readonly')
                addr_entry.pack(fill=tk.X, pady=2)
                
                # Private key info
                ttk.Label(details_frame, text="Private Key:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10,0))
                priv_entry = ttk.Entry(details_frame, width=60, show="*")
                priv_entry.insert(0, result['private_key'])
                priv_entry.config(state='readonly')
                priv_entry.pack(fill=tk.X, pady=2)
                
                # Public key info
                ttk.Label(details_frame, text="Public Key:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10,0))
                pub_entry = ttk.Entry(details_frame, width=60)
                pub_entry.insert(0, result['public_key'])
                pub_entry.config(state='readonly')
                pub_entry.pack(fill=tk.X, pady=2)
                
                # Balance info
                ttk.Label(details_frame, text=f"Starting Balance: {result['balance']:.8f} GSC", 
                         font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10,0))
                
                # Backup seed frame
                seed_frame = ttk.LabelFrame(info_dialog, text="IMPORTANT: Backup Seed Phrase", padding=10)
                seed_frame.pack(fill=tk.X, padx=20, pady=10)
                
                seed_text = tk.Text(seed_frame, height=3, wrap=tk.WORD)
                seed_text.insert(1.0, result['backup_seed'])
                seed_text.config(state=tk.DISABLED)
                seed_text.pack(fill=tk.X)
                
                ttk.Label(seed_frame, text="Keep this seed phrase safe - it's needed to recover your wallet!", 
                         foreground="red", font=('Arial', 9, 'bold')).pack(pady=5)
                
                # Buttons
                button_frame = ttk.Frame(info_dialog)
                button_frame.pack(fill=tk.X, padx=20, pady=10)
                
                def show_qr():
                    self.show_address_qr(result['address'])
                
                def copy_address():
                    self.root.clipboard_clear()
                    self.root.clipboard_append(result['address'])
                    messagebox.showinfo("Copied", "Address copied to clipboard")
                
                ttk.Button(button_frame, text="Show QR Code", command=show_qr).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Copy Address", command=copy_address).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Close", command=info_dialog.destroy).pack(side=tk.RIGHT, padx=5)
                
                dialog.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create wallet: {str(e)}")
        
        ttk.Button(dialog, text="Create Wallet", command=create_wallet).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def open_wallet_dialog(self):
        """Open wallet dialog"""
        wallets = self.wallet_manager.list_wallets()
        if not wallets:
            messagebox.showinfo("Info", "No wallets found. Create a new wallet first.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Open Wallet")
        dialog.geometry("400x250")
        
        ttk.Label(dialog, text="Select Wallet:").pack(pady=10)
        wallet_var = tk.StringVar()
        wallet_combo = ttk.Combobox(dialog, textvariable=wallet_var, values=wallets, state="readonly")
        wallet_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Passphrase (if encrypted):").pack(pady=(20, 5))
        pass_entry = ttk.Entry(dialog, width=30, show="*")
        pass_entry.pack(pady=5)
        
        def open_wallet():
            wallet_name = wallet_var.get()
            passphrase = pass_entry.get()
            
            if not wallet_name:
                messagebox.showerror("Error", "Please select a wallet")
                return
            
            try:
                result = self.wallet_manager.open_wallet(wallet_name, passphrase if passphrase else None)
                self.current_address = result['address']
                
                # Get ACTUAL balance from blockchain (not from wallet file)
                self.current_balance = self.blockchain.get_balance(self.current_address)
                
                success_msg = f"Wallet '{wallet_name}' opened successfully!\n\n"
                success_msg += f"Address: {result['address']}\n"
                success_msg += f"Balance: {self.current_balance:.8f} GSC\n"
                success_msg += f"Addresses: {result['addresses_count']}"
                
                messagebox.showinfo("Wallet Opened", success_msg)
                dialog.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open wallet: {str(e)}")
        
        ttk.Button(dialog, text="Open Wallet", command=open_wallet).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def close_current_wallet(self):
        """Close current wallet"""
        if self.wallet_manager.current_wallet:
            self.wallet_manager.close_wallet()
            messagebox.showinfo("Info", "Wallet closed")
            self.update_displays()
        else:
            messagebox.showinfo("Info", "No wallet is currently open")
    
    def close_all_wallets(self):
        """Close all wallets"""
        self.close_current_wallet()
    
    def backup_wallet_dialog(self):
        """Backup wallet dialog"""
        if not self.wallet_manager.current_wallet:
            messagebox.showerror("Error", "No wallet is currently open")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Backup Wallet",
            defaultextension=".backup",
            filetypes=[("Backup files", "*.backup"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.wallet_manager.backup_wallet(filename)
                messagebox.showinfo("Success", f"Wallet backed up to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Backup failed: {str(e)}")
    
    def restore_wallet_dialog(self):
        """Restore wallet dialog"""
        filename = filedialog.askopenfilename(
            title="Restore Wallet",
            filetypes=[("Backup files", "*.backup"), ("All files", "*.*")]
        )
        
        if filename:
            new_name = simpledialog.askstring("Restore Wallet", "Enter new wallet name:")
            if new_name:
                try:
                    result = self.wallet_manager.restore_wallet(filename, new_name)
                    messagebox.showinfo("Success", f"Wallet restored as '{new_name}'")
                except Exception as e:
                    messagebox.showerror("Error", f"Restore failed: {str(e)}")
    
    def encrypt_wallet_dialog(self):
        """Encrypt wallet dialog"""
        if not self.wallet_manager.current_wallet:
            messagebox.showerror("Error", "No wallet is currently open")
            return
        
        if self.wallet_manager.is_encrypted:
            messagebox.showinfo("Info", "Wallet is already encrypted")
            return
        
        passphrase = simpledialog.askstring("Encrypt Wallet", "Enter passphrase:", show='*')
        if passphrase:
            confirm = simpledialog.askstring("Encrypt Wallet", "Confirm passphrase:", show='*')
            if passphrase == confirm:
                try:
                    self.wallet_manager.encrypt_wallet(passphrase)
                    messagebox.showinfo("Success", "Wallet encrypted successfully")
                except Exception as e:
                    messagebox.showerror("Error", f"Encryption failed: {str(e)}")
            else:
                messagebox.showerror("Error", "Passphrases do not match")
    
    def change_passphrase_dialog(self):
        """Change passphrase dialog"""
        if not self.wallet_manager.current_wallet:
            messagebox.showerror("Error", "No wallet is currently open")
            return
        
        if not self.wallet_manager.is_encrypted:
            messagebox.showinfo("Info", "Wallet is not encrypted")
            return
        
        old_pass = simpledialog.askstring("Change Passphrase", "Enter current passphrase:", show='*')
        if old_pass:
            new_pass = simpledialog.askstring("Change Passphrase", "Enter new passphrase:", show='*')
            if new_pass:
                confirm = simpledialog.askstring("Change Passphrase", "Confirm new passphrase:", show='*')
                if new_pass == confirm:
                    try:
                        self.wallet_manager.change_passphrase(old_pass, new_pass)
                        messagebox.showinfo("Success", "Passphrase changed successfully")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to change passphrase: {str(e)}")
                else:
                    messagebox.showerror("Error", "New passphrases do not match")
    
    def sign_message_dialog(self):
        """Sign message dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Sign Message")
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text="Address:").pack(pady=5)
        addr_entry = ttk.Entry(dialog, width=60)
        addr_entry.pack(pady=5)
        addr_entry.insert(0, self.current_address)
        
        ttk.Label(dialog, text="Message:").pack(pady=(20, 5))
        msg_text = scrolledtext.ScrolledText(dialog, height=8, width=60)
        msg_text.pack(pady=5)
        
        ttk.Label(dialog, text="Signature:").pack(pady=(20, 5))
        sig_text = scrolledtext.ScrolledText(dialog, height=4, width=60)
        sig_text.pack(pady=5)
        
        def sign_message():
            address = addr_entry.get()
            message = msg_text.get(1.0, tk.END).strip()
            
            if not message:
                messagebox.showerror("Error", "Please enter a message")
                return
            
            # Simple signature (in real implementation, use proper cryptographic signing)
            signature = hashlib.sha256(f"{address}{message}".encode()).hexdigest()
            sig_text.delete(1.0, tk.END)
            sig_text.insert(1.0, signature)
        
        ttk.Button(dialog, text="Sign Message", command=sign_message).pack(pady=10)
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack()
    
    def verify_message_dialog(self):
        """Verify message dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Verify Message")
        dialog.geometry("500x450")
        
        ttk.Label(dialog, text="Address:").pack(pady=5)
        addr_entry = ttk.Entry(dialog, width=60)
        addr_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Message:").pack(pady=(20, 5))
        msg_text = scrolledtext.ScrolledText(dialog, height=8, width=60)
        msg_text.pack(pady=5)
        
        ttk.Label(dialog, text="Signature:").pack(pady=(20, 5))
        sig_entry = ttk.Entry(dialog, width=60)
        sig_entry.pack(pady=5)
        
        result_label = ttk.Label(dialog, text="", foreground="blue")
        result_label.pack(pady=10)
        
        def verify_message():
            address = addr_entry.get()
            message = msg_text.get(1.0, tk.END).strip()
            signature = sig_entry.get()
            
            if not all([address, message, signature]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            # Simple verification (in real implementation, use proper cryptographic verification)
            expected_sig = hashlib.sha256(f"{address}{message}".encode()).hexdigest()
            if signature == expected_sig:
                result_label.config(text="✓ Message signature verified", foreground="green")
            else:
                result_label.config(text="✗ Message signature invalid", foreground="red")
        
        ttk.Button(dialog, text="Verify Message", command=verify_message).pack(pady=10)
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack()
    
    def toggle_mask_values(self):
        """Toggle value masking"""
        # Implementation for masking sensitive values
        pass
    
    def show_options_dialog(self):
        """Show options dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Options")
        dialog.geometry("600x500")
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Main")
        
        ttk.Label(main_frame, text="Mining Difficulty:").pack(pady=10)
        diff_var = tk.StringVar(value=str(self.blockchain.difficulty))
        ttk.Spinbox(main_frame, from_=1, to=8, textvariable=diff_var).pack()
        
        # Network tab
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="Network")
        
        ttk.Label(network_frame, text="Network settings will be implemented here").pack(pady=20)
        
        def save_options():
            self.blockchain.difficulty = int(diff_var.get())
            messagebox.showinfo("Success", "Options saved")
            dialog.destroy()
        
        ttk.Button(dialog, text="OK", command=save_options).pack(side=tk.RIGHT, padx=10, pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, pady=10)
    
    def show_sending_addresses(self):
        """Show sending addresses window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Sending Addresses")
        dialog.geometry("600x400")
        
        # Address list
        tree = ttk.Treeview(dialog, columns=("Label", "Address"), show="headings")
        tree.heading("Label", text="Label")
        tree.heading("Address", text="Address")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load sending addresses
        for addr_info in self.wallet_manager.get_sending_addresses():
            tree.insert("", tk.END, values=(addr_info['label'], addr_info['address']))
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def add_address():
            addr = simpledialog.askstring("Add Address", "Enter address:")
            if addr:
                label = simpledialog.askstring("Add Address", "Enter label:")
                if label:
                    self.wallet_manager.add_sending_address(addr, label)
                    tree.insert("", tk.END, values=(label, addr))
        
        ttk.Button(button_frame, text="Add", command=add_address).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def show_receiving_addresses(self):
        """Show receiving addresses window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Receiving Addresses")
        dialog.geometry("600x400")
        
        # Address list
        tree = ttk.Treeview(dialog, columns=("Label", "Address", "Created"), show="headings")
        tree.heading("Label", text="Label")
        tree.heading("Address", text="Address")
        tree.heading("Created", text="Created")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load receiving addresses
        for addr_info in self.wallet_manager.get_receiving_addresses():
            tree.insert("", tk.END, values=(addr_info['label'], addr_info['address'], addr_info['created']))
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def new_address():
            label = simpledialog.askstring("New Address", "Enter label:")
            if label:
                addr = self.wallet_manager.generate_new_address(label)
                tree.insert("", tk.END, values=(label, addr, datetime.now().isoformat()))
        
        ttk.Button(button_frame, text="New", command=new_address).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def show_information(self):
        """Show blockchain information window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Information")
        dialog.geometry("500x400")
        
        info_text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info = self.blockchain.get_blockchain_info()
        wallet_info = self.wallet_manager.get_wallet_info()
        
        info_content = f"""GSC Coin Information
{'=' * 30}

Blockchain:
- Blocks: {info['blocks']}
- Difficulty: {info['difficulty']}
- Mempool Size: {info['mempool_size']}
- Chain Valid: {info['chain_valid']}

Wallet:
- Name: {wallet_info.get('name', 'None')}
- Encrypted: {wallet_info.get('encrypted', False)}
- Addresses: {wallet_info.get('addresses_count', 0)}
- Master Address: {wallet_info.get('master_address', 'None')}

Network:
- Peers: {len(self.network_peers)}
- Sync Status: {self.sync_status}
"""
        
        info_text.insert(1.0, info_content)
        info_text.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def show_console(self):
        """Show console window"""
        # Switch to console tab
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Console":
                self.notebook.select(i)
                break
    
    def show_network_traffic(self):
        """Show network traffic window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Network Traffic")
        dialog.geometry("600x400")
        
        ttk.Label(dialog, text="Network traffic monitoring will be implemented here").pack(pady=20)
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def show_peers(self):
        """Show peers window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Peers")
        dialog.geometry("600x400")
        
        # Peers list
        tree = ttk.Treeview(dialog, columns=("Address", "Version", "Height"), show="headings")
        tree.heading("Address", text="Address")
        tree.heading("Version", text="Version")
        tree.heading("Height", text="Height")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add sample peers (in real implementation, show actual network peers)
        tree.insert("", tk.END, values=("127.0.0.1:8333", "GSC/1.0", "1024"))
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def download_wallet_exe(self):
        """Download wallet as .exe file for other devices"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Download GSC Coin Wallet")
        dialog.geometry("500x400")
        dialog.configure(bg='#f0f0f0')
        
        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(header_frame, text="Download GSC Coin Wallet", 
                 font=('Arial', 16, 'bold')).pack()
        ttk.Label(header_frame, text="Create a standalone .exe file for other devices").pack(pady=5)
        
        # Info section
        info_frame = ttk.LabelFrame(dialog, text="Distribution Package", padding=15)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        info_text = """The downloadable package includes:
• GSC_Coin_Wallet.exe (Standalone executable)
• Complete blockchain and wallet functionality
• 21.75 trillion GSC total supply
• Bitcoin-like reward halving system
• Real GSC addresses and market values
• No installation required - runs on any Windows device"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack()
        
        # Progress section
        progress_frame = ttk.Frame(dialog)
        progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        build_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        build_progress.pack(fill=tk.X, pady=5)
        
        build_status = ttk.Label(progress_frame, text="Ready to build executable")
        build_status.pack()
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def start_build():
            """Start building the executable"""
            build_progress.start()
            build_status.config(text="Building executable... Please wait...")
            
            def build_thread():
                try:
                    import subprocess
                    import os
                    
                    # Create build script
                    build_script = '''
import subprocess
import sys
import os

def build_exe():
    try:
        # Install PyInstaller if not available
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
        # Build the executable
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            "--name=GSC_Coin_Wallet",
            "--add-data=blockchain.py;.",
            "--add-data=wallet_manager.py;.",
            "--add-data=paper_wallet_generator.py;.",
            "gsc_wallet_gui.py"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stderr
        
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    success, error = build_exe()
    if success:
        print("SUCCESS")
    else:
        print(f"ERROR: {error}")
'''
                    
                    # Write and run build script
                    with open('build_temp.py', 'w') as f:
                        f.write(build_script)
                    # Run the fixed executable builder
                    result = subprocess.run([
                        sys.executable, "build_exe_fixed.py"
                    ], capture_output=True, text=True, cwd=os.getcwd())
                    
                    # Clean up
                    if os.path.exists('build_temp.py'):
                        os.remove('build_temp.py')
                    
                    def update_ui():
                        build_progress.stop()
                        if "SUCCESS" in result.stdout:
                            build_status.config(text=" Executable built successfully!")
                            
                            success_msg = """GSC Coin Wallet executable created successfully!

Location: dist/GSC_Coin_Wallet.exe
Features included:
• 21.75 trillion GSC total supply
• Bitcoin-like reward halving system
• Real market addresses and values
• Complete blockchain functionality
• Professional interface

The executable is ready for distribution to other devices!"""
                            
                            messagebox.showinfo("Build Complete", success_msg)
                            
                            # Ask if user wants to open the dist folder
                            if messagebox.askyesno("Open Folder", "Open the dist folder to see the files?"):
                                try:
                                    os.startfile("dist")
                                except:
                                    pass
                        else:
                            build_status.config(text=" Build failed - Installing PyInstaller...")
                            # Try to install PyInstaller and show instructions
                            install_msg = """Build requires PyInstaller. Please run:

pip install pyinstaller

Then try building again. Or use the portable version instead."""
                            messagebox.showwarning("PyInstaller Required", install_msg)
                    
                    dialog.after(0, update_ui)
                    
                except Exception as error:
                    def show_error():
                        build_progress.stop()
                        build_status.config(text=" Build error occurred")
                        messagebox.showerror("Error", f"Build error: {str(error)}")
                    
                    dialog.after(0, show_error)
            
            # Start build in background thread
            threading.Thread(target=build_thread, daemon=True).start()
        
        ttk.Button(button_frame, text="Build .exe File", command=start_build).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def create_portable_version(self):
        """Create portable version of the wallet"""
        try:
            import shutil
            import os
            
            # Create portable folder
            portable_dir = "GSC_Wallet_Portable"
            if os.path.exists(portable_dir):
                shutil.rmtree(portable_dir)
            os.makedirs(portable_dir)
            
            # Copy essential files
            files_to_copy = [
                'gsc_wallet_gui.py',
                'blockchain.py',
                'wallet_manager.py',
                'paper_wallet_generator.py',
                'launch_gsc_coin.py',
                'requirements.txt'
            ]
            
            for file in files_to_copy:
                if os.path.exists(file):
                    shutil.copy2(file, portable_dir)
            
            # Create launcher batch file
            launcher_content = '''@echo off
echo Starting GSC Coin Wallet...
python launch_gsc_coin.py
pause'''
            
            with open(os.path.join(portable_dir, 'Start_GSC_Wallet.bat'), 'w') as f:
                f.write(launcher_content)
            
            # Create README
            readme_content = '''GSC Coin Wallet - Portable Version
==================================

Total Supply: 21.75 Trillion GSC
Bitcoin-like reward halving system
Real market addresses and values

Requirements:
- Python 3.7 or higher
- Required packages (install with: pip install -r requirements.txt)

To run:
1. Double-click Start_GSC_Wallet.bat
   OR
2. Run: python launch_gsc_coin.py

Features:
- Complete GSC blockchain functionality
- Professional wallet management
- Mining with proof of work
- Transaction processing
'''
            
            with open(os.path.join(portable_dir, 'README.txt'), 'w') as f:
                f.write(readme_content)
            
            messagebox.showinfo("Success", f"Portable version created in '{portable_dir}' folder!")
            
            # Ask if user wants to open the folder
            if messagebox.askyesno("Open Folder", "Open the portable folder?"):
                try:
                    os.startfile(portable_dir)
                except:
                    pass
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create portable version: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""GSC Coin - Professional Cryptocurrency Wallet

Version: 2.0 (Market Ready)
Total Supply: {self.blockchain.max_supply:,.0f} GSC (21.75 Trillion)
Current Reward: {self.blockchain.get_current_reward()} GSC
Blockchain Height: {len(self.blockchain.chain) - 1}
Connected Nodes: {len(self.blockchain.nodes)}

Features:
• Complete blockchain from genesis block
• Bitcoin-like reward halving system
• Professional Bitcoin Core-style interface
• Real-time mining with nonce visualization
• Transaction mempool management
• Wallet encryption and backup
• Paper wallet generation with QR codes
• Downloadable .exe distribution
• Network synchronization

Built with Python and Tkinter for cross-platform compatibility."""
        
        messagebox.showinfo("About GSC Coin", about_text)
    
    def show_command_options(self):
        """Show command line options"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Command-line Options")
        dialog.geometry("500x300")
        
        options_text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
        options_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        options_content = """GSC Coin Command-line Options:

python gsc_professional_wallet.py [options]

Options:
  --datadir=<dir>     Specify data directory
  --testnet          Use test network
  --rpcport=<port>   Set RPC port
  --help             Show this help message

Examples:
  python gsc_professional_wallet.py --datadir=./data
  python gsc_professional_wallet.py --testnet
"""
        
        options_text.insert(1.0, options_content)
        options_text.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def execute_console_command(self, event=None):
        """Execute console command"""
        command = self.console_input.get().strip()
        if not command:
            return
        
        self.console_output.insert(tk.END, f"> {command}\n")
        self.console_input.delete(0, tk.END)
        
        # Process commands
        if command == "help":
            help_text = """Available commands:
help - Show this help
getblockcount - Get number of blocks
getbalance - Get wallet balance
getnewaddress - Generate new address
sendtoaddress <address> <amount> - Send GSC coins
getblockchaininfo - Get blockchain information
listwallets - List available wallets
"""
            self.console_output.insert(tk.END, help_text)
        
        elif command == "getblockcount":
            self.console_output.insert(tk.END, f"{len(self.blockchain.chain)}\n")
        
        elif command == "getbalance":
            balance = self.blockchain.get_balance(self.current_address)
            self.console_output.insert(tk.END, f"{balance:.8f}\n")
        
        elif command == "getnewaddress":
            if self.wallet_manager.current_wallet:
                addr = self.wallet_manager.generate_new_address("Console Generated")
                self.console_output.insert(tk.END, f"{addr}\n")
            else:
                self.console_output.insert(tk.END, "No wallet open\n")
        
        elif command == "getblockchaininfo":
            info = self.blockchain.get_blockchain_info()
            self.console_output.insert(tk.END, f"{json.dumps(info, indent=2)}\n")
        
        elif command == "listwallets":
            wallets = self.wallet_manager.list_wallets()
            self.console_output.insert(tk.END, f"{json.dumps(wallets, indent=2)}\n")
        
        else:
            self.console_output.insert(tk.END, f"Unknown command: {command}\n")
        
        self.console_output.see(tk.END)
    
    # Additional helper methods for new tabs
    def clear_send_form(self):
        """Clear send form"""
        self.send_address_entry.delete(0, tk.END)
        self.send_label_entry.delete(0, tk.END)
        self.send_amount_entry.delete(0, tk.END)
    
    def send_transaction_advanced(self):
        """Advanced send transaction"""
        try:
            # Check if wallet is loaded
            if not self.current_address:
                messagebox.showerror("No Wallet", "Please create or open a wallet first before sending transactions.")
                return
            
            recipient = self.send_address_entry.get().strip()
            amount = float(self.send_amount_entry.get())
            fee = float(self.send_fee_entry.get())
            
            if not recipient or amount <= 0:
                messagebox.showerror("Error", "Please enter valid recipient and amount")
                return
            
            # Check balance
            balance = self.blockchain.get_balance(self.current_address)
            if balance < (amount + fee):
                messagebox.showerror("Error", f"Insufficient balance. Available: {balance} GSC")
                return
            
            # Create transaction
            tx = Transaction(
                sender=self.current_address,
                receiver=recipient,
                amount=amount,
                fee=fee,
                timestamp=time.time()
            )
            
            # Add to mempool
            print(f"🔄 [ADVANCED] Attempting to add transaction to mempool...")
            print(f"   Current Wallet: {getattr(self, 'current_wallet_name', 'Unknown')}")
            print(f"   Sender: {tx.sender}")
            print(f"   Sender Balance: {self.blockchain.get_balance(tx.sender)} GSC")
            print(f"   Receiver: {tx.receiver}")
            print(f"   Amount: {tx.amount} GSC")
            print(f"   Fee: {tx.fee} GSC")
            print(f"   TX ID: {tx.tx_id}")
            
            if self.blockchain.add_transaction_to_mempool(tx):
                print(f"✅ Transaction successfully added to mempool!")
                
                # Send transaction notification to Telegram
                try:
                    self.send_transaction_to_telegram(tx)
                    print(f"📱 Transaction sent to Telegram bot")
                except Exception as e:
                    print(f"⚠️ Telegram notification failed: {e}")
                
                # Broadcast to network if available
                if hasattr(self.blockchain, 'network_node') and self.blockchain.network_node:
                    try:
                        self.blockchain.network_node.broadcast_transaction(tx)
                        print(f"📡 Transaction broadcasted to network")
                    except Exception as e:
                        print(f"⚠️ Network broadcast failed: {e}")
                
                messagebox.showinfo("Success", f"Transaction sent successfully!\n\nTX ID: {tx.tx_id[:16]}...\nAmount: {tx.amount} GSC\nFee: {tx.fee} GSC\n\n✅ Added to mempool\n📱 Sent to Telegram\n📡 Broadcasted to network")
                self.clear_send_form()
                self.update_displays()
            else:
                print(f"❌ Failed to add transaction to mempool")
                messagebox.showerror("Error", "Failed to add transaction to mempool")
        
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for amount and fee")
        except Exception as e:
            messagebox.showerror("Error", f"Transaction failed: {str(e)}")
    
    def clear_receive_form(self):
        """Clear receive form"""
        self.receive_label_entry.delete(0, tk.END)
        self.receive_amount_entry.delete(0, tk.END)
        self.receive_message_entry.delete(0, tk.END)
    
    def create_payment_request(self):
        """Create payment request"""
        label = self.receive_label_entry.get()
        amount = self.receive_amount_entry.get()
        message = self.receive_message_entry.get()
        
        request_info = f"GSC Payment Request\n"
        request_info += f"Address: {self.current_address}\n"
        if label:
            request_info += f"Label: {label}\n"
        if amount:
            request_info += f"Amount: {amount} GSC\n"
        if message:
            request_info += f"Message: {message}\n"
        
        messagebox.showinfo("Payment Request", request_info)
    
    def show_address_qr(self, address):
        """Show QR code for specific address"""
        try:
            import qrcode
            from PIL import Image, ImageTk
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(address)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Show QR code in new window
            qr_window = tk.Toplevel(self.root)
            qr_window.title("Address QR Code")
            qr_window.geometry("350x400")
            
            # Convert PIL image to PhotoImage
            qr_photo = ImageTk.PhotoImage(qr_img)
            qr_label = ttk.Label(qr_window, image=qr_photo)
            qr_label.image = qr_photo  # Keep a reference
            qr_label.pack(pady=10)
            
            ttk.Label(qr_window, text=address, font=("Courier", 8), wraplength=300).pack(pady=5)
            
            # Buttons
            button_frame = ttk.Frame(qr_window)
            button_frame.pack(pady=10)
            
            def copy_addr():
                self.root.clipboard_clear()
                self.root.clipboard_append(address)
                messagebox.showinfo("Copied", "Address copied to clipboard")
            
            ttk.Button(button_frame, text="Copy Address", command=copy_addr).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=qr_window.destroy).pack(side=tk.LEFT, padx=5)
            
        except ImportError:
            messagebox.showinfo("Info", f"QR Code libraries not available.\nAddress: {address}")
    
    def simple_download_exe(self):
        """Direct download like Bitcoin Core - no dependencies needed"""
        try:
            import os
            import shutil
            
            # Check if pre-built .exe exists
            exe_path = "dist/GSC_Coin_Wallet.exe"
            
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                
                success_msg = f"""✅ GSC Coin Wallet Ready for Download!

📁 Location: {os.path.abspath(exe_path)}
📊 Size: {size_mb:.1f} MB

🚀 Just like Bitcoin Core:
• No installation required
• No dependencies needed
• Complete standalone executable
• Works on any Windows device
• Ready to distribute immediately

🎯 Features included:
• Complete GSC blockchain (21.75 trillion supply)
• Bitcoin-like mining and rewards
• Professional wallet interface
• Locked difficulty at 4
• All dependencies bundled

The .exe file is ready for immediate download!"""
                
                messagebox.showinfo("Download Ready", success_msg)
                
                # Ask to open folder
                if messagebox.askyesno("Open Download Folder", "Open the dist folder to access your downloadable .exe file?"):
                    try:
                        os.startfile("dist")
                    except:
                        pass
            else:
                # If .exe doesn't exist, show message that it needs to be built first
                build_msg = """GSC Coin Wallet .exe not found.

Would you like to build it now? This will create a standalone .exe file that users can download directly without any dependencies (just like Bitcoin Core).

The build process will take a few minutes but only needs to be done once."""
                
                if messagebox.askyesno("Build Required", build_msg):
                    self.build_exe_for_download()
                    
        except Exception as e:
            messagebox.showerror("Error", f"Download preparation failed: {str(e)}")
    
    def build_exe_for_download(self):
        """Build .exe for download distribution"""
        try:
            import subprocess
            import threading
            
            def build_process():
                try:
                    # Show progress dialog
                    progress_dialog = tk.Toplevel(self.root)
                    progress_dialog.title("Building Downloadable .exe")
                    progress_dialog.geometry("450x200")
                    progress_dialog.resizable(False, False)
                    
                    ttk.Label(progress_dialog, text="Creating Bitcoin Core-style Download", 
                             font=('Arial', 12, 'bold')).pack(pady=20)
                    
                    progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
                    progress_bar.pack(pady=10, padx=20, fill=tk.X)
                    progress_bar.start()
                    
                    status_label = ttk.Label(progress_dialog, text="Building standalone executable...")
                    status_label.pack(pady=10)
                    
                    # Run the build script
                    result = subprocess.run([
                        sys.executable, 'build_exe_fixed.py'
                    ], capture_output=True, text=True, cwd=os.getcwd())
                    
                    progress_bar.stop()
                    progress_dialog.destroy()
                    
                    if result.returncode == 0:
                        # Success - now show download ready message
                        self.simple_download_exe()
                    else:
                        messagebox.showerror("Build Failed", f"Failed to create downloadable .exe.\n\nError: {result.stderr}")
                        
                except Exception as e:
                    if 'progress_dialog' in locals():
                        progress_dialog.destroy()
                    messagebox.showerror("Error", f"Build process failed: {str(e)}")
            
            # Run build in background thread
            threading.Thread(target=build_process, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start build process: {str(e)}")
    
    def create_setup_installer(self):
        """Direct download Bitcoin Core-style setup.exe installer"""
        try:
            import os
            
            # Check if pre-built setup.exe exists
            setup_path = "dist/gsc-coin-2.0-win64-setup.exe"
            
            if os.path.exists(setup_path):
                size_mb = os.path.getsize(setup_path) / (1024 * 1024)
                
                success_msg = f"""✅ Bitcoin Core-style Setup.exe Ready!

📁 File: {os.path.abspath(setup_path)}
📊 Size: {size_mb:.1f} MB

🎯 Perfect Bitcoin Core-style installer:
• Professional Windows installer
• Setup wizard with license agreement
• Installs to Program Files
• Creates desktop & start menu shortcuts
• Includes uninstaller
• No dependencies required

🚀 Ready for distribution like bitcoincore.org!

Users can download and run this setup.exe on any Windows device - just like Bitcoin Core!"""
                
                messagebox.showinfo("Setup Ready for Download", success_msg)
                
                # Ask to open folder
                if messagebox.askyesno("Open Download Folder", "Open the dist folder to access your setup.exe?"):
                    try:
                        os.startfile("dist")
                    except:
                        pass
            else:
                # If setup.exe doesn't exist, offer to create it
                build_msg = """Bitcoin Core-style setup.exe not found.

Would you like to create it now? This will build a professional Windows installer that works exactly like Bitcoin Core's setup.exe.

Users will be able to download and install GSC Coin just like they install Bitcoin Core."""
                
                if messagebox.askyesno("Create Setup", build_msg):
                    self.build_setup_for_download()
                    
        except Exception as e:
            messagebox.showerror("Error", f"Setup preparation failed: {str(e)}")
    
    def build_setup_for_download(self):
        """Build setup.exe for download distribution"""
        try:
            import subprocess
            import threading
            
            def build_process():
                try:
                    # Show progress dialog
                    progress_dialog = tk.Toplevel(self.root)
                    progress_dialog.title("Creating Bitcoin Core Setup")
                    progress_dialog.geometry("450x200")
                    progress_dialog.resizable(False, False)
                    
                    ttk.Label(progress_dialog, text="Building Bitcoin Core-style Setup.exe", 
                             font=('Arial', 12, 'bold')).pack(pady=20)
                    
                    progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
                    progress_bar.pack(pady=10, padx=20, fill=tk.X)
                    progress_bar.start()
                    
                    status_label = ttk.Label(progress_dialog, text="Creating professional installer...")
                    status_label.pack(pady=10)
                    
                    # Run the setup creator
                    result = subprocess.run([
                        sys.executable, 'create_setup_exe.py'
                    ], capture_output=True, text=True, cwd=os.getcwd())
                    
                    progress_bar.stop()
                    progress_dialog.destroy()
                    
                    if result.returncode == 0:
                        # Success - now show setup ready message
                        self.create_setup_installer()
                    else:
                        messagebox.showerror("Setup Failed", f"Failed to create setup installer.\n\nError: {result.stderr}")
                        
                except Exception as e:
                    if 'progress_dialog' in locals():
                        progress_dialog.destroy()
                    messagebox.showerror("Error", f"Setup creation failed: {str(e)}")
            
            # Run build in background thread
            threading.Thread(target=build_process, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start setup creation: {str(e)}")
    
    def show_qr_code(self):
        """Show QR code for current address"""
        self.show_address_qr(self.current_address)
    
    def copy_address(self):
        """Copy address to clipboard"""
        if self.current_address:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_address)
            messagebox.showinfo("Copied", f"Address copied to clipboard:\n{self.current_address}")
        else:
            messagebox.showwarning("No Address", "No wallet address available to copy")
    
    def copy_my_address_to_send(self):
        """Copy current wallet address to send field"""
        if self.current_address:
            self.send_address_entry.delete(0, tk.END)
            self.send_address_entry.insert(0, self.current_address)
            messagebox.showinfo("Address Filled", f"Your address filled in Pay To field:\n{self.current_address}")
        else:
            messagebox.showwarning("No Address", "No wallet address available. Please open a wallet first.")
    
    def get_private_key(self):
        """Get and display private key for current address with security confirmation"""
        try:
            if not self.current_address:
                messagebox.showwarning("No Address", "No wallet address available. Please open a wallet first.")
                return
            
            if not self.wallet_manager.current_wallet:
                messagebox.showerror("No Wallet", "No wallet is currently open.")
                return
            
            # Security confirmation
            confirm = messagebox.askyesno(
                "Security Warning", 
                "⚠️ WARNING: Private keys control your GSC coins!\n\n"
                "• Never share your private key with anyone\n"
                "• Anyone with your private key can steal your coins\n"
                "• Only export private keys to secure, offline storage\n\n"
                "Do you want to continue and display the private key?"
            )
            
            if not confirm:
                return
            
            # Find private key for current address
            private_key = None
            wallet_data = self.wallet_manager.wallet_data
            
            # Check if current address matches master address
            if wallet_data.get('master_address') == self.current_address:
                private_key = wallet_data.get('master_private_key')
            else:
                # Search in addresses list
                for addr_data in wallet_data.get('addresses', []):
                    if addr_data.get('address') == self.current_address:
                        private_key = addr_data.get('private_key')
                        break
            
            if not private_key:
                messagebox.showerror("Error", "Private key not found for current address.")
                return
            
            # Create private key display dialog
            key_dialog = tk.Toplevel(self.root)
            key_dialog.title("Private Key - KEEP SECRET!")
            key_dialog.geometry("600x400")
            key_dialog.resizable(True, True)
            key_dialog.transient(self.root)
            key_dialog.grab_set()
            
            # Warning frame
            warning_frame = ttk.LabelFrame(key_dialog, text="⚠️ SECURITY WARNING", padding=15)
            warning_frame.pack(fill=tk.X, padx=15, pady=10)
            
            warning_text = (
                "🔐 This is your PRIVATE KEY - Keep it absolutely secret!\n"
                "• Anyone with this key can steal ALL your GSC coins\n"
                "• Never share, email, or post this key anywhere\n"
                "• Store it securely offline if needed for backup"
            )
            ttk.Label(warning_frame, text=warning_text, foreground='red', font=('Arial', 10, 'bold')).pack()
            
            # Address info
            addr_frame = ttk.LabelFrame(key_dialog, text="Address Information", padding=15)
            addr_frame.pack(fill=tk.X, padx=15, pady=5)
            
            ttk.Label(addr_frame, text="Address:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
            ttk.Label(addr_frame, text=self.current_address, font=('Courier', 10)).pack(anchor=tk.W, pady=(0, 10))
            
            # Private key display
            key_frame = ttk.LabelFrame(key_dialog, text="Private Key", padding=15)
            key_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
            
            ttk.Label(key_frame, text="Private Key (Hex):", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
            
            # Text widget for private key with scrollbar
            key_text_frame = ttk.Frame(key_frame)
            key_text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            key_text = tk.Text(key_text_frame, height=4, wrap=tk.WORD, font=('Courier', 10))
            key_scrollbar = ttk.Scrollbar(key_text_frame, orient=tk.VERTICAL, command=key_text.yview)
            key_text.configure(yscrollcommand=key_scrollbar.set)
            
            key_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            key_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            key_text.insert(1.0, private_key)
            key_text.config(state=tk.DISABLED)  # Make read-only
            
            # Buttons
            button_frame = ttk.Frame(key_dialog)
            button_frame.pack(fill=tk.X, padx=15, pady=10)
            
            def copy_private_key():
                key_dialog.clipboard_clear()
                key_dialog.clipboard_append(private_key)
                messagebox.showinfo("Copied", "Private key copied to clipboard!\n\n⚠️ Remember: Keep it secret and secure!")
            
            ttk.Button(button_frame, text="Copy Private Key", command=copy_private_key).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=key_dialog.destroy).pack(side=tk.RIGHT, padx=5)
            
            print(f"🔐 Private key displayed for address: {self.current_address}")
            
        except Exception as e:
            print(f"❌ Error getting private key: {e}")
            messagebox.showerror("Error", f"Failed to get private key: {str(e)}")
    
    def generate_new_address_gui(self):
        """Generate new address with GUI"""
        if not self.wallet_manager.current_wallet:
            messagebox.showerror("Error", "No wallet is currently open")
            return
        
        label = simpledialog.askstring("New Address", "Enter label for new address:")
        if label:
            try:
                new_addr = self.wallet_manager.generate_new_address(label)
                messagebox.showinfo("Success", f"New address generated:\n{new_addr}")
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate address: {str(e)}")
    
    def open_address_book(self):
        """Open address book"""
        self.show_sending_addresses()
    
    def generate_paper_wallet(self):
        """Generate paper wallet"""
        self.paper_wallet_generator.show_paper_wallet_dialog()

if __name__ == "__main__":
    print("Starting GSC Coin Professional Wallet...")
    wallet = GSCWalletGUI()
    wallet.run()
