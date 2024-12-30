import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

def scrape_nepse_data():
    url = "https://nepsealpha.com/live-market/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract data
    try:
        table = soup.find("table", {"class": "table-market-summary"})
        rows = table.find_all("tr")

        data = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Current": rows[1].find_all("td")[1].text.strip(),
            "Daily Gain": rows[2].find_all("td")[1].text.strip(),
            "Total Turnover": rows[3].find_all("td")[1].text.strip(),
            "Total Traded Share": rows[4].find_all("td")[1].text.strip(),
            "Total Transactions": rows[5].find_all("td")[1].text.strip(),
            "Total Scrips Traded": rows[6].find_all("td")[1].text.strip(),
            "Total Float Market Capitalization Rs": rows[7].find_all("td")[1].text.strip(),
            "NEPSE Market Cap": rows[8].find_all("td")[1].text.strip()
        }
    except Exception as e:
        print("Error while scraping:", e)
        return None

    return data

def generate_html(data):
    # Determine Daily Gain color
    daily_gain = float(data["Daily Gain"].replace(",", "").strip())
    if daily_gain > 0:
        color = "green"
    elif daily_gain < 0:
        color = "red"
    else:
        color = "blue"

    # HTML Template
    html_content = f"""
    <html>
    <head>
        <title>NEPSE Market Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .gain {{ color: {color}; }}
        </style>
    </head>
    <body>
        <h1>NEPSE Market Summary</h1>
        <p>Date: {data['Date']}</p>
        <p>Current: {data['Current']}</p>
        <p class="gain">Daily Gain: {data['Daily Gain']}</p>
        <p>Total Turnover: {data['Total Turnover']}</p>
        <p>Total Traded Share: {data['Total Traded Share']}</p>
        <p>Total Transactions: {data['Total Transactions']}</p>
        <p>Total Scrips Traded: {data['Total Scrips Traded']}</p>
        <p>Total Float Market Capitalization Rs: {data['Total Float Market Capitalization Rs']}</p>
        <p>NEPSE Market Cap: {data['NEPSE Market Cap']}</p>
    </body>
    </html>
    """
    return html_content

def upload_to_ftp(html_content):
    try:
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            with open("nepse_summary.html", "w") as file:
                file.write(html_content)

            with open("nepse_summary.html", "rb") as file:
                ftp.storbinary("STOR nepse_summary.html", file)

        print("File uploaded successfully.")
    except Exception as e:
        print("FTP upload error:", e)

def update_nepse_summary():
    data = scrape_nepse_data()
    if data:
        html_content = generate_html(data)
        upload_to_ftp(html_content)

# Scheduler to run the script every 5 minutes
scheduler = BackgroundScheduler(timezone=timezone("Asia/Kathmandu"))
scheduler.add_job(update_nepse_summary, "interval", minutes=5)
scheduler.start()

if __name__ == "__main__":
    # Run Flask server if needed (optional for testing purposes)
    from flask import Flask
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "<h1>NEPSE Summary Scraper Running...</h1>"

    app.run(port=int(os.getenv("PORT", 5000)))
