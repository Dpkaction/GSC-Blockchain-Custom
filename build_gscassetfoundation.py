#!/usr/bin/env python3
"""
Build script for GSC Asset Foundation executable
Publisher: ztesarbd
"""

import os
import sys
import subprocess

def build_executable():
    """Build the GSC Asset Foundation executable with proper metadata"""
    
    print("🔨 Building GSC Asset Foundation executable...")
    print("📋 Publisher: ztesarbd")
    print("📦 Name: gscassetfoundation.exe")
    
    # PyInstaller command with all necessary options
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window
        "--name", "gscassetfoundation", # Executable name
        "--version-file", "version_info.txt",  # Version information with publisher
        "--add-data", "*.py;.",         # Include all Python files
        "--hidden-import", "tkinter",   # Ensure tkinter is included
        "--hidden-import", "requests",  # Ensure requests is included
        "--hidden-import", "qrcode",    # Ensure qrcode is included
        "--hidden-import", "PIL",       # Ensure PIL is included
        "--hidden-import", "cryptography", # Ensure cryptography is included
        "--icon", "NONE",               # No icon for now
        "gsc_wallet_gui.py"             # Main script
    ]
    
    try:
        print("⚙️ Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Build completed successfully!")
        print(f"📁 Executable location: dist/gscassetfoundation.exe")
        print(f"👤 Publisher: ztesarbd")
        print(f"📋 Product: GSC Asset Foundation")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error code: {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = build_executable()
    if success:
        print("\n🎉 GSC Asset Foundation executable built successfully!")
        print("📦 File: gscassetfoundation.exe")
        print("👤 Publisher: ztesarbd")
    else:
        print("\n💥 Build failed!")
        sys.exit(1)
