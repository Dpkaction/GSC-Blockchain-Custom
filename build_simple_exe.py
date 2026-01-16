"""
Simple GSC.exe Builder
Creates standalone GSC.exe executable with fixed build process
"""

import os
import sys
import subprocess
import shutil

def build_gsc_exe():
    """Build GSC.exe using PyInstaller with simple approach"""
    
    print("Building GSC Coin Executable...")
    print("=" * 40)
    
    # Install PyInstaller if needed
    try:
        import PyInstaller
        print("PyInstaller found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed")
    
    # Create simple main file
    main_content = '''#!/usr/bin/env python3
"""GSC Coin Standalone Application"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from gsc_wallet_gui import GSCWalletGUI
    
    def main():
        print("Starting GSC Coin...")
        gui = GSCWalletGUI()
        gui.root.mainloop()
    
    if __name__ == "__main__":
        main()
        
except Exception as e:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("GSC Coin Error", f"Failed to start GSC Coin: {e}")
    sys.exit(1)
'''
    
    # Write main file
    with open("gsc_main_simple.py", "w", encoding="utf-8") as f:
        f.write(main_content)
    
    print("Created main application file")
    
    # Build with PyInstaller using simple command
    print("Building executable...")
    
    try:
        # Simple PyInstaller command
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed", 
            "--name", "gsc",
            "--add-data", "*.py;.",
            "--add-data", "mainnet;mainnet",
            "--hidden-import", "tkinter",
            "--hidden-import", "tkinter.ttk",
            "--hidden-import", "tkinter.messagebox",
            "--hidden-import", "threading",
            "--hidden-import", "json",
            "--hidden-import", "hashlib",
            "--hidden-import", "time",
            "--hidden-import", "socket",
            "--hidden-import", "datetime",
            "gsc_main_simple.py"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("GSC.exe built successfully!")
            
            # Check if exe exists
            exe_path = os.path.join("dist", "gsc.exe")
            if os.path.exists(exe_path):
                file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
                print(f"Executable: {exe_path}")
                print(f"Size: {file_size:.1f} MB")
                
                # Create distribution folder
                dist_folder = "GSC_Distribution"
                if os.path.exists(dist_folder):
                    shutil.rmtree(dist_folder)
                os.makedirs(dist_folder)
                
                # Copy executable
                shutil.copy2(exe_path, os.path.join(dist_folder, "gsc.exe"))
                
                # Create simple README
                readme = """GSC Coin - Cryptocurrency Wallet

QUICK START:
1. Double-click gsc.exe to launch
2. Create or open a wallet
3. Start mining or send transactions

FEATURES:
- Smart mining (only mines when transactions available)
- Real-time mempool synchronization
- Secure wallet management
- P2P networking
- 2-minute block times
- 4-year halving cycles

NETWORK PARAMETERS:
- Block Time: 2 minutes
- Block Reward: 50 GSC
- Mining Difficulty: Fixed at 5
- Transaction Fee: 0.1 GSC minimum
- Total Supply: 21.75 trillion GSC

For support: https://gsccoin.network
Version: 1.0.0 Mainnet
"""
                
                with open(os.path.join(dist_folder, "README.txt"), "w") as f:
                    f.write(readme)
                
                print(f"Distribution ready: {dist_folder}/")
                print("GSC.exe is ready for sharing!")
                
                return True
            else:
                print("Executable not found after build")
                return False
        else:
            print("Build failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"Build error: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            if os.path.exists("gsc_main_simple.py"):
                os.remove("gsc_main_simple.py")
            if os.path.exists("build"):
                shutil.rmtree("build")
            if os.path.exists("gsc.spec"):
                os.remove("gsc.spec")
        except:
            pass

if __name__ == "__main__":
    success = build_gsc_exe()
    if success:
        print("\nSUCCESS: GSC.exe created and ready for distribution!")
    else:
        print("\nFAILED: Could not create GSC.exe")
