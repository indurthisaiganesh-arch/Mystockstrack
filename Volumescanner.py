import os
import yfinance as yf
import pandas as pd
import time as t
from zoneinfo import ZoneInfo
from datetime import datetime, time
import requests
import warnings
import pyotp
from smartapi import SmartConnect

API_KEY = os.getenv('API_KEY')
TOTP_SECRET = os.getenv('TOTP_SECRET')
CLIENT_CODE = os.getenv('CLIENT_CODE')
PASSWORD = os.getenv('PASSWORD')
ADMIN = os.getenv('ADMINID')
CHAT = os.getenv('CHAT_ID')
BOT_TOKEN = os.getenv('BOT_TOKEN')

warnings.filterwarnings("ignore")

def time_now():
    return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%H:%M:%S")

def send_telegram_message(msg, CHAT_ID=CHAT):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception:
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={"chat_id": ADMIN, "text": "Telegram error"},
                timeout=10
            )
        except Exception:
            pass

send_telegram_message(f"Program started {time_now()}", ADMIN)

class VolumeSpikeScanner:

    def __init__(self):
        self.VOLUME_SPIKE = 7
        self.REALERT_STEP = 2
        self.SCAN_INTERVAL = 60
        self.MARKET_OPEN = time(9, 15)
        self.MARKET_CLOSE = time(15, 20)
        self.printed = {}
        self.df = None
        self.weekly_averages = None
        self.tokens_list = []
        self.chunked_tokens = []

    def chunk_list(self, lst, size=50):
        for i in range(0, len(lst), size):
            yield lst[i:i + size]

    def is_market_open(self):
        now = datetime.now(ZoneInfo("Asia/Kolkata")).time()
        return self.MARKET_OPEN <= now <= self.MARKET_CLOSE

    def get_weekly_average(self):
        send_telegram_message("Updating Weekly Averages...")
        stocks = self.df['yfinsymbol'].tolist()
        data = yf.download(
            stocks,
            period="7d",
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False
        )
        rows = []
        for s in stocks:
            try:
                if not data[s].empty:
                    rows.append({
                        "Symbol": s.replace(".NS", ""),
                        "weekly_avg": int(data[s]["Volume"].mean())
                    })
            except Exception:
                continue
        self.weekly_averages = pd.DataFrame(rows)
        send_telegram_message("Weekly Averages Updated ✅")

    def login(self):
        obj = SmartConnect(api_key=API_KEY)
        totp = pyotp.TOTP(TOTP_SECRET).now()
        session=obj.generateSession(CLIENT_CODE, PASSWORD, totp)
        send_telegram_message(f"angel one status:{session.get('status')}",ADMIN)
        return obj

    def start_scanner(self):
        send_telegram_message("Bot got to Online")
        obj = self.login()
        self.df = pd.read_csv("Master.csv")
        self.tokens_list = self.df['tokens'].tolist()
        self.chunked_tokens = list(self.chunk_list(self.tokens_list))
        self.get_weekly_average()
        send_telegram_message("🚀 Market Scanner Online")
        

        while self.is_market_open():
            try:
                send_telegram_message(f"Stocks downloading intiated\n{time_now()}",ADMIN)
                for chunk in self.chunked_tokens:
                    res = obj.getMarketData(
                        mode="FULL",
                        exchangeTokens={"NSE": chunk}
                    )
                    if not res or "data" not in res or "fetched" not in res["data"]:
                        continue
                    for stock in res["data"]["fetched"]:
                        live_vol = stock["tradeVolume"]
                        symbol = stock["tradeSymbol"].replace("-EQ", "")

                        avg_row = self.weekly_averages[
                            self.weekly_averages["Symbol"] == symbol
                        ]
                        if avg_row.empty: continue

                        avg_vol = avg_row["weekly_avg"].values[0]

                        threshold = self.VOLUME_SPIKE
                        if symbol in self.printed:
                            threshold = self.printed[symbol] + self.REALERT_STEP

                        if live_vol >= avg_vol * threshold:
                            send_telegram_message(
                                f"🔥 Volume Spike Alert * {threshold} *\n\n"
                                f"Ticker: {symbol}\n"
                                f"Current Vol: {int(live_vol):,}\n"
                                f"Avg Vol: {int(avg_vol):,}\n"
                                f"Time: {time_now()}\n\n"
                                f"https://charting.nseindia.com/?symbol={symbol}-EQ"
                            )
                            self.printed[symbol] = threshold

                    t.sleep(0.4)
            except Exception as e:
                send_telegram_message(f"Error: {e}", ADMIN)
                t.sleep(self.SCAN_INTERVAL)
                obj = self.login()

            send_telegram_message(f"Stocks downloaded scanned\n{time_now()}",ADMIN)
            t.sleep(self.SCAN_INTERVAL)
        send_telegram_message("Market Closed")
        send_telegram_message("Market Closed", ADMIN)
        send_telegram_message("🚀 Market Scanner Offline", ADMIN)

def main():
    VolumeSpikeScanner().start_scanner()

if __name__ == "__main__":
    main()
    
