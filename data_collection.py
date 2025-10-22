import pandas as pd
import numpy as np
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# --- Step 1: Download NLTK Data ---
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    print("Vader Lexicon not found. Downloading...")
    nltk.download('vader_lexicon')

# --- Step 2: Define Parameters ---
START_DATE = '2015-01-01'
END_DATE = '2024-12-31'

# --- Step 3: Collect Data ---
print("[data_collection] Start: Fetching core market data...")
nifty_df = yf.download('^NSEI', start=START_DATE, end=END_DATE, progress=False)
vix_df = yf.download('^INDIAVIX', start=START_DATE, end=END_DATE, progress=False)
sp500_df = yf.download('^GSPC', start=START_DATE, end=END_DATE, progress=False)
usdinr_df = yf.download('INR=X', start=START_DATE, end=END_DATE, progress=False)
brent_df = yf.download('BZ=F', start=START_DATE, end=END_DATE, progress=False)

# Flatten MultiIndex columns that yfinance may produce
def _flatten_columns(df):
    if hasattr(df, 'columns') and isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[-1] if isinstance(col, tuple) else col for col in df.columns]
    return df

nifty_df = _flatten_columns(nifty_df)
vix_df = _flatten_columns(vix_df)
sp500_df = _flatten_columns(sp500_df)
usdinr_df = _flatten_columns(usdinr_df)
brent_df = _flatten_columns(brent_df)

print("[debug] nifty_df columns initially:", list(nifty_df.columns))

# If columns are unusual (e.g., all equal the ticker like '^NSEI'), try a heuristic rename
if len(nifty_df.columns) >= 5 and len(set(nifty_df.columns)) == 1:
    print(f"[debug] Detected repeated column names ({nifty_df.columns[0]}). Applying heuristic column names.")
    common = ['Open', 'High', 'Low', 'Close', 'Volume']
    # If there are more than 5 columns, keep the first five mapped to common names
    nifty_df.columns = common + list(nifty_df.columns[len(common):])
    print("[debug] Renamed nifty_df.columns ->", list(nifty_df.columns))

# --- Step 4: Get News Sentiment ---
def get_news_sentiment():
    print("Fetching and analyzing news sentiment...")
    url = "https://www.reuters.com/world/india/"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = [h.get_text() for h in soup.find_all('h3', limit=10)]
        if not headlines: return 0.0
        sia = SentimentIntensityAnalyzer()
        scores = [sia.polarity_scores(headline)['compound'] for headline in headlines]
        return np.mean(scores)
    except Exception as e:
        print(f"Could not fetch news: {e}")
        return 0.0

news_sentiment_today = get_news_sentiment()
print(f"Today's aggregated news sentiment score: {news_sentiment_today:.2f}")

# --- Step 5: Combine and Engineer Features ---
print("Combining data and engineering features...")

# Helper: find a column in a dataframe using case-insensitive and suffix matching
def _find_col(df, target):
    target_l = target.lower()
    for c in df.columns:
        c_s = str(c).lower()
        if c_s == target_l or c_s.endswith('.' + target_l) or target_l in c_s:
            return c
    return None

# Detect and rename primary OHLCV columns in nifty_df
col_map = {}
for name in ['Open', 'High', 'Low', 'Close', 'Volume']:
    found = _find_col(nifty_df, name)
    if found is None:
        # fallback: try exact match on common alternatives
        found = _find_col(nifty_df, name.lower())
    if found is None:
        print(f"Available columns in nifty_df: {list(nifty_df.columns)}")
        raise KeyError(f"Could not find required column '{name}' in nifty dataframe.")
    col_map[found] = name

# Rename the found columns to standard names
nifty_df = nifty_df.rename(columns=col_map)

# For auxiliary dataframes, find the 'Close' column name robustly
def _ensure_close(df, name):
    # If all column names are identical (yfinance oddity), try mapping first five to OHLCV
    if len(df.columns) >= 5 and len(set(df.columns)) == 1:
        print(f"[debug] Detected repeated column names in {name}. Applying heuristic column names.")
        common = ['Open', 'High', 'Low', 'Close', 'Volume']
        df.columns = common + list(df.columns[len(common):])
    # Try to find Close robustly
    c = _find_col(df, 'Close')
    if c is None:
        # fallback to first column
        c = df.columns[0]
        print(f"[debug] Falling back to first column for {name} as Close: {c}")
    return df, c

vix_df, vix_close = _ensure_close(vix_df, 'vix_df')
sp500_df, sp500_close = _ensure_close(sp500_df, 'sp500_df')
usdinr_df, usdinr_close = _ensure_close(usdinr_df, 'usdinr_df')
brent_df, brent_close = _ensure_close(brent_df, 'brent_df')

# Build working dataframe using renamed/found columns
df = nifty_df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
df['VIX_Close'] = vix_df[vix_close]
df['Log_Ret'] = np.log(df['Close'] / df['Close'].shift(1))
df['Hist_Vol_30D'] = df['Log_Ret'].rolling(window=30).std() * np.sqrt(252)
df['SP500_Ret'] = (sp500_df[sp500_close] / sp500_df[sp500_close].shift(1)) - 1
df['USDINR_Ret'] = (usdinr_df[usdinr_close] / usdinr_df[usdinr_close].shift(1)) - 1
df['Brent_Ret'] = (brent_df[brent_close] / brent_df[brent_close].shift(1)) - 1
df['News_Sentiment'] = news_sentiment_today

# Compute target similar to algorithmic_trading: future 21-day rolling vol of log returns
df['Target_Nifty_Vol'] = df['Log_Ret'].rolling(window=21).std().shift(-21) * np.sqrt(252)

# Drop rows with NaNs created by rolling/shifting
df.dropna(inplace=True)

# Ensure column names don't have a name (prevents extra header rows like 'Price' or 'Ticker')
try:
    df.columns.name = None
except Exception:
    pass

# Ensure the index name is 'Date' for a clean CSV with the date as the first column
df.index.name = 'Date'

# --- Step 6: Save the Final Dataset ---
# Add a 'Price' column (some consumers expect Price as first column) and reorder columns
df['Price'] = df['Close']
desired_order = ['Price','Open','High','Low','Close','Volume','VIX_Close',
                 'Log_Ret','Hist_Vol_30D','SP500_Ret','USDINR_Ret','Brent_Ret','News_Sentiment','Target_Nifty_Vol']
existing = [c for c in desired_order if c in df.columns]
other = [c for c in df.columns if c not in existing]
df = df[existing + other]

# Save CSV with a single header row and Date as the first column
# Reset index to ensure Date becomes a regular column
df_export = df.reset_index()
df_export.to_csv('final_nifty_volatility_dataset.csv', index=False)
print("\nFresh dataset saved to 'final_nifty_volatility_dataset.csv'")
print(f"Dataset shape: {df_export.shape}")
print(f"Columns: {list(df_export.columns)}")
print("[data_collection] Completed successfully.")
