import os
import time
import requests
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import pytz
from flask import Flask
import threading

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TOKEN_HERE")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURJPY"]
TIMEFRAME = "1m"  # for yfinance

app = Flask(__name__)

# Keep-alive for UptimeRobot - FIXES YOUR REBOOT ISSUE
@app.route('/')
def home():
    sg_time = datetime.now(pytz.timezone('Asia/Singapore')).strftime('%Y-%m-%d %I:%M:%S %p SGT')
    return f"V5.3 FAST MONEY LIVE - {sg_time} - Scanning 5 pairs every 30s"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_signal(pair):
    try:
        # Get data from Yahoo Finance (free)
        import yfinance as yf
        ticker = f"{pair[:3]}{pair[3:]}=X"
        df = yf.download(ticker, period="2d", interval="1m", progress=False)
        if len(df) < 60:
            return None
        
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['EMA50'] = ta.ema(df['Close'], length=50)
        bb = ta.bbands(df['Close'], length=20, std=2)
        df = pd.concat([df, bb], axis=1)
        
        last = df.iloc[-1]
        rsi = last['RSI']
        
        # V5.3 FAST FILTER - looser for more signals = faster money
        # CALL: oversold + touches lower BB + uptrend
        if rsi < 45 and last['Close'] <= last['BBL_20_2.0'] and last['EMA20'] > last['EMA50']:
            return "CALL", rsi
        # PUT: overbought + touches upper BB + downtrend
        if rsi > 55 and last['Close'] >= last['BBU_20_2.0'] and last['EMA20'] < last['EMA50']:
            return "PUT", rsi
        return None
    except Exception as e:
        print(f"{pair} error: {e}")
        return None

def brain_loop():
    sg_tz = pytz.timezone('Asia/Singapore')
    # Send ONLINE once when starts
    sg_time = datetime.now(sg_tz).strftime('%I:%M %p')
    send_telegram(f"🧠 V5.3 FAST MONEY ONLINE - CLOUD\n✅ RSI 45/55 - More Signals!\n☁️ 24/7 on Render\n⏰ {sg_time} Singapore\n👉 @MalvinJojoOcampo")
    
    last_signal_time = 0
    while True:
        try:
            for pair in PAIRS:
                result = get_signal(pair)
                if result:
                    # Cooldown 10 mins to avoid spam
                    if time.time() - last_signal_time > 600:
                        signal, rsi = result
                        sg_time = datetime.now(sg_tz).strftime('%I:%M %p SGT')
                        msg = f"📈 V5.3 SIGNAL {pair} {signal}\nRSI: {rsi:.1f}\nTime: {sg_time}\n⏰ 1% Risk - 1 Min Expiry"
                        send_telegram(msg)
                        last_signal_time = time.time()
                        print(f"SIGNAL SENT: {pair} {signal}")
                        time.sleep(10)  # avoid double
            print(f"Scanning... {datetime.now(sg_tz).strftime('%H:%M:%S')} SGT")
            time.sleep(30)
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(30)

# Start brain in background thread
threading.Thread(target=brain_loop, daemon=True).start()

if __name__ == "__main__":
    # Render needs port 10000
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
