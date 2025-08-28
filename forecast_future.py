import pandas as pd
import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt

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
    if col != 'Target_VIX': # Exclude the target column for now
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
last_known_data = features.iloc[[-1]] # Get the very last row of data
future_predictions = []

for _ in range(N_FORECAST_DAYS):
    # Predict the next day
    next_day_pred = final_model.predict(last_known_data)[0]
    future_predictions.append(next_day_pred)
    
    # --- Update the last_known_data for the next prediction ---
    # Create a new row for the next day
    new_row = last_known_data.iloc[0].copy()
    
    # We need to update the features based on our prediction.
    # For simplicity, we'll update the most direct features.
    # A more complex model would update rolling averages, etc.
    new_row['VIX_Close'] = next_day_pred # The new "known" VIX is our prediction
    
    # We can assume other features (like returns) might revert to their mean, or stay flat.
    # Here, we will keep them constant from the last day for this forecast.
    
    last_known_data = pd.DataFrame([new_row])


# --- Step 6: Create and Plot the Future Graph ---
# Create future dates for the x-axis of our plot
last_date = df.index[-1]
future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=N_FORECAST_DAYS)

# Combine historical and future data for plotting
historical_vix = df['VIX_Close']
future_vix = pd.Series(future_predictions, index=future_dates)

plt.style.use('seaborn-v0_8-darkgrid')
plt.figure(figsize=(15, 7))
plt.plot(historical_vix.index[-200:], historical_vix[-200:], label='Historical Actual VIX', color='blue')
plt.plot(future_vix.index, future_vix, label='Future Predicted VIX', color='red', linestyle='--')
plt.title('Nifty VIX: Historical Data and 30-Day Future Forecast', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('VIX Value', fontsize=12)
plt.legend()
plt.show()

print("\nForecast complete. A plot showing the future prediction has been generated.")