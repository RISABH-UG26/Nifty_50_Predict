import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt

# --- Step 1: Load the Preprocessed Dataset ---
print("Loading the dataset...")
try:
    df = pd.read_csv('final_nifty_volatility_dataset.csv', index_col=0, parse_dates=True)
except FileNotFoundError:
    print("Error: 'final_nifty_volatility_dataset.csv' not found.")
    print("Please run the data collection script first.")
    exit()

# --- NEW: Step 1.5: Ensure all data is numeric ---
# This is the fix for the ValueError.
# It will convert columns to numbers and turn any errors into NaN (which are then dropped).
print("Ensuring all feature columns are numeric...")
for col in ['Open', 'High', 'Low', 'Close', 'Volume', 'VIX_Close', 'Hist_Vol_30D', 'SP500_Ret', 'USDINR_Ret', 'Brent_Ret']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop any rows that might have missing values after conversion
df.dropna(inplace=True)


# --- Step 2: Prepare Data for the Model ---
print("Preparing data for the model...")

# Define the features (X) and the target (y)
features = df.drop(['Target_VIX', 'Log_Ret'], axis=1)
target = df['Target_VIX']

# Chronological split for time-series data (80% train, 20% test)
split_index = int(len(features) * 0.8)
X_train, X_test = features[:split_index], features[split_index:]
y_train, y_test = target[:split_index], target[split_index:]

print(f"Training data shape: {X_train.shape}")
print(f"Testing data shape: {X_test.shape}")


# --- Step 3: Model Training (XGBoost) ---
print("\nTraining the XGBoost model...")

# Initialize the XGBoost Regressor
xgb_model = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=5,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

# Train the model
xgb_model.fit(X_train, y_train)

# --- Step 4: Model Evaluation ---
print("\nEvaluating the model...")

# Make predictions on the test set
predictions = xgb_model.predict(X_test)

# Calculate performance metrics
rmse = np.sqrt(mean_squared_error(y_test, predictions))
mae = mean_absolute_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")
print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"R-squared (R²): {r2:.2f}")

# Feature Importance
feature_importance = pd.DataFrame({
    'Feature': features.columns,
    'Importance': xgb_model.feature_importances_
}).sort_values('Importance', ascending=False)

print("\nTop 10 Most Important Features:")
print(feature_importance.head(10))


# --- Step 5: Visualize the Results ---
plt.style.use('seaborn-v0_8-darkgrid')
plt.figure(figsize=(15, 7))
plt.plot(y_test.index, y_test, label='Actual VIX', color='blue', alpha=0.7)
plt.plot(y_test.index, predictions, label='Predicted VIX', color='orange', linestyle='--')
plt.title('Nifty VIX Prediction: Actual vs. Predicted', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('VIX Value', fontsize=12)
plt.legend()
plt.show()

# --- Step 6: Simple Backtesting of a Volatility Strategy ---
print("\nRunning a simple backtest...")

# Create a new DataFrame for the backtest results
backtest_df = pd.DataFrame(index=y_test.index)
backtest_df['Actual_VIX'] = y_test
backtest_df['Predicted_VIX'] = predictions
backtest_df['Nifty_Return'] = df['Log_Ret'].loc[y_test.index]

# Strategy
backtest_df['VIX_MA10'] = backtest_df['Actual_VIX'].rolling(window=10).mean()
backtest_df['Signal'] = np.where(backtest_df['Predicted_VIX'] < backtest_df['VIX_MA10'], 1, 0)
backtest_df['Strategy_Return'] = backtest_df['Signal'] * backtest_df['Nifty_Return']

# Calculate cumulative returns
backtest_df['Buy_and_Hold_Cumulative'] = np.exp(backtest_df['Nifty_Return'].cumsum())
backtest_df['Strategy_Cumulative'] = np.exp(backtest_df['Strategy_Return'].cumsum())

# Plot backtest results
plt.figure(figsize=(15, 7))
plt.plot(backtest_df.index, backtest_df['Buy_and_Hold_Cumulative'], label='Nifty Buy and Hold')
plt.plot(backtest_df.index, backtest_df['Strategy_Cumulative'], label='Volatility Strategy')
plt.title('Backtest: Volatility-Based Strategy vs. Buy and Hold', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Cumulative Returns', fontsize=12)
plt.legend()
plt.show()

print("\nBacktest complete. Check the generated plots.")