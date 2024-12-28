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
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            h1 {{
                text-align: center;
                font-size: 40px;
                font-weight: bold;
                margin-top: 20px;
            }}
            h2 {{
                text-align: center;
                font-size: 14px;
                margin-bottom: 20px;
            }}
            .search-container {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .search-container input[type="text"] {{
                width: 60%;
                padding: 8px;
                font-size: 16px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .table-container {{
                margin: 0 auto;
                width: 95%;
                overflow-x: auto;
                overflow-y: auto;
                height: 600px; /* Adjust as needed */
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 14px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #8B4513;
                color: white;
                position: sticky;
                top: 0;
                z-index: 2;
                cursor: pointer;
                white-space: nowrap;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .symbol {{ 
                color: #1e90ff;
                font-weight: bold;
            }}
            .footer {{
                text-align: right;
                padding: 10px;
                font-size: 12px;
                color: gray;
            }}
            .footer a {{
                color: inherit;
                text-decoration: none;
            }}
            .updated-time {{
                font-size: 14px;
                margin-top: 10px;
            }}
        </style>
        <script>
            function searchSymbol() {{
                var input, filter, table, tr, td, i, txtValue;
                input = document.getElementById("symbolSearch");
                filter = input.value.toUpperCase();
                table = document.getElementById("nepseTable");
                tr = table.getElementsByTagName("tr");
                for (i = 1; i < tr.length; i++) {{
                    td = tr[i].getElementsByTagName("td")[1];
                    if (td) {{
                        txtValue = td.textContent || td.innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                            tr[i].style.display = "";
                        }} else {{
                            tr[i].style.display = "none";
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <h2>Welcome 🙏 to my Nepse Data website</h2>
        <div class="updated-time">
            <div>Updated on: {updated_time}</div>
        </div>
        <div class="search-container">
            <input type="text" id="symbolSearch" onkeyup="searchSymbol()" placeholder="Search for symbols..">
        </div>
        <div class="table-container">
            <table id="nepseTable">
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
        change_class = "light-red" if float(row["Change%"]) < 0 else (
            "light-green" if float(row["Change%"]) > 0 else "light-blue")
        html += f"""
            <tr>
                <td>{row["SN"]}</td>
                <td class="symbol">{row["Symbol"]}</td>
                <td>{row["LTP"]}</td>
                <td class="{change_class}">{row["Change%"]}</td>
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
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html_content = generate_html(merged_data, updated_time)
    upload_to_ftp(html_content)

# Scheduler
scheduler = BackgroundScheduler()
trigger1 = OrTrigger([CronTrigger(day_of_week='sun-thu', hour='10-15', minute='*/10')])
scheduler.add_job(refresh_data, trigger1)
scheduler.add_job(refresh_data, CronTrigger(day_of_week='sun-thu', hour=15, minute=10))
scheduler.start()

# Initial Data Refresh
refresh_data()

# Serve the generated HTML file
@app.route('/')
def serve_html():
    return send_from_directory('.', 'index.html')

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
