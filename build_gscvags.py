#!/usr/bin/env python3
"""
GSC Coin Executable Builder
Creates a standalone .exe file named 'gscvags' for distribution
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_gscvags_exe():
    """Build the GSC Coin executable named 'gscvags'"""
    
    print("🚀 Building GSC Coin executable 'gscvags.exe'...")
    print("=" * 60)
    
    # Get current directory
    current_dir = Path.cwd()
    
    # Define paths
    main_script = current_dir / "run.py"
    dist_dir = current_dir / "dist"
    build_dir = current_dir / "build"
    
    # Clean previous builds safely
    try:
        if dist_dir.exists():
            print("🧹 Cleaning previous dist directory...")
            shutil.rmtree(dist_dir, ignore_errors=True)
        if build_dir.exists():
            print("🧹 Cleaning previous build directory...")
            shutil.rmtree(build_dir, ignore_errors=True)
    except Exception as e:
        print(f"⚠️ Warning: Could not clean previous builds: {e}")
        print("Continuing with build...")
    
    # PyInstaller command for creating standalone executable
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window (GUI app)
        "--name=gscvags",              # Output name
        "--icon=NONE",                 # No icon for now
        "--add-data=*.json;.",         # Include JSON files
        "--hidden-import=tkinter",     # Ensure tkinter is included
        "--hidden-import=tkinter.ttk", # Ensure ttk is included
        "--hidden-import=PIL",         # Include PIL for QR codes
        "--hidden-import=qrcode",      # Include qrcode library
        "--hidden-import=requests",    # Include requests
        "--hidden-import=threading",   # Include threading
        "--hidden-import=socket",      # Include socket
        "--hidden-import=json",        # Include json
        "--hidden-import=hashlib",     # Include hashlib
        "--hidden-import=time",        # Include time
        "--hidden-import=datetime",    # Include datetime
        "--collect-all=tkinter",       # Collect all tkinter modules
        "--collect-all=PIL",           # Collect all PIL modules
        str(main_script)
    ]
    
    print("📦 Building executable with PyInstaller...")
    print(f"Command: {' '.join(pyinstaller_cmd)}")
    print()
    
    try:
        # Run PyInstaller
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build successful!")
            
            # Check if executable was created
            exe_path = dist_dir / "gscvags.exe"
            if exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
                print(f"📁 Executable created: {exe_path}")
                print(f"📊 File size: {file_size:.2f} MB")
                
                # Create distribution info
                create_distribution_info(dist_dir)
                
                print("\n🎉 GSC Coin executable 'gscvags.exe' is ready for distribution!")
                print(f"📂 Location: {exe_path}")
                print("\n📋 Distribution Instructions:")
                print("1. Share the 'gscvags.exe' file with others")
                print("2. Recipients can run it directly - no Python installation needed")
                print("3. The executable includes all blockchain features:")
                print("   - Complete Bitcoin-like transaction system")
                print("   - Automatic peer broadcasting")
                print("   - Blockchain import/export (JSON)")
                print("   - Mining with GUI")
                print("   - P2P networking")
                
                return True
            else:
                print("❌ Executable not found after build")
                return False
        else:
            print("❌ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error during build: {e}")
        return False

def create_distribution_info(dist_dir):
    """Create distribution information file"""
    info_file = dist_dir / "README.txt"
    
    info_content = """
GSC Coin Blockchain Wallet - Standalone Executable
==================================================

File: gscvags.exe
Version: 1.0
Built: """ + str(Path.cwd()) + """

FEATURES:
---------
✅ Complete Bitcoin-like blockchain system
✅ Automatic transaction broadcasting to peers
✅ Mining with real-time visualization
✅ Blockchain import/export (JSON format)
✅ P2P networking and peer discovery
✅ Wallet management with QR codes
✅ RPC server for external integrations
✅ Real-time mempool and transaction tracking

HOW TO USE:
-----------
1. Double-click 'gscvags.exe' to launch
2. The application will start with a GUI interface
3. Create or open a wallet to begin
4. Send/receive transactions
5. Mine blocks to earn GSC coins
6. Connect to other peers for networking

SYSTEM REQUIREMENTS:
-------------------
- Windows 10/11 (64-bit)
- No Python installation required
- Internet connection for P2P networking (optional)

SHARING:
--------
This executable can be shared with anyone.
No additional files or installations needed.
All blockchain data is stored locally.

For support or questions, refer to the GSC Coin documentation.
"""
    
    with open(info_file, 'w') as f:
        f.write(info_content)
    
    print(f"📄 Created distribution info: {info_file}")

if __name__ == "__main__":
    success = build_gscvags_exe()
    if success:
        print("\n🎯 Build completed successfully!")
        input("Press Enter to exit...")
    else:
        print("\n❌ Build failed!")
        input("Press Enter to exit...")
