import os
import yfinance as yf
import pandas as pd
import time as t
from zoneinfo import ZoneInfo
from datetime import datetime, time
import requests
import warnings
Admin=os.getenv('AdminId')
CHAT=os.getenv('CHAT_ID')
BOT_TOKEN = os.getenv('BOT_TOKEN')
warnings.filterwarnings("ignore")
def send_telegram_message(msg,CHAT_ID =CHAT):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        send_telegram_message("Telegram error:",Admin)
        
class VolumeSpikeScanner:

    def __init__(self):

        self.VOLUME_SPIKE = 7
        self.SCAN_INTERVAL = 60
        self.MARKET_OPEN = time(9, 15)
        self.MARKET_CLOSE = time(15, 30)

        self.link = "https://drive.google.com/file/d/1h0-lm2PR2JeZqR1hn5ua-zqQeuyKg6dw/view?usp=drivesdk"
        self.linkid = self.link.split("/")[-2]
        self.stockurl = f"https://drive.google.com/uc?export=download&id={self.linkid}"

        self.printed = set()
        self.df = None
        self.stocks_list = []

    def is_market_open(self):
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        return self.MARKET_OPEN <= now.time() <= self.MARKET_CLOSE

    def get_weekly_average(self):
        print("Updating weekly averages...")
        send_telegram_message("Updating Weekly Averages...")

        df = pd.read_csv(self.stockurl)
        stocks = (df["Symbol "] + ".NS").to_list()

        data = yf.download(
            stocks,
            period="7d",
            interval="1d",
            group_by="ticker",
            progress=True,
            threads=True
        )

        rows = []
        for s in stocks:
            try:
                if not data[s].empty:
                    rows.append({
                        "Symbol_NS": s,
                        "weekly_avg": int(data[s]["Volume"].mean())
                    })
            except Exception:
                continue

        self.df = pd.DataFrame(rows)
        self.stocks_list = self.df["Symbol_NS"].to_list()

        print("Weekly averages updated")
        send_telegram_message("Weekly Averages Updated ✅")

    def start_scanner(self):   
        send_telegram_message(f"Programm started {datetime.now(ZoneInfo('Asia/Kolkata')).time()}",Admin)
        self.printed.clear()
        print("Bot got to Online")
        send_telegram_message("Bot got to Online")
        self.get_weekly_average()
        print("🚀 Market Scanner Online")
        send_telegram_message("🚀 Market Scanner Online")

        while self.is_market_open():
            send_telegram_message(f"Stocks downloading intiated\n{datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%H:%M:%S')}",Admin)
            try:
                data = yf.download(
                    self.stocks_list,
                    period="1d",
                    interval="1m",
                    group_by="ticker",
                    progress=False,
                    threads=True
                )
                send_telegram_message(f"stocks dowloaded\n{datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%H:%M:%S')\n\nscaning",Admin}

                for stock in self.stocks_list:
                    try:
                        current_vol = data[stock]["Volume"].sum()
                        avg_vol = self.df.loc[
                            self.df["Symbol_NS"] == stock, "weekly_avg"
                        ].values[0]
                        if stock in self.printed:
                          if current_vol // self.printed[stock]+2>= avg_vol :
                            change_pct = ((current_vol - avg_vol) / avg_vol) * 100
                            msg = (
                                f"🔥 Realerting Stock incresed 2 spike\n\n"
                                f"Ticker: {stock.replace('.NS','')}\n"
                                f"Current Vol: {int(current_vol):,}\n"
                                f"Avg Vol: {int(avg_vol):,}\n"
                                f"Increase: {change_pct:.2f}%\n"
                                f"Time: {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%H:%M:%S')}\n\n"
                                f"https://charting.nseindia.com/?symbol={stock}-EQ"
                            )

                            print(msg)
                            send_telegram_message(msg)
                            self.printed[stock]=self.printed[stock]+2
                            continue

                        if current_vol // self.VOLUME_SPIKE >= avg_vol :
                            change_pct = ((current_vol - avg_vol) / avg_vol) * 100

                            msg = (
                                f"🔥 Volume Spike Alert\n\n"
                                f"Ticker: {stock.replace('.NS','')}\n"
                                f"Current Vol: {int(current_vol):,}\n"
                                f"Avg Vol: {int(avg_vol):,}\n"
                                f"Increase: {change_pct:.2f}%\n"
                                f"Time: {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%H:%M:%S')}\n\n"
                                f"https://charting.nseindia.com/?symbol={stock}-EQ"
                            )

                            print(msg)
                            send_telegram_message(msg)
                            self.printed[stock]=self.VOLUME_SPIKE

                    except Exception:
                        send_telegram_message(f"Stock Error:{stock}",Admin)
                        continue

                t.sleep(self.SCAN_INTERVAL)

            except Exception as e:
                send_telegram_message(f"Scanner error:{e}",Admin)
                t.sleep(30)
                continue

        send_telegram_message(f"📴 Market Closed Time: {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%H:%M:%S')}")
        print("Market closed")

def main():
    scanner = VolumeSpikeScanner()
    scanner.start_scanner()

if __name__ == "__main__":
    main()
