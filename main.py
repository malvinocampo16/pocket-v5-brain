import os, ccxt, time, requests, pandas as pd, threading
from datetime import datetime
from flask import Flask
import pytz

TOKEN = os.getenv("BOT_TOKEN", "8221875653:AAFa3YLy1ER9Cna8FEWDlDiBgUcJtlo38e0")
CHAT_ID = os.getenv("CHAT_ID", "165525623")
TIMEZONE = "Asia/Singapore"
SYMBOLS = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","EUR/JPY","GBP/JPY","AUD/JPY","EUR/GBP","USD/CAD"]

app = Flask(__name__)

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def super_brain_score(df):
    if len(df) < 60: return None
    c = df['c']; h = df['h']; l = df['l']
    close = c.iloc[-1]
    ema9 = c.ewm(span=9).mean().iloc[-1]
    ema21 = c.ewm(span=21).mean().iloc[-1]
    ema50 = c.ewm(span=50).mean().iloc[-1]
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/(loss+1e-9)))
    rsi_now = rsi.iloc[-1]
    ema12 = c.ewm(span=12).mean()
    ema26 = c.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    macd_hist = (macd - signal).iloc[-1]
    sma20 = c.rolling(20).mean().iloc[-1]
    std20 = c.rolling(20).std().iloc[-1]
    bb_upper = sma20 + 2*std20
    bb_lower = sma20 - 2*std20
    lowest_low = l.rolling(14).min().iloc[-1]
    highest_high = h.rolling(14).max().iloc[-1]
    stoch = 100 * ((close - lowest_low) / (highest_high - lowest_low + 1e-9))
    score = 0
    if ema9 > ema21 > ema50: score += 25
    if 52 < rsi_now < 68: score += 20
    if macd_hist > 0: score += 20
    if sma20 < close < bb_upper: score += 15
    if 30 < stoch < 75: score += 20
    if score >= 82: return f"BUY ⬆️ CALL", score, rsi_now, stoch
    score_s = 0
    if ema9 < ema21 < ema50: score_s += 25
    if 34 < rsi_now < 48: score_s += 20
    if macd_hist < 0: score_s += 20
    if bb_lower < close < sma20: score_s += 15
    if 25 < stoch < 70: score_s += 20
    if score_s >= 82: return f"SELL ⬇️ PUT", score_s, rsi_now, stoch
    return None

def bot_loop():
    tz = pytz.timezone(TIMEZONE)
    ex = ccxt.binance()
    send(f"🧠 *V5 SUPER BRAIN ONLINE - CLOUD*\n\n✅ 5-Filter 82%+\n☁️ 24/7 on Render\n⏰ Singapore\n@Malvin_Jojo_Ocampo")
    while True:
        try:
            for sym in SYMBOLS:
                try:
                    bars = ex.fetch_ohlcv("BTC/USDT", "1m", limit=100)
                    df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
                    res = super_brain_score(df)
                    if res:
                        direction, score, rsi, stoch = res
                        now = datetime.now(tz).strftime('%H:%M:%S')
                        msg = f"🔥 *V5 {score:.0f}%*\n\nPair: `{sym}`\nSignal: *{direction}*\nRSI: {rsi:.1f}\nTime: {now} SGT\nExpiry: 2-3 min\n@Malvin_Jojo_Ocampo"
                        send(msg)
                        time.sleep(120)
                except: continue
            time.sleep(30)
        except: time.sleep(10)

@app.route("/")
def home(): return "V5 BOT ALIVE"

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
