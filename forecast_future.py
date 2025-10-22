import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

print("Loading the dataset...")
try:
    # Load CSV with Date as the first column (not index)
    df = pd.read_csv('final_nifty_volatility_dataset.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
except FileNotFoundError:
    print("Error: 'final_nifty_volatility_dataset.csv' not found.")
    print("Please run 'data_collection.py' first to generate the data.")
    exit()
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit()

# --- Step 2: Ensure Data is Numeric ---
print("Preparing and cleaning data...")
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df.dropna(inplace=True)

# Define features (X) and target (y)
# We use price-related features for forecasting
features_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
target_col = 'Close'  # We'll predict the closing price

X = df[features_cols]
y = df[target_col]

# --- Step 3: Scale Data ---
print("Scaling data...")
# We use two separate scalers for features and target
# This makes inverse transforming the target (our price prediction) much easier
scaler_X = MinMaxScaler(feature_range=(0, 1))
X_scaled = scaler_X.fit_transform(X)

scaler_y = MinMaxScaler(feature_range=(0, 1))
y_scaled = scaler_y.fit_transform(y.values.reshape(-1, 1))

# --- Step 4: Create Time Sequences for LSTM ---
# This function transforms our flat data into sequences [samples, timesteps, features]
def create_sequences(X, y, look_back=60):
    Xs, ys = [], []
    for i in range(len(X) - look_back):
        Xs.append(X[i:(i + look_back)])
        ys.append(y[i + look_back])
    return np.array(Xs), np.array(ys)

LOOK_BACK_WINDOW = 60 # Look back 60 trading days (approx 3 months)
X_seq, y_seq = create_sequences(X_scaled, y_scaled, LOOK_BACK_WINDOW)

# --- Step 5: Split into Training and Test Sets ---
# It's CRITICAL to split time-series data chronologically
split_index = int(len(X_seq) * 0.8)
X_train, X_test = X_seq[:split_index], X_seq[split_index:]
y_train, y_test = y_seq[:split_index], y_seq[split_index:]

print(f"Total samples: {len(X_seq)}")
print(f"Training data shape: {X_train.shape}")
print(f"Testing data shape: {X_test.shape}")

# --- Step 6: Build the LSTM Model ---
print("\nBuilding the stacked LSTM model...")
# Based on the model from the GitHub repo, but adding Dropout for regularization
model = Sequential()
model.add(LSTM(units=64, return_sequences=True, input_shape=(LOOK_BACK_WINDOW, X_train.shape[2])))
model.add(Dropout(0.2))
model.add(LSTM(units=64, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(units=1)) # Output layer for a single prediction

model.compile(optimizer='adam', loss='mse')
model.summary()

# --- Step 7: Train the LSTM Model ---
print("\nTraining the LSTM model...")
# EarlyStopping prevents overfitting and stops training when validation loss stops improving
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

history = model.fit(
    X_train, y_train,
    epochs=100,
    batch_size=32,
    validation_split=0.1, # Use 10% of training data for validation
    callbacks=[early_stopping],
    verbose=1
)
print("Model training complete.")

# --- Step 8: Make Predictions on Test Set ---
print("\nRunning model on test set...")
y_pred_scaled = model.predict(X_test)

# Inverse transform the predictions and actuals to their original Nifty price scale
y_pred = scaler_y.inverse_transform(y_pred_scaled)
y_test_actual = scaler_y.inverse_transform(y_test)

# --- Step 9: The "Novelty" - Backtesting the Strategy ---
print("Backtesting trading strategy...")

# Get the dates that correspond to our test set
test_dates = df.index[split_index + LOOK_BACK_WINDOW:]

# Get the *actual* Nifty closing prices for our test period
# We need the 'Close' column, not the 'Target_Nifty_Close' for this
actual_prices = df['Close'].iloc[split_index + LOOK_BACK_WINDOW:]

# Create a DataFrame for our backtest
backtest_df = pd.DataFrame(index=test_dates)
backtest_df['Actual_Close'] = actual_prices
backtest_df['Predicted_Close'] = y_pred

# --- Define the Trading Strategy ---
# Signal 1 = BUY (predict tomorrow's price is higher than today's)
# Signal 0 = SELL/HOLD (predict tomorrow's price is lower than today's)
backtest_df['Signal'] = np.where(backtest_df['Predicted_Close'] > backtest_df['Actual_Close'].shift(1), 1, 0)
# We shift signals by 1 day because a prediction for 'tomorrow' is made based on 'today's' data
backtest_df['Signal'] = backtest_df['Signal'].shift(1).fillna(0).astype(int)

# --- Simulate the Portfolio ---
INITIAL_CASH = 100000.0
cash = INITIAL_CASH
shares = 0
portfolio_values = []

for date, row in backtest_df.iterrows():
    price_today = row['Actual_Close']
    signal_today = row['Signal']
    
    if signal_today == 1 and cash > 0:
        # BUY signal and we have cash
        shares_to_buy = cash / price_today
        shares += shares_to_buy
        cash = 0
    elif signal_today == 0 and shares > 0:
        # SELL signal and we have shares
        cash_from_sale = shares * price_today
        cash += cash_from_sale
        shares = 0
        
    # Calculate total portfolio value for the day
    portfolio_value = cash + (shares * price_today)
    portfolio_values.append(portfolio_value)

backtest_df['Strategy_Portfolio'] = portfolio_values

# --- Calculate "Buy and Hold" Benchmark ---
buy_hold_shares = INITIAL_CASH / backtest_df['Actual_Close'].iloc[0]
backtest_df['Buy_Hold_Portfolio'] = buy_hold_shares * backtest_df['Actual_Close']

# --- Step 10: Plot the "Accurate Curves" (Backtest Results) ---
print("\nGenerating strategy performance plot...")
plt.style.use('seaborn-v0_8-darkgrid')
plt.figure(figsize=(18, 9))

plt.plot(backtest_df['Strategy_Portfolio'], label='LSTM Strategy Portfolio', color='red')
plt.plot(backtest_df['Buy_Hold_Portfolio'], label='"Buy and Hold" Strategy (Benchmark)', color='blue')

# Format Y-axis to show currency (Rupees)
formatter = mticker.FormatStrFormatter('INR %.0f')
plt.gca().yaxis.set_major_formatter(formatter)

plt.title('Nifty 50 LSTM Strategy Performance', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Portfolio Value (INR)', fontsize=12)
plt.legend(fontsize=12)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

# Save the plot instead of showing it
plt.savefig('nifty_strategy_performance.png')
print("\nPlot saved as 'nifty_strategy_performance.png'")

# --- Final Performance ---
final_strategy_value = backtest_df['Strategy_Portfolio'].iloc[-1]
final_buy_hold_value = backtest_df['Buy_Hold_Portfolio'].iloc[-1]
strategy_return = (final_strategy_value / INITIAL_CASH - 1) * 100
buy_hold_return = (final_buy_hold_value / INITIAL_CASH - 1) * 100

print("\n--- Backtest Results ---")
print(f"Initial Portfolio Value: INR {INITIAL_CASH:,.2f}")
print(f"Final LSTM Strategy Value: INR {final_strategy_value:,.2f} ({strategy_return:+.2f}%)")
print(f"Final Buy and Hold Value: INR {final_buy_hold_value:,.2f} ({buy_hold_return:+.2f}%)")

if final_strategy_value > final_buy_hold_value:
    print("\nResult: The LSTM strategy outperformed the 'Buy and Hold' benchmark.")
else:
    print("\nResult: The 'Buy and Hold' benchmark outperformed the LSTM strategy.")
