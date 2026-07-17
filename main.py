import os, threading, time, requests
from flask import Flask
from datetime import datetime
import pytz, yfinance as yf
SGT=pytz.timezone('Asia/Singapore')
BOT_TOKEN=os.getenv("BOT_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
app=Flask(__name__)
@app.route('/')
def home():
    return "V5.2 SGT LIVE"
def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML"}, timeout=10)
    except:
        pass
def get_signal(sym):
    try:
        data=yf.download(sym, period="1d", interval="1m", progress=False)
        if len(data)<50:
            return None
        close=data['Close']
        delta=close.diff()
        gain=delta.where(delta>0,0).rolling(14).mean()
        loss=-delta.where(delta<0,0).rolling(14).mean()
        rs=gain/loss
        rsi=100-(100/(1+rs))
        rsi_val=float(rsi.iloc[-1])
        ema20=close.ewm(span=20).mean().iloc[-1]
        ema50=close.ewm(span=50).mean().iloc[-1]
        sma20=close.rolling(20).mean().iloc[-1]
        std20=close.rolling(20).std().iloc[-1]
        price=float(close.iloc[-1])
        lower=sma20-2*std20
        upper=sma20+2*std20
        if rsi_val<38 and price<lower*1.001 and ema20>ema50:
            return "CALL 🟢", rsi_val
        if rsi_val>62 and price>upper*0.999 and ema20<ema50:
            return "PUT 🔴", rsi_val
    except:
        return None
def brain_loop():
    now=datetime.now(SGT).strftime('%H:%M:%S')
    send_telegram(f"🧠 <b>V5.2 ONLINE - {now} SGT</b>\n\n✅ Singapore Time\n✅ Real Filter\n⏰ {now} Singapore")
    pairs={"EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"JPY=X","AUD/USD":"AUDUSD=X","EUR/JPY":"EURJPY=X"}
    while True:
        for name, ysym in pairs.items():
            res=get_signal(ysym)
            if res:
                direction,rsi=res
                now=datetime.now(SGT).strftime('%H:%M:%S')
                msg=f"📈 <b>V5.2 SIGNAL {now} SGT</b>\n\n💱 {name}\n📊 {direction}\n📉 RSI:{rsi:.1f}\n⏰ {now} Singapore"
                send_telegram(msg)
                time.sleep(120)
        time.sleep(30)
threading.Thread(target=brain_loop, daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
