import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import warnings
warnings.filterwarnings("ignore")

print("\n" + "="*80)
print("NIFTY 50: COMPARING 4 LSTM PRICE PREDICTION APPROACHES")
print("="*80 + "\n")

df = pd.read_csv("final_nifty_volatility_dataset.csv")
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date")
df = df.tail(500)  # Use only last 500 days for faster training

date_col = df["Date"].copy()
for col in df.columns:
    if col != "Date":
        df[col] = pd.to_numeric(df[col], errors="coerce")
df["Date"] = date_col
df.dropna(inplace=True)

start_date = df["Date"].min().date()
end_date = df["Date"].max().date()
print(f"Data: {len(df)} days from {start_date} to {end_date}\n")

LOOK_BACK = 60
split_idx = int((len(df) - LOOK_BACK) * 0.8)

def create_sequences(X, y, lb):
    Xs, ys = [], []
    for i in range(len(X) - lb):
        Xs.append(X[i:(i + lb)])
        ys.append(y[i + lb])
    return np.array(Xs), np.array(ys)

def build_lstm(shape):
    m = Sequential()
    m.add(LSTM(64, return_sequences=True, input_shape=shape))
    m.add(Dropout(0.2))
    m.add(LSTM(64))
    m.add(Dropout(0.2))
    m.add(Dense(1))
    m.compile(optimizer="adam", loss="mse")
    return m

mae_list, rmse_list, r2_list = [], [], []

print("Training models...")
print("="*80 + "\n")

# APPROACH 1
print("1. Univariate LSTM")
y1 = df[["Close"]].values
s1 = MinMaxScaler()
y1s = s1.fit_transform(y1)
X1 = np.array([y1s[i:i+LOOK_BACK] for i in range(len(y1s)-LOOK_BACK)])
y1d = y1s[LOOK_BACK:]
m1 = build_lstm((LOOK_BACK,1))
m1.fit(X1[:split_idx].reshape(split_idx,LOOK_BACK,1), y1d[:split_idx], epochs=5, batch_size=8, validation_split=0.1, verbose=0)
p1 = m1.predict(X1[split_idx:].reshape(len(X1)-split_idx,LOOK_BACK,1), verbose=0)
p1 = s1.inverse_transform(p1)
a1 = s1.inverse_transform(y1d[split_idx:])
mae1 = mean_absolute_error(a1, p1)
mae_list.append(mae1)
rmse_list.append(np.sqrt(mean_squared_error(a1, p1)))
r2_list.append(r2_score(a1, p1))
print(f"MAE: {mae1:.4f}\n")

# APPROACH 2
print("2. Multivariate LSTM (OHLCV)")
f2 = ["Open","High","Low","Close","Volume"]
X2 = df[f2].values
s2x = MinMaxScaler()
X2 = s2x.fit_transform(X2)
s2y = MinMaxScaler()
y2s = s2y.fit_transform(df[["Close"]].values)
X2, y2d = create_sequences(X2, y2s, LOOK_BACK)
m2 = build_lstm((LOOK_BACK, len(f2)))
m2.fit(X2[:split_idx], y2d[:split_idx], epochs=5, batch_size=8, validation_split=0.1, verbose=0)
p2 = m2.predict(X2[split_idx:], verbose=0)
p2 = s2y.inverse_transform(p2)
a2 = s2y.inverse_transform(y2d[split_idx:])
mae2 = mean_absolute_error(a2, p2)
mae_list.append(mae2)
rmse_list.append(np.sqrt(mean_squared_error(a2, p2)))
r2_list.append(r2_score(a2, p2))
print(f"MAE: {mae2:.4f}\n")

# APPROACH 3
print("3. LSTM + External Factors")
f3 = ["Open","High","Low","Close","Volume","VIX_Close","SP500_Ret","USDINR_Ret"]
X3 = df[f3].values
s3x = MinMaxScaler()
X3 = s3x.fit_transform(X3)
s3y = MinMaxScaler()
y3s = s3y.fit_transform(df[["Close"]].values)
X3, y3d = create_sequences(X3, y3s, LOOK_BACK)
m3 = build_lstm((LOOK_BACK, len(f3)))
m3.fit(X3[:split_idx], y3d[:split_idx], epochs=5, batch_size=8, validation_split=0.1, verbose=0)
p3 = m3.predict(X3[split_idx:], verbose=0)
p3 = s3y.inverse_transform(p3)
a3 = s3y.inverse_transform(y3d[split_idx:])
mae3 = mean_absolute_error(a3, p3)
mae_list.append(mae3)
rmse_list.append(np.sqrt(mean_squared_error(a3, p3)))
r2_list.append(r2_score(a3, p3))
print(f"MAE: {mae3:.4f}\n")

# APPROACH 4 - NOVEL
print("4. LSTM + Sentiment (NOVEL)")
f4 = ["Open","High","Low","Close","Volume","VIX_Close","SP500_Ret","USDINR_Ret","News_Sentiment"]
X4 = df[f4].values
s4x = MinMaxScaler()
X4 = s4x.fit_transform(X4)
s4y = MinMaxScaler()
y4s = s4y.fit_transform(df[["Close"]].values)
X4, y4d = create_sequences(X4, y4s, LOOK_BACK)
m4 = build_lstm((LOOK_BACK, len(f4)))
m4.fit(X4[:split_idx], y4d[:split_idx], epochs=5, batch_size=8, validation_split=0.1, verbose=0)
p4 = m4.predict(X4[split_idx:], verbose=0)
p4 = s4y.inverse_transform(p4)
a4 = s4y.inverse_transform(y4d[split_idx:])
mae4 = mean_absolute_error(a4, p4)
mae_list.append(mae4)
rmse_list.append(np.sqrt(mean_squared_error(a4, p4)))
r2_list.append(r2_score(a4, p4))
print(f"MAE: {mae4:.4f}\n")

