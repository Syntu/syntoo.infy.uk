import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Function to scrape live trading data
def scrape_live_trading():
    url = "https://www.sharesansar.com/live-trading"
    response = requests.get(url)
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

# Function to scrape today's share price summary
def scrape_today_share_price():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
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

# Function to scrape NEPSE index data
def scrape_nepse_index():
    url = "https://nepalstock.com.np/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    index_data = {}
    try:
        index_data["Points"] = soup.find("div", {"id": "nepse_index"}).find("span", {"class": "point"}).text.strip()
        index_data["Points Change"] = soup.find("div", {"id": "nepse_index"}).find("span", {"class": "point-change"}).text.strip()
        index_data["Change Percent"] = soup.find("div", {"id": "nepse_index"}).find("span", {"class": "percent-change"}).text.strip()
        index_data["Total Turnover"] = soup.find("div", {"id": "total_turnover"}).find("span").text.strip()
        index_data["Total Traded Share"] = soup.find("div", {"id": "total_traded_share"}).find("span").text.strip()
    except AttributeError as e:
        print(f"Error parsing NEPSE index: {e}")
    return index_data

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
    nepse_index = scrape_nepse_index()  # Fetch NEPSE index data
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Live Data</title>
        <style>
            /* Add your existing CSS styles here */
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <h2>Welcome 🙏 to my Nepse Data website</h2>
        <div class="updated-time">
            <div class="left">Updated on: {updated_time}</div>
            <div class="right">Developed By: <a href="https://www.facebook.com/srajghimire">Syntoo</a></div>
        </div>
        <div class="nepse-index">
            <h3>NEPSE Index Data:</h3>
            <ul>
                <li><strong>Points:</strong> {nepse_index.get("Points", "N/A")}</li>
                <li><strong>Points Change:</strong> {nepse_index.get("Points Change", "N/A")}</li>
                <li><strong>Change Percent:</strong> {nepse_index.get("Change Percent", "N/A")}</li>
                <li><strong>Total Turnover:</strong> {nepse_index.get("Total Turnover", "N/A")}</li>
                <li><strong>Total Traded Share:</strong> {nepse_index.get("Total Traded Share", "N/A")}</li>
            </ul>
        </div>
        <div class="search-container">
            <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Search for symbols...">
        </div>
        <div class="table-container">
            <!-- Existing Table Content -->
        </div>
    </body>
    </html>
    """
    return html

# Upload to FTP
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Refresh Data
def refresh_data():
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    merged_data = merge_data(live_data, today_data)
    html_content = generate_html(merged_data)
    upload_to_ftp(html_content)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=10)  # Updated to 10 minutes
scheduler.start()

# Initial Data Refresh
refresh_data()

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
