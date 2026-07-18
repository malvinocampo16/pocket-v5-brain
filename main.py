import os, time, requests
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz
from flask import Flask
import threading

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PAIRS = ["EURUSD","GBPUSD","USDJPY","AUDUSD","EURJPY"]

app = Flask(__name__)

@app.route('/')
def home():
    sg = datetime.now(pytz.timezone('Asia/Singapore')).strftime('%I:%M %p SGT')
    return f"V5.4 LIGHT LIVE - {sg} - FAST MONEY"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(e)

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_signal(pair):
    try:
        ticker = f"{pair[:3]}{pair[3:]}=X"
        df = yf.download(ticker, period="2d", interval="1m", progress=False, auto_adjust=True)
        if len(df) < 60: return None
        df['RSI'] = calc_rsi(df['Close'], 14)
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['STD20'] = df['Close'].rolling(20).std()
        df['BBU'] = df['SMA20'] + 2*df['STD20']
        df['BBL'] = df['SMA20'] - 2*df['STD20']
        last = df.iloc[-1]
        rsi = float(last['RSI'])
        if rsi < 45 and last['Close'] <= last['BBL'] and last['EMA20'] > last['EMA50']:
            return "CALL", rsi
        if rsi > 55 and last['Close'] >= last['BBU'] and last['EMA20'] < last['EMA50']:
            return "PUT", rsi
        return None
    except Exception as e:
        print(f"{pair} {e}")
        return None

def brain_loop():
    sg_tz = pytz.timezone('Asia/Singapore')
    time.sleep(5)
    sg_time = datetime.now(sg_tz).strftime('%I:%M %p')
    send_telegram(f"🧠 V5.4 LIGHT ONLINE - FIXED!\n✅ No more build error\n⚡ FAST MONEY 45/55\n⏰ {sg_time} SGT\n👉 Next signal in 20-40 mins")
    last_signal = 0
    while True:
        try:
            for pair in PAIRS:
                res = get_signal(pair)
                if res and time.time()-last_signal > 600:
                    sig, rsi = res
                    sg_time = datetime.now(sg_tz).strftime('%I:%M %p SGT')
                    send_telegram(f"📈 V5.4 SIGNAL {pair} {sig}\nRSI: {rsi:.1f}\nTime: {sg_time}\n💰 1% Risk - 1 Min Expiry\n👉 Pocket Option NOW")
                    last_signal = time.time()
                    time.sleep(10)
            print(f"Scan {datetime.now(sg_tz).strftime('%H:%M:%S')}")
            time.sleep(30)
        except Exception as e:
            print(e); time.sleep(30)

threading.Thread(target=brain_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
