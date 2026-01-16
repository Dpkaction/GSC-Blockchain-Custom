@echo off
title GSC Coin Wallet
echo Starting GSC Coin Wallet...
echo.
cd /d "%~dp0"
python gsc_wallet_gui.py
if errorlevel 1 (
    echo.
    echo Error starting wallet!
    echo Make sure Python and required modules are installed.
    pause
)
