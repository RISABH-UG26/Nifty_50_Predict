import pandas as pd
import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# --- Step 1: Load the Dataset ---
print("Loading the dataset...")
try:
    df = pd.read_csv('final_nifty_volatility_dataset.csv', index_col=0, parse_dates=True)
except FileNotFoundError:
    print("Error: 'final_nifty_volatility_dataset.csv' not found.")
    print("Please run the data collection script first.")
    exit()

# --- Step 2: Ensure Data is Numeric ---
print("Ensuring all feature columns are numeric...")
for col in df.columns:
    if col != 'Target_VIX':
        df[col] = pd.to_numeric(df[col], errors='coerce')
df.dropna(inplace=True)

# --- Step 3: Prepare Data for Final Model Training ---
print("Preparing data for the final model...")
features = df.drop(['Target_VIX', 'Log_Ret'], axis=1)
target = df['Target_VIX']

# --- Step 4: Train the Model on ALL Available Data ---
print("Training the final XGBoost model on all historical data...")
final_model = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=5,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)
final_model.fit(features, target)
print("Model training complete.")

# --- Step 5: Generate Future Predictions ---
print("\nGenerating future forecast...")
N_FORECAST_DAYS = 30
last_known_data = features.iloc[[-1]]
future_predictions = []

for _ in range(N_FORECAST_DAYS):
    next_day_pred = final_model.predict(last_known_data)[0]
    future_predictions.append(next_day_pred)
    
    new_row = last_known_data.iloc[0].copy()
    new_row['VIX_Close'] = next_day_pred
    
    last_known_data = pd.DataFrame([new_row])

# --- Step 6: Create and Plot the Future Graph ---
historical_vix = df['VIX_Close'][-200:]
future_vix = pd.Series(future_predictions)

# **THE FIX: Create simple numerical ranges for plotting**
historical_x = np.arange(len(historical_vix))
future_x = np.arange(len(historical_vix), len(historical_vix) + N_FORECAST_DAYS)

plt.style.use('seaborn-v0_8-darkgrid')
plt.figure(figsize=(15, 7))

# Plot data using the numerical index
plt.plot(historical_x, historical_vix.values, label='Historical Actual VIX', color='blue')
plt.plot(future_x, future_vix.values, label='Future Predicted VIX', color='red', linestyle='--')

# Manually add a few date labels to the x-axis for context
all_dates = pd.date_range(start=historical_vix.index[0], periods=len(historical_x) + len(future_x))
tick_positions = np.linspace(0, len(historical_x) + len(future_x) - 1, 10, dtype=int)
tick_labels = [all_dates[i].strftime('%Y-%m-%d') for i in tick_positions]

plt.xticks(ticks=tick_positions, labels=tick_labels, rotation=45, ha="right")

plt.title('Nifty VIX: Historical Data and 30-Day Future Forecast', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('VIX Value', fontsize=12)
plt.legend()
plt.tight_layout() # Adjust layout to make sure everything fits
plt.show()

print("\nForecast complete. A plot showing the future prediction has been generated.")