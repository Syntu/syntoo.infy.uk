# Import libraries
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

# Scrape NEPSE Market Summary
def scrape_market_summary():
    url = "https://nepsealpha.com/live-market/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    summary_data = {}

    try:
        summary_section = soup.find("div", class_="market-summary")  # Adjust class as per website
        rows = summary_section.find_all("div", class_="summary-row")
        for row in rows:
            label = row.find("div", class_="label").text.strip()
            value = row.find("div", class_="value").text.strip()
            summary_data[label] = value
    except Exception as e:
        print("Error scraping market summary:", e)

    return summary_data

# Generate HTML for Market Summary
def generate_market_summary_html(summary_data):
    html = '<div class="market-summary">'
    for key, value in summary_data.items():
        color = "blue"  # Default color
        if "Daily Gain" in key:
            value_num = float(value.replace(",", "").replace("%", ""))
            if value_num > 0:
                color = "green"
            elif value_num < 0:
                color = "red"

        html += f'<div class="summary-row" style="color: {color};"><span>{key}:</span> {value}</div>'
    html += '</div>'
    return html

# Main HTML Generator
def generate_html(main_table):
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    market_summary = scrape_market_summary()
    market_summary_html = generate_market_summary_html(market_summary)

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Live Data</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            h1 {{ text-align: center; font-size: 40px; margin-top: 20px; }}
            .updated-time, .market-summary, .search-container {{ text-align: center; margin: 10px 0; }}
            .summary-row {{ margin-bottom: 5px; }}
            .table-container {{ margin: 0 auto; width: 95%; overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #8B4513; color: white; cursor: pointer; }}
            .light-red {{ background-color: #FFCCCB; }}
            .light-green {{ background-color: #D4EDDA; }}
            .light-blue {{ background-color: #CCE5FF; }}
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <div class="updated-time">Updated on: {updated_time}</div>
        {market_summary_html}
        <div class="search-container">
            <input type="text" id="searchInput" placeholder="Search for symbols...">
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>SN</th><th>Symbol</th><th>LTP</th><th>Change%</th>
                        <th>Day High</th><th>Day Low</th><th>Volume</th>
                    </tr>
                </thead>
                <tbody>
    """
    for row in main_table:
        html += f"""
            <tr>
                <td>{row["SN"]}</td><td>{row["Symbol"]}</td><td>{row["LTP"]}</td>
                <td>{row["Change%"]}</td><td>{row["Day High"]}</td><td>{row["Day Low"]}</td>
                <td>{row["Volume"]}</td>
            </tr>
        """
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html

# Upload to FTP and Scheduler
def refresh_data():
    live_data = scrape_live_trading()  # Assuming function exists
    html_content = generate_html(live_data)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=15)
scheduler.start()

if __name__ == "__main__":
    refresh_data()
    app.run(host="0.0.0.0", port=PORT)
