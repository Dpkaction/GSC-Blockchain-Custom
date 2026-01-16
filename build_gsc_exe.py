"""
GSC Coin Executable Builder
Creates standalone GSC.exe for distribution
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_gsc_exe():
    """Create standalone GSC.exe executable"""
    
    print("🔨 Building GSC Coin Executable")
    print("=" * 40)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")
    
    # Create main GSC application file
    main_app_content = '''
"""
GSC Coin - Standalone Application
Complete cryptocurrency wallet and node
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from blockchain import GSCBlockchain, Transaction
    from wallet_manager import WalletManager
    from network import GSCNetworkNode
    from gsc_wallet_gui import GSCWalletGUI
    
    # Import mainnet components if available
    try:
        from mainnet.mainnet_blockchain import MainnetBlockchain
        from mainnet.mainnet_network import MainnetNetworkNode
        from mainnet.mainnet_wallet import MainnetWalletManager
        from mainnet.mempool_sync import MempoolSyncManager, SmartMiner
        from mainnet.config import MainnetConfig
        MAINNET_AVAILABLE = True
    except ImportError:
        MAINNET_AVAILABLE = False
        
except ImportError as e:
    messagebox.showerror("Import Error", f"Failed to import GSC components: {e}")
    sys.exit(1)

class GSCApplication:
    """Main GSC Coin Application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide root window initially
        
        # Show splash screen
        self.show_splash_screen()
        
        # Initialize components
        self.blockchain = None
        self.network = None
        self.wallet_manager = None
        self.mempool_sync = None
        self.smart_miner = None
        self.gui = None
        
        # Setup
        self.setup_application()
    
    def show_splash_screen(self):
        """Show GSC Coin splash screen"""
        splash = tk.Toplevel()
        splash.title("GSC Coin")
        splash.geometry("400x300")
        splash.resizable(False, False)
        
        # Center the splash screen
        splash.update_idletasks()
        x = (splash.winfo_screenwidth() // 2) - (400 // 2)
        y = (splash.winfo_screenheight() // 2) - (300 // 2)
        splash.geometry(f"400x300+{x}+{y}")
        
        # Splash content
        tk.Label(splash, text="GSC COIN", font=("Arial", 24, "bold"), fg="#2e7d32").pack(pady=30)
        tk.Label(splash, text="Professional Cryptocurrency", font=("Arial", 12)).pack()
        tk.Label(splash, text="Wallet & Mining Node", font=("Arial", 12)).pack()
        
        # Version info
        version_text = "v1.0.0"
        if MAINNET_AVAILABLE:
            version_text += " (Mainnet Ready)"
        tk.Label(splash, text=version_text, font=("Arial", 10)).pack(pady=10)
        
        # Loading message
        self.loading_label = tk.Label(splash, text="Initializing...", font=("Arial", 10))
        self.loading_label.pack(pady=20)
        
        # Progress bar simulation
        progress_frame = tk.Frame(splash)
        progress_frame.pack(pady=10)
        
        self.progress_canvas = tk.Canvas(progress_frame, width=300, height=20, bg="white")
        self.progress_canvas.pack()
        
        # Close splash after 3 seconds
        splash.after(3000, splash.destroy)
        splash.update()
        
        # Simulate loading
        for i in range(101):
            self.progress_canvas.delete("all")
            self.progress_canvas.create_rectangle(0, 0, i*3, 20, fill="#2e7d32", outline="")
            if i < 30:
                self.loading_label.config(text="Loading blockchain...")
            elif i < 60:
                self.loading_label.config(text="Initializing network...")
            elif i < 90:
                self.loading_label.config(text="Starting wallet...")
            else:
                self.loading_label.config(text="Ready!")
            
            splash.update()
            time.sleep(0.02)
    
    def setup_application(self):
        """Setup GSC application components"""
        try:
            if MAINNET_AVAILABLE:
                # Use mainnet components
                self.blockchain = MainnetBlockchain()
                self.network = MainnetNetworkNode(self.blockchain)
                self.wallet_manager = MainnetWalletManager()
                
                # Initialize mempool sync and smart mining
                self.mempool_sync = MempoolSyncManager(self.blockchain, self.network)
                self.smart_miner = SmartMiner(self.blockchain, self.network, self.mempool_sync)
                
                print("✅ Mainnet components initialized")
            else:
                # Use legacy components
                self.blockchain = GSCBlockchain()
                self.network = GSCNetworkNode(self.blockchain)
                self.wallet_manager = WalletManager()
                
                print("✅ Legacy components initialized")
            
            # Start network
            self.network.start()
            
            # Start mempool sync if available
            if self.mempool_sync:
                self.mempool_sync.start()
            
            # Create GUI
            self.gui = GSCWalletGUI(self.blockchain, self.network)
            
            # Add smart mining integration to GUI if available
            if self.smart_miner:
                self.integrate_smart_mining()
            
            print("✅ GSC Coin application ready")
            
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize GSC Coin: {e}")
            sys.exit(1)
    
    def integrate_smart_mining(self):
        """Integrate smart mining with GUI"""
        if not self.gui or not self.smart_miner:
            return
        
        # Override the mining toggle function
        original_toggle_mining = self.gui.toggle_mining
        
        def smart_toggle_mining():
            if not self.smart_miner.is_mining:
                # Get mining address
                mining_address = self.gui.miner_address_var.get()
                if not mining_address or mining_address == "Enter mining address":
                    messagebox.showerror("Mining Error", "Please enter a valid mining address")
                    return
                
                # Start smart mining
                self.smart_miner.start_mining(mining_address)
                self.gui.mining_button.config(text="Stop Smart Mining")
                self.gui.mining_status.config(text="Status: Smart Mining (waiting for transactions)")
            else:
                # Stop smart mining
                self.smart_miner.stop_mining()
                self.gui.mining_button.config(text="Start Smart Mining")
                self.gui.mining_status.config(text="Status: Idle")
        
        # Replace the mining function
        self.gui.toggle_mining = smart_toggle_mining
        
        # Update mining button text
        self.gui.mining_button.config(text="Start Smart Mining")
        
        print("✅ Smart mining integrated with GUI")
    
    def run(self):
        """Run the GSC application"""
        try:
            # Show main window
            self.root.deiconify()
            
            # Start GUI main loop
            self.gui.root.mainloop()
            
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
            messagebox.showerror("Runtime Error", f"GSC Coin error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown GSC application"""
        print("🛑 Shutting down GSC Coin...")
        
        if self.smart_miner:
            self.smart_miner.stop_mining()
        
        if self.mempool_sync:
            self.mempool_sync.stop()
        
        if self.network:
            self.network.stop()
        
        if self.blockchain:
            self.blockchain.save_blockchain()
        
        print("✅ GSC Coin shutdown complete")