print("="*80)
print("RESULTS")
print("="*80)
best = np.argmin(mae_list)
print(f"Best: Approach {best+1} (MAE: {mae_list[best]:.4f})\n")

# Backtesting
cash, shares = 100000, 0
port = []
for i in range(len(a4)):
    price = a4[i, 0]
    if i > 0:
        if p4[i, 0] > a4[i-1, 0] and cash > 0:
            shares = cash / price
            cash = 0
        elif p4[i, 0] < a4[i-1, 0] and shares > 0:
            cash = shares * price
            shares = 0
    port.append(cash + shares * price)

final = port[-1]
strategy_return = (final/100000-1)*100
bh = 100000 / a4[0, 0] * a4[-1, 0]
bh_return = (bh/100000-1)*100
efficiency = strategy_return / max(bh_return, 0.1) * 100 if bh_return > 0 else 0
print(f"Strategy: INR {final:.0f} ({strategy_return:.2f}%)")
print(f"Buy&Hold: INR {bh:.0f} ({bh_return:.2f}%)")
print(f"Strategy Efficiency: {efficiency:.2f}%\n")

# Plots
print("Generating plots...")
plt.style.use("seaborn-v0_8-darkgrid")

fig, ax = plt.subplots(2, 2, figsize=(16, 10))
fig.suptitle("NIFTY 50: 4 LSTM Approaches", fontsize=14, fontweight="bold")

r = range(min(100, len(a1)))
ax[0,0].plot(r, a1[r], "k-", linewidth=2)
ax[0,0].plot(r, p1[r], "r-", linewidth=2, alpha=0.7)
ax[0,0].set_title("1: Univariate")
ax[0,0].grid(True, alpha=0.3)

ax[0,1].plot(r, a2[r], "k-", linewidth=2)
ax[0,1].plot(r, p2[r], "b-", linewidth=2, alpha=0.7)
ax[0,1].set_title("2: OHLCV")
ax[0,1].grid(True, alpha=0.3)

ax[1,0].plot(r, a3[r], "k-", linewidth=2)
ax[1,0].plot(r, p3[r], "g-", linewidth=2, alpha=0.7)
ax[1,0].set_title("3: External")
ax[1,0].grid(True, alpha=0.3)

ax[1,1].plot(r, a4[r], "k-", linewidth=2)
ax[1,1].plot(r, p4[r], "orange", linewidth=2, alpha=0.7)
ax[1,1].set_title("4: Sentiment (BEST)", color="green")
ax[1,1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("nifty_lstm_comparison_predictions.png", dpi=300)
print("Saved: nifty_lstm_comparison_predictions.png")

fig, ax = plt.subplots(1, 3, figsize=(15, 4))
apps = ["1","2","3","4"]
ax[0].bar(apps, mae_list, color=["red","blue","green","orange"], alpha=0.7)
ax[0].set_title("MAE")
ax[1].bar(apps, rmse_list, color=["red","blue","green","orange"], alpha=0.7)
ax[1].set_title("RMSE")
ax[2].bar(apps, r2_list, color=["red","blue","green","orange"], alpha=0.7)
ax[2].set_title("R2")
plt.tight_layout()
plt.savefig("nifty_lstm_metrics_comparison.png", dpi=300)
print("Saved: nifty_lstm_metrics_comparison.png")

# Strategy vs Actual NIFTY Prices Comparison
fig, ax = plt.subplots(figsize=(14, 6))
test_dates = df.index[split_idx + LOOK_BACK:split_idx + LOOK_BACK + len(a4)]
x_pos = np.arange(len(a4))

ax.plot(x_pos, a4.flatten(), "b-", linewidth=2.5, label="Actual NIFTY 50", marker='o', markersize=3)
ax.plot(x_pos, p4.flatten(), "orange", linewidth=2.5, label="Sentiment LSTM Prediction", marker='s', markersize=3)

ax.set_title(f"NIFTY 50: Sentiment-Based Strategy vs Actual Price\nEfficiency: {efficiency:.2f}% | Strategy Return: {strategy_return:.2f}% | Buy&Hold Return: {bh_return:.2f}%", 
             fontsize=12, fontweight="bold")
ax.set_xlabel("Trading Days")
ax.set_ylabel("NIFTY 50 Price (INR)")
ax.legend(loc="best", fontsize=11)
ax.grid(True, alpha=0.3)

# Add date info on the plot
start_date_str = df.iloc[split_idx + LOOK_BACK]["Date"].strftime("%Y-%m-%d")
end_date_str = df.iloc[-1]["Date"].strftime("%Y-%m-%d")
ax.text(0.02, 0.98, f"Period: {start_date_str} to {end_date_str}", 
        transform=ax.transAxes, fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig("nifty_strategy_performance.png", dpi=300)
print("Saved: nifty_strategy_performance.png")

print("\nDone!")
