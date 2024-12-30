import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, render_template_string

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Function to scrape NEPSE Market Summary
def scrape_market_summary():
    url = "https://nepsealpha.com/live-market/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    summary_data = {}
    table = soup.find("table", class_="table")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 2:
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                summary_data[key] = value
    return summary_data

# Function to scrape Nepse Index from HamroShare
def scrape_nepse_index():
    url = "https://www.hamroshare.com.np/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    index_div = soup.find("div", class_="nepse-index")
    nepse_index = index_div.text.strip() if index_div else "N/A"
    return nepse_index

# (Remaining scraping functions unchanged...)

# Function to generate HTML
def generate_html(main_table, nepse_index):
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    market_summary = scrape_market_summary()

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Live Data</title>
        <style>
            /* Styles are unchanged */
        </style>
        <script>
            /* JavaScript code is unchanged */
        </script>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <h2>Welcome 🙏 to my Nepse Data website</h2>
        <div class="updated-time">
            <div class="left">Updated on: {updated_time}</div>
            <div class="right">Developed By: <a href="https://www.facebook.com/srajghimire">Syntoo</a></div>
        </div>

        <div class="nepse-index">
            <strong>NEPSE Index:</strong> {nepse_index}
        </div>

        <div class="summary-container">
            <h2>NEPSE Market Summary</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Date</td><td>{market_summary.get("Date", "N/A")}</td></tr>
                <tr><td>Current</td><td>{market_summary.get("Current", "N/A")}</td></tr>
                <tr><td>Daily Gain</td><td>{market_summary.get("Daily Gain", "N/A")}</td></tr>
                <tr><td>Total Turnover</td><td>{market_summary.get("Total Turnover", "N/A")}</td></tr>
                <tr><td>Total Traded Share</td><td>{market_summary.get("Total Traded Share", "N/A")}</td></tr>
                <tr><td>Total Transactions</td><td>{market_summary.get("Total Transactions", "N/A")}</td></tr>
                <tr><td>Total Scrips Traded</td><td>{market_summary.get("Total Scrips Traded", "N/A")}</td></tr>
            </table>
        </div>

        <div class="search-container">
            <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Search for symbols...">
        </div>

        <div class="table-container">
            <table id="nepseTable">
                <thead>
                    <tr>
                        <!-- Table headers are unchanged -->
                    </tr>
                </thead>
                <tbody>
    """
    for row in main_table:
        # Row generation remains unchanged
        pass
    html += """
        </tbody>
        </table>
    </div>
    </body>
    </html>
    """
    return html

# (Remaining functions unchanged...)

# Refresh Data
def refresh_data():
    nepse_index = scrape_nepse_index()
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    merged_data = merge_data(live_data, today_data)
    html_content = generate_html(merged_data, nepse_index)
    upload_to_ftp(html_content)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=15)
scheduler.start()

# Initial Data Refresh
refresh_data()

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
