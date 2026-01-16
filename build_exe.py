#!/usr/bin/env python3
"""
GSC Wallet Build Script
Creates standalone executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import PyInstaller
        print("✅ PyInstaller found")
        return True
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def create_spec_file():
    """Create PyInstaller spec file"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gsc_wallet_enhanced.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'blockchain_improved',
        'network_improved', 
        'wallet_manager',
        'gsc_logger',
        'thread_safety',
        'rpc_server_improved'
    ],
    hookspath=[],
    hooksconfig={},
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
    name='GSC_Wallet',
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
    
    with open('gsc_wallet.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created PyInstaller spec file")

def build_executable():
    """Build the executable"""
    print("🔨 Building GSC Wallet executable...")
    
    try:
        # Run PyInstaller
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller', 
            '--onefile', 
            '--windowed',
            '--name=GSC_Wallet',
            '--add-data=blockchain_improved.py;.',
            '--add-data=network_improved.py;.',
            '--add-data=wallet_manager.py;.',
            '--add-data=gsc_logger.py;.',
            '--add-data=thread_safety.py;.',
            '--add-data=gsc_simple_console.py;.',
            'gsc_wallet_enhanced.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build completed successfully!")
            return True
        else:
            print(f"❌ Build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def create_installer():
    """Create simple installer script"""
    installer_content = '''
@echo off
echo Installing GSC Coin Wallet...
echo.
echo Creating installation directory...
if not exist "%PROGRAMFILES%\\GSC_Coin" mkdir "%PROGRAMFILES%\\GSC_Coin"

echo Copying files...
copy "GSC_Wallet.exe" "%PROGRAMFILES%\\GSC_Coin\\" /Y
copy "*.py" "%PROGRAMFILES%\\GSC_Coin\\" /Y 2>nul
copy "*.json" "%PROGRAMFILES%\\GSC_Coin\\" /Y 2>nul
copy "*.md" "%PROGRAMFILES%\\GSC_Coin\\" /Y 2>nul

echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%PROGRAMDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\GSC Wallet.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\\GSC_Coin\\GSC_Wallet.exe'; $Shortcut.Save()"

echo Creating start menu entry...
copy "%PROGRAMDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\GSC Wallet.lnk" "%USERPROFILE%\\Desktop\\GSC Wallet.lnk" 2>nul

echo.
echo ✅ GSC Coin Wallet installed successfully!
echo You can now run GSC Wallet from the Start Menu or Desktop.
echo.
pause
'''
    
    with open('install.bat', 'w') as f:
        f.write(installer_content)
    
    print("✅ Created installer script: install.bat")

def create_portable_package():
    """Create portable package"""
    print("📦 Creating portable package...")
    
    portable_dir = Path("GSC_Wallet_Portable")
    portable_dir.mkdir(exist_ok=True)
    
    # Copy executable
    if os.path.exists("dist/GSC_Wallet.exe"):
        shutil.copy("dist/GSC_Wallet.exe", portable_dir / "GSC_Wallet.exe")
        print("✅ Copied executable")
    
    # Copy essential files
    essential_files = [
        'blockchain_improved.py',
        'network_improved.py',
        'wallet_manager.py',
        'gsc_logger.py',
        'thread_safety.py',
        'gsc_simple_console.py',
        'gsc_wallet_enhanced.py',
        'README.md',
        'CONSOLE_GUIDE.md',
        'SECURITY_REPORT.md'
    ]
    
    for file in essential_files:
        if os.path.exists(file):
            shutil.copy(file, portable_dir / file)
            print(f"✅ Copied {file}")
    
    # Create launcher script
    launcher_content = '''
@echo off
cd /d "%~dp0"
echo Starting GSC Coin Wallet...
GSC_Wallet.exe
'''
    
    with open(portable_dir / "Start_GSC_Wallet.bat", 'w') as f:
        f.write(launcher_content)
    
    print("✅ Created portable package")
    
    # Create ZIP
    shutil.make_archive("GSC_Wallet_Portable", 'zip', portable_dir)
    print("✅ Created portable ZIP archive")

def main():
    """Main build process"""
    print("🪙 GSC Coin Wallet Build Script")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Failed to install dependencies")
        return
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    if not build_executable():
        print("❌ Build failed")
        return
    
    # Create installer
    create_installer()
    
    # Create portable package
    create_portable_package()
    
    print("\n🎉 Build completed successfully!")
    print("\n📁 Created files:")
    print("  - dist/GSC_Wallet.exe (Main executable)")
    print("  - install.bat (Installer script)")
    print("  - GSC_Wallet_Portable.zip (Portable package)")
    print("\n🚀 Ready to distribute!")

if __name__ == "__main__":
    main()
