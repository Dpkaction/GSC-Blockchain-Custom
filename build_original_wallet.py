#!/usr/bin/env python3
"""
Build Script for Original GSC Wallet GUI
Creates standalone executable for the original working GUI
"""

import os
import sys
import subprocess

def build_original_wallet():
    """Build the original wallet GUI executable"""
    print("🪙 Building Original GSC Wallet executable...")
    
    # Install PyInstaller if not available
    try:
        import PyInstaller
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build command for original GUI
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed", 
        "--name=GSC_Wallet_Original",
        "--add-data=blockchain.py;.",
        "--add-data=wallet_manager.py;.",
        "--add-data=paper_wallet_generator.py;.",
        "--add-data=network.py;.",
        "--add-data=gsc_simple_console.py;.",
        "gsc_wallet_gui.py"
    ]
    
    print("🔨 Running build command...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build completed successfully!")
            print(f"📁 Executable created: dist/GSC_Wallet_Original.exe")
            
            # Check if file exists
            if os.path.exists("dist/GSC_Wallet_Original.exe"):
                size = os.path.getsize("dist/GSC_Wallet_Original.exe")
                print(f"📊 File size: {size:,} bytes")
            
            return True
        else:
            print("❌ Build failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def create_original_launcher():
    """Create launcher for original wallet"""
    launcher_content = '''
@echo off
title GSC Coin Wallet - Original
echo Starting GSC Coin Wallet (Original)...
echo.
if exist "dist\\GSC_Wallet_Original.exe" (
    echo ✅ Found executable
    start "" "dist\\GSC_Wallet_Original.exe"
) else (
    echo ❌ Executable not found!
    echo Please run build_original_wallet.py first
    pause
)
'''
    
    with open("run_original_wallet.bat", 'w') as f:
        f.write(launcher_content)
    
    print("✅ Created launcher: run_original_wallet.bat")

def main():
    """Main build process"""
    print("🪙 GSC Coin Original Wallet Build Script")
    print("=" * 50)
    
    # Build executable
    if build_original_wallet():
        # Create launcher
        create_original_launcher()
        
        print("\n🎉 Build completed!")
        print("\n📋 To run the original wallet:")
        print("1. Use run_original_wallet.bat (recommended)")
        print("2. Or run dist/GSC_Wallet_Original.exe directly")
        print("\n📦 Executable: dist/GSC_Wallet_Original.exe")
        print("🚀 Launcher: run_original_wallet.bat")
    else:
        print("\n❌ Build failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()
