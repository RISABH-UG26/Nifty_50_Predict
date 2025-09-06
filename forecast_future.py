import pandas as pd
import numpy as np
import xgboost as xgb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


print("Loading the dataset...")
try:
    # Try reading with Date as index first
    df = pd.read_csv('final_nifty_volatility_dataset.csv', index_col='Date', parse_dates=True)
except Exception:
    # Fallback: read without index and try to detect a date-like first column
    try:
        df = pd.read_csv('final_nifty_volatility_dataset.csv')
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df.set_index('Date', inplace=True)
        else:
            # assume first column is date
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            df.set_index(df.columns[0], inplace=True)
    except FileNotFoundError:
        print("Error: 'final_nifty_volatility_dataset.csv' not found.")
        print("Please run the data collection script first.")
        raise

print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

print("Ensuring all feature columns are numeric (coercing where needed)...")
for col in df.columns:
    if col != 'Target_Nifty_Vol':
        df[col] = pd.to_numeric(df[col], errors='coerce')
df.dropna(inplace=True)

if df.empty:
    raise ValueError('Dataframe is empty after cleaning. Check CSV for proper numeric columns and non-null Target_Nifty_Vol')

print("Preparing data for the final model...")
# Detect target column from common names
possible_target_names = ['Target_Nifty_Vol', 'Target_VIX', 'Target_Vol', 'Target']
target_col = None
for name in possible_target_names:
    if name in df.columns:
        target_col = name
        break

if target_col is None:
    raise KeyError(f"None of the expected target columns found. Tried: {possible_target_names}. Available columns: {list(df.columns)}")

print(f"Using target column: {target_col}")
cols_to_drop = [target_col]
if 'Log_Ret' in df.columns:
    cols_to_drop.append('Log_Ret')
features = df.drop(cols_to_drop, axis=1)
target = df[target_col]

print("Training the final XGBoost model on all historical data...")
final_model = xgb.XGBRegressor(
    objective='reg:squarederror', n_estimators=1000, learning_rate=0.05,
    max_depth=5, subsample=0.8, colsample_bytree=0.8,
    random_state=42, n_jobs=-1
)
final_model.fit(features, target)
print("Model training complete.")

print("\nGenerating future forecast...")
N_FORECAST_DAYS = 30
last_known_data = features.iloc[[-1]]
future_predictions = []

for _ in range(N_FORECAST_DAYS):
    next_day_pred = final_model.predict(last_known_data)[0]
    future_predictions.append(next_day_pred)
    
    new_row = last_known_data.iloc[0].copy()
    new_row['Hist_Vol_30D'] = next_day_pred
    last_known_data = pd.DataFrame([new_row])

last_date = df.index[-1]
future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=N_FORECAST_DAYS)

historical_vol = df['Hist_Vol_30D'][-200:]
future_vol = pd.Series(future_predictions, index=future_dates)

plt.style.use('seaborn-v0_8-darkgrid')
plt.figure(figsize=(15, 7))

plt.plot(historical_vol.index, historical_vol, label='Historical Nifty Volatility', color='blue')
plt.plot(future_vol.index, future_vol, label='Future Predicted Volatility', color='red', linestyle='--')

ax = plt.gca()
ax.xaxis.set_major_locator(mticker.MaxNLocator(10)) 
plt.xticks(rotation=45, ha="right")

plt.title('Nifty 50: Historical and 30-Day Future Volatility Forecast', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Annualized Volatility', fontsize=12)
plt.legend()
plt.tight_layout()
out_path = 'nifty_vol_forecast.png'
plt.savefig(out_path)
print(f"Plot saved to {out_path}")

print("\nForecast complete. A plot showing the future Nifty 50 volatility has been generated.")