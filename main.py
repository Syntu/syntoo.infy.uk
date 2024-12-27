import os
from datetime import datetime, time
import ftplib
import logging
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask
from pytz import timezone

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Global variable to store the last data fetched at 15:10
last_data = None

# Function to scrape live trading data
def scrape_live_trading():
    logging.info("Scraping live trading data...")
    url = "https://www.sharesansar.com/live-trading"
    try:
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
    except requests.RequestException as e:
        logging.error(f"Error scraping live trading data: {e}")
        return []

# Function to scrape today's share price summary
def scrape_today_share_price():
    logging.info("Scraping today's share price data...")
    url = "https://www.sharesansar.com/today-share-price"
    try:
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
    except requests.RequestException as e:
        logging.error(f"Error scraping today's share price data: {e}")
        return []

# Function to merge live and today's data
def merge_data(live_data, today_data):
    logging.info("Merging live and today's data...")
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
    logging.info("Generating HTML...")
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Live Data</title>
        <!-- Styles and JS -->
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <h2>Updated on: {updated_time}</h2>
        <table>
            <thead>
                <tr>
                    <th>SN</th>
                    <th>Symbol</th>
                    <th>LTP</th>
                    <th>Change%</th>
                    <th>52 Week High</th>
                    <th>52 Week Low</th>
                    <th>Down From High (%)</th>
                    <th>Up From Low (%)</th>
                </tr>
            </thead>
            <tbody>
    """
    for row in main_table:
        html += f"""
            <tr>
                <td>{row["SN"]}</td>
                <td>{row["Symbol"]}</td>
                <td>{row["LTP"]}</td>
                <td>{row["Change%"]}</td>
                <td>{row["52 Week High"]}</td>
                <td>{row["52 Week Low"]}</td>
                <td>{row["Down From High (%)"]}</td>
                <td>{row["Up From Low (%)"]}</td>
            </tr>
        """
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

# Upload to FTP
def upload_to_ftp(html_content):
    logging.info("Uploading to FTP...")
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.cwd("/htdocs")
            with open("index.html", "rb") as f:
                ftp.storbinary("STOR index.html", f)
        logging.info("Upload successful!")
    except ftplib.all_errors as e:
        logging.error(f"Error uploading to FTP: {e}")

# Refresh Data
def refresh_data():
    global last_data
    logging.info("Refreshing data...")
    current_time = datetime.now(timezone("Asia/Kathmandu")).time()
    start_time = time(10, 30)
    end_time = time(15, 10)
    if start_time <= current_time <= end_time:
        live_data = scrape_live_trading()
        today_data = scrape_today_share_price()
        merged_data = merge_data(live_data, today_data)
        if current_time == end_time:
            last_data = merged_data  # Store the last data at 15:10
    else:
        logging.info("Outside trading hours. Using last available data.")
        merged_data = last_data if last_data else []
    html_content = generate_html(merged_data)
    upload_to_ftp(html_content)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, CronTrigger(minute='*/10', hour='10-14', day_of_week='sun,mon,tue,wed,thu'))
scheduler.add_job(refresh_data, CronTrigger(minute='0-10/10', hour='15', day_of_week='sun,mon,tue,wed,thu'))
scheduler.add_job(refresh_data, CronTrigger(minute='10', hour='15', day_of_week='sun,mon,tue,wed,thu'))
scheduler.start()

if __name__ == "__main__":
    refresh_data()
    app.run(host="0.0.0.0", port=PORT)
