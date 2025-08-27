# Nifty Predict: Algorithmic Trading Model

This project implements an algorithmic trading model to predict the future volatility of the Nifty 50 index (India VIX). It uses an XGBoost Regressor to learn from historical market data and make predictions.

## 🚀 Features

- **Predictive Modeling**: Utilizes `XGBoost` to forecast the 30-day forward volatility of the Nifty 50.
- **Rich Dataset**: Incorporates a variety of financial indicators as features:
  - Nifty 50 historical data (Open, High, Low, Close, Volume)
  - Historical India VIX data
  - 30-Day Historical Volatility
  - S&P 500 Returns
  - USD/INR Exchange Rate Returns
  - Brent Crude Oil Returns
- **Model Evaluation**: Assesses model performance using standard regression metrics: Mean Squared Error (MSE), Mean Absolute Error (MAE), and R-squared (R²).
- **Visualization**: Plots the predicted VIX values against the actual values for visual comparison.

## 📂 Dataset

The model is trained on a preprocessed dataset named `final_nifty_volatility_dataset.csv`. This dataset is created by combining and cleaning the following raw data files:

- `nifty50_data.csv`: Historical data for the Nifty 50 index.
- `india_vix_data.csv`: Historical data for the India VIX (volatility index).
- Other external data sources for S&P 500, USD/INR, and Brent oil.

## 🛠️ How It Works

The core logic is contained in `algorithmic_trading.py` and follows these steps:

1.  **Data Loading**: The preprocessed dataset is loaded into a pandas DataFrame.
2.  **Data Preparation**: The data is cleaned to ensure all feature columns are numeric. It is then split into features (X) and the target variable (y, which is `Target_VIX`).
3.  **Chronological Split**: The dataset is split into training (80%) and testing (20%) sets in a chronological order to respect the time-series nature of the data.
4.  **Model Training**: An XGBoost Regressor model is trained on the training data.
5.  **Prediction**: The trained model is used to make predictions on the test set.
6.  **Evaluation**: The model's predictions are evaluated against the actual `Target_VIX` values.
7.  **Visualization**: A plot is generated to show how the model's predictions compare to the actual volatility.

## ⚙️ Getting Started

### Prerequisites

Make sure you have Python installed on your system.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/RISABH-UG26/Nifty_Predict.git
    cd Nifty_Predict
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required packages:**
    It is recommended to create a `requirements.txt` file with the following content:
    ```
    pandas
    numpy
    xgboost
    scikit-learn
    matplotlib
    ```
    Then, install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

### Usage

To run the model and see the prediction results, execute the main script:

```bash
python algorithmic_trading.py
```

The script will output the model's performance metrics to the console and display a plot comparing the predicted and actual VIX values.

## 📈 Results

The script will print the following performance metrics for the model on the test data:
- **Mean Squared Error (MSE)**
- **Mean Absolute Error (MAE)**
- **R-squared (R²)**

It will also save a plot named `nifty_vix_prediction.png` showing the comparison between the predicted and actual VIX.

## 🔮 Future Improvements

- **Hyperparameter Tuning**: Optimize the XGBoost model's performance by tuning its hyperparameters.
- **Feature Engineering**: Create new features that might improve predictive accuracy.
- **Try Different Models**: Experiment with other regression models like LSTM or Prophet, which are well-suited for time-series data.
- **Live Trading API**: Integrate the model with a brokerage API for paper trading or live trading.