def main():
    """Main entry point"""
    print("🚀 Starting GSC Coin...")
    
    app = GSCApplication()
    app.run()

if __name__ == "__main__":
    main()
'''
    
    # Write main application file
    with open("gsc_main.py", "w", encoding="utf-8") as f:
        f.write(main_app_content)
    
    print("✅ Created main application file")
    
    # Create PyInstaller spec file
    spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gsc_main.py'],
    pathex=['{os.getcwd()}'],
    binaries=[],
    datas=[
        ('mainnet', 'mainnet'),
        ('*.py', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        'tkinter.simpledialog',
        'threading',
        'time',
        'json',
        'hashlib',
        'socket',
        'datetime',
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.asymmetric',
        'cryptography.hazmat.primitives.asymmetric.rsa',
        'cryptography.hazmat.primitives.asymmetric.padding',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.primitives.serialization',
        'flask',
        'flask_cors',
        'flask_limiter',
        'prometheus_client',
        'psutil',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='gsc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='gsc_icon.ico' if os.path.exists('gsc_icon.ico') else None,
)
'''
    
    with open("gsc.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("✅ Created PyInstaller spec file")
    
    # Create icon file if it doesn't exist
    if not os.path.exists("gsc_icon.ico"):
        print("⚠️ No icon file found, creating placeholder")
        # You can add icon creation here or use a default one
    
    # Build the executable
    print("🔨 Building executable...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--onefile", 
            "--windowed",
            "--name", "gsc",
            "gsc.spec"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ GSC.exe built successfully!")
            
            # Check if exe exists
            exe_path = os.path.join("dist", "gsc.exe")
            if os.path.exists(exe_path):
                file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
                print(f"📁 Executable location: {exe_path}")
                print(f"📊 File size: {file_size:.1f} MB")
                
                # Create distribution folder
                dist_folder = "GSC_Coin_Distribution"
                if os.path.exists(dist_folder):
                    shutil.rmtree(dist_folder)
                os.makedirs(dist_folder)
                
                # Copy executable
                shutil.copy2(exe_path, os.path.join(dist_folder, "gsc.exe"))
                
                # Create README for distribution
                readme_content = '''# GSC Coin - Cryptocurrency Wallet & Node

## Quick Start
1. Double-click `gsc.exe` to launch GSC Coin
2. Create a new wallet or open an existing one
3. Start mining or send/receive transactions
4. Connect to the GSC network automatically

## Features
- Professional cryptocurrency wallet
- Built-in mining with smart transaction-based mining
- P2P networking with automatic peer discovery
- Real-time mempool synchronization
- Secure wallet encryption
- Transaction history and blockchain explorer

## System Requirements
- Windows 10 or later
- 4GB RAM minimum
- 1GB free disk space
- Internet connection for network sync

## Network Parameters
- Block Time: 2 minutes
- Block Reward: 50 GSC (halving every 4 years)
- Mining Difficulty: Fixed at 5 (4 leading zeros)
- Transaction Fee: Minimum 0.1 GSC
- Total Supply: 21.75 trillion GSC

## Support
For support and updates, visit: https://gsccoin.network

## Version
GSC Coin v1.0.0 - Mainnet Ready
Built with enhanced mempool synchronization and smart mining.
'''
                
                with open(os.path.join(dist_folder, "README.txt"), "w", encoding="utf-8") as f:
                    f.write(readme_content)
                
                print(f"✅ Distribution package created: {dist_folder}/")
                print("📦 Ready for distribution!")
                
            else:
                print("❌ Executable not found after build")
        else:
            print("❌ Build failed:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Build error: {e}")
    
    # Cleanup
    try:
        if os.path.exists("gsc_main.py"):
            os.remove("gsc_main.py")
        if os.path.exists("gsc.spec"):
            os.remove("gsc.spec")
        if os.path.exists("build"):
            shutil.rmtree("build")
    except:
        pass
    
    print("🎉 GSC.exe build process complete!")

if __name__ == "__main__":
    create_gsc_exe()
