import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Function to scrape live trading data
def scrape_live_trading():
    try:
        url = "https://www.sharesansar.com/live-trading"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        rows = soup.find_all("tr")
        data = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                data.append({
                    "Symbol": cells[1].text.strip(),
                    "LTP": cells[2].text.strip().replace(",", ""),
                    "Change%": cells[4].text.strip(),
                    "Day High": cells[6].text.strip().replace(",", ""),
                    "Day Low": cells[7].text.strip().replace(",", ""),
                    "Previous Close": cells[9].text.strip().replace(",", ""),
                    "Volume": cells[8].text.strip().replace(",", "")
                })
        return data
    except Exception as e:
        print(f"Error scraping live trading data: {e}")
        return []

# Function to scrape today's share price
def scrape_today_share_price():
    try:
        url = "https://www.sharesansar.com/today-share-price"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        rows = soup.find_all("tr")
        data = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                data.append({
                    "SN": cells[0].text.strip(),
                    "Symbol": cells[1].text.strip(),
                    "Turnover": cells[10].text.strip().replace(",", ""),
                    "52 Week High": cells[19].text.strip().replace(",", ""),
                    "52 Week Low": cells[20].text.strip().replace(",", "")
                })
        return data
    except Exception as e:
        print(f"Error scraping today's share price: {e}")
        return []

# Function to merge live and today's data
def merge_data(live_data, today_data):
    merged = []
    today_dict = {item["Symbol"]: item for item in today_data}
    for live in live_data:
        symbol = live["Symbol"]
        if symbol in today_dict:
            today = today_dict[symbol]
            high = today["52 Week High"]
            low = today["52 Week Low"]
            ltp = live["LTP"]
            down_from_high = (float(high) - float(ltp)) / float(high) * 100 if high != "N/A" and ltp != "N/A" else "N/A"
            up_from_low = (float(ltp) - float(low)) / float(low) * 100 if low != "N/A" and ltp != "N/A" else "N/A"
            merged.append({
                "SN": today["SN"],
                "Symbol": symbol,
                "LTP": live["LTP"],
                "Change%": live["Change%"],
                "Day High": live["Day High"],
                "Day Low": live["Day Low"],
                "Previous Close": live["Previous Close"],
                "Volume": live["Volume"],
                "Turnover": today["Turnover"],
                "52 Week High": today["52 Week High"],
                "52 Week Low": today["52 Week Low"],
                "Down From High (%)": f"{down_from_high:.2f}" if isinstance(down_from_high, float) else "N/A",
                "Up From Low (%)": f"{up_from_low:.2f}" if isinstance(up_from_low, float) else "N/A"
            })
    return merged

# Function to generate HTML
def generate_html(main_table):
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Live Data</title>
        <style>
            /* CSS styles here */
        </style>
        <script>
            /* JavaScript functions here */
        </script>
    </head>
    <body>
        <h1>NEPSE Data Table</h1>
        <h2>Welcome to Syntoo's Nepse Stock Data</h2>
        <div class="updated-time">
            <div class="left">Updated on: {updated_time}</div>
            <div class="right">Developed By: <a href="https://www.facebook.com/srajghimire">Syntoo</a></div>
        </div>
        <!-- Table and other HTML content here -->
    </body>
    </html>
    """
    return html

# Upload to FTP
def upload_to_ftp(html_content):
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.cwd("/htdocs")
            with open("index.html", "rb") as f:
                ftp.storbinary("STOR index.html", f)
    except Exception as e:
        print(f"Error uploading to FTP: {e}")

# Refresh Data
def refresh_data():
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    if live_data and today_data:
        merged_data = merge_data(live_data, today_data)
        html_content = generate_html(merged_data)
        upload_to_ftp(html_content)
    else:
        print("Failed to retrieve data for refreshing.")

# Scheduler
scheduler.add_job(refresh_data, CronTrigger(hour="11-15", minute="*/5", timezone="Asia/Kathmandu"))
scheduler.start()

# Initial Data Refresh
refresh_data()

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
