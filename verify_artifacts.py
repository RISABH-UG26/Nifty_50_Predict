#!/usr/bin/env python3
"""
Verify Script - Check all artifacts exist and provide a summary
"""
import os
import sys
from pathlib import Path

def verify_artifacts():
    """Verify that all required artifacts have been generated"""
    
    workspace = Path("c:\\Users\\Risabh\\Desktop\\Trade_algo")
    artifacts = {
        "CSV Dataset": "final_nifty_volatility_dataset.csv",
        "Strategy Performance Plot": "nifty_strategy_performance.png",
        "Price Forecast Plot": "nifty_price_forecast.png",
        "Volatility Forecast Plot": "nifty_vol_forecast.png",
    }
    
    print("=" * 70)
    print("ARTIFACT VERIFICATION REPORT")
    print("=" * 70)
    
    all_exist = True
    for name, filename in artifacts.items():
        filepath = workspace / filename
        exists = filepath.exists()
        status = "✓ EXISTS" if exists else "✗ MISSING"
        size_info = f"({filepath.stat().st_size / 1024:.1f} KB)" if exists else ""
        print(f"{name:.<35} {status:.<20} {size_info}")
        all_exist = all_exist and exists
    
    print("=" * 70)
    if all_exist:
        print("✓ ALL ARTIFACTS SUCCESSFULLY GENERATED!")
    else:
        print("✗ SOME ARTIFACTS ARE MISSING")
    print("=" * 70)
    
    return all_exist

if __name__ == "__main__":
    success = verify_artifacts()
    sys.exit(0 if success else 1)
