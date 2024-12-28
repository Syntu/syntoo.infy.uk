import os
import asyncio
import aiohttp
import aioftp
import aiofiles
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
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

LIVE_TRADING_URL = "YOUR_LIVE_TRADING_URL"
TODAY_SHARE_PRICE_URL = "YOUR_TODAY_SHARE_PRICE_URL"

# Function to scrape data from a given URL and parse it with BeautifulSoup
async def scrape_data(url, parse_function):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            soup = BeautifulSoup(content, "html.parser")
            return parse_function(soup)

# Parse function for live trading data
def parse_live_trading(soup):
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

# Parse function for today's share price summary
def parse_today_share_price(soup):
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
        <!-- Add your CSS and JavaScript here -->
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <div>Updated on: {updated_time}</div>
        <table>
            <thead>
                <tr>
                    <th>SN</th>
                    <th>Symbol</th>
                    <th>LTP</th>
                    <th>Change%</th>
                    <th>Day High</th>
                    <th>Day Low</th>
                    <th>Previous Close</th>
                    <th>Volume</th>
                    <th>Turnover</th>
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
                <td>{row["Day High"]}</td>
                <td>{row["Day Low"]}</td>
                <td>{row["Previous Close"]}</td>
                <td>{row["Volume"]}</td>
                <td>{row["Turnover"]}</td>
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
async def upload_to_ftp(html_content):
    try:
        async with aioftp.Client.context(FTP_HOST, FTP_USER, FTP_PASS) as client:
            async with aiofiles.open("nepse_live.html", "w") as f:
                await f.write(html_content)
            await client.upload("nepse_live.html", "/nepse_live.html")
    except Exception as e:
        print(f"FTP Upload Error: {e}")

# Refresh Data
async def refresh_data():
    try:
        live_data = await scrape_data(LIVE_TRADING_URL, parse_live_trading)
        today_data = await scrape_data(TODAY_SHARE_PRICE_URL, parse_today_share_price)
        merged_data = merge_data(live_data, today_data)
        html_content = generate_html(merged_data)
        await upload_to_ftp(html_content)
    except Exception as e:
        print(f"Error during data refresh: {e}")

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: asyncio.run(refresh_data()), "interval", minutes=5)
scheduler.start()

# Initial Data Refresh
asyncio.run(refresh_data())

# Flask route to show data
@app.route("/")
async def home():
    async with aiofiles.open("nepse_live.html", "r") as f:
        content = await f.read()
    return content

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
