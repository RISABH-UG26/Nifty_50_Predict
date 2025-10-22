import os
import subprocess
import shlex

proj_root = os.path.dirname(__file__)
python = os.path.join(proj_root, '.venv', 'Scripts', 'python.exe')

scripts = ['algorithmic_trading.py', 'data_collection.py', 'forecast_future.py']
artifacts = ['final_nifty_volatility_dataset.csv', 'nifty_vol_forecast.png']

# Run each script with a timeout to avoid hangs and print captured output.
for s in scripts:
    script_path = os.path.join(proj_root, s)
    print(f"\n--- Running {s} (timeout 300s) ---")
    try:
        res = subprocess.run([python, script_path], capture_output=True, text=True, timeout=300)
        if res.stdout:
            print("STDOUT:\n", res.stdout)
        if res.stderr:
            print("STDERR:\n", res.stderr)
        if res.returncode != 0:
            print(f"{s} failed with return code {res.returncode}")
            raise SystemExit(1)
    except subprocess.TimeoutExpired:
        print(f"{s} timed out after 300 seconds and was terminated.")
        raise

print("\nChecking artifacts...")
missing = []
for a in artifacts:
    path = os.path.join(proj_root, a)
    if not os.path.exists(path):
        missing.append(a)
    else:
        print(f"Found {a} ({os.path.getsize(path)} bytes)")

if missing:
    raise FileNotFoundError(f"Expected artifact(s) not found: {', '.join(missing)}")

print("Smoke tests passed.")
