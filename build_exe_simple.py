#!/usr/bin/env python3
"""
Simple GSC Wallet Build Script
Creates standalone executable using PyInstaller
"""

import os
import sys
import subprocess

def build_exe():
    """Build executable using PyInstaller"""
    print("🪙 Building GSC Wallet executable...")
    
    # Install PyInstaller if not available
    try:
        import PyInstaller
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed", 
        "--name=GSC_Wallet",
        "--add-data=blockchain_improved.py;.",
        "--add-data=network_improved.py;.",
        "--add-data=wallet_manager.py;.",
        "--add-data=gsc_logger.py;.",
        "--add-data=thread_safety.py;.",
        "--add-data=gsc_simple_console.py;.",
        "gsc_wallet_enhanced.py"
    ]
    
    print("🔨 Running build command...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build completed successfully!")
            print(f"📁 Executable created: dist/GSC_Wallet.exe")
            
            # Check if file exists
            if os.path.exists("dist/GSC_Wallet.exe"):
                size = os.path.getsize("dist/GSC_Wallet.exe")
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

def create_launcher():
    """Create simple launcher script"""
    launcher_content = '''
@echo off
title GSC Coin Wallet
echo Starting GSC Coin Wallet...
echo.
if exist "dist\\GSC_Wallet.exe" (
    echo ✅ Found executable
    start "" "dist\\GSC_Wallet.exe"
) else (
    echo ❌ Executable not found!
    echo Please run build_exe.py first
    pause
)
'''
    
    with open("run_wallet.bat", 'w') as f:
        f.write(launcher_content)
    
    print("✅ Created launcher: run_wallet.bat")

def main():
    """Main build process"""
    print("🪙 GSC Coin Wallet Build Script")
    print("=" * 50)
    
    # Build executable
    if build_exe():
        # Create launcher
        create_launcher()
        
        print("\n🎉 Build completed!")
        print("\n📋 To run the wallet:")
        print("1. Use run_wallet.bat (recommended)")
        print("2. Or run dist/GSC_Wallet.exe directly")
        print("\n📦 Executable: dist/GSC_Wallet.exe")
        print("🚀 Launcher: run_wallet.bat")
    else:
        print("\n❌ Build failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()
