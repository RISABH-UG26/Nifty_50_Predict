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
print("Fetching core market data...")
nifty_df = yf.download('^NSEI', start=START_DATE, end=END_DATE, progress=False)
vix_df = yf.download('^INDIAVIX', start=START_DATE, end=END_DATE, progress=False)
sp500_df = yf.download('^GSPC', start=START_DATE, end=END_DATE, progress=False)
usdinr_df = yf.download('INR=X', start=START_DATE, end=END_DATE, progress=False)
brent_df = yf.download('BZ=F', start=START_DATE, end=END_DATE, progress=False)

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
df = nifty_df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
df['VIX_Close'] = vix_df['Close']
df['Log_Ret'] = np.log(df['Close'] / df['Close'].shift(1))
df['Hist_Vol_30D'] = df['Log_Ret'].rolling(window=30).std() * np.sqrt(252)
df['SP500_Ret'] = (sp500_df['Close'] / sp500_df['Close'].shift(1)) - 1
df['USDINR_Ret'] = (usdinr_df['Close'] / usdinr_df['Close'].shift(1)) - 1
df['Brent_Ret'] = (brent_df['Close'] / brent_df['Close'].shift(1)) - 1
df['News_Sentiment'] = news_sentiment_today
df['Target_VIX'] = df['VIX_Close'].shift(-1)
df.dropna(inplace=True)

# --- Step 6: Save the Final Dataset ---
df.to_csv('final_nifty_volatility_dataset.csv')
print("\nFresh dataset saved to 'final_nifty_volatility_dataset.csv'")
