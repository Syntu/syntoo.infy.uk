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


@app.route("/")
def index():
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    merged_data = merge_data(live_data, today_data)

    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trading Data</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th {
                position: sticky;
                top: 0;
                background-color: brown;
                color: white;
                cursor: pointer;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border: 1px solid #ddd;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .negative {
                background-color: lightcoral;
            }
            .positive {
                background-color: lightgreen;
            }
            .neutral {
                background-color: lightblue;
            }
            .highlight {
                background-color: yellow;
            }
        </style>
    </head>
    <body>
        <table id="tradingTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">SN</th>
                    <th onclick="sortTable(1)">Symbol</th>
                    <th onclick="sortTable(2)">LTP</th>
                    <th onclick="sortTable(3)">Change%</th>
                    <th onclick="sortTable(4)">Day High</th>
                    <th onclick="sortTable(5)">Day Low</th>
                    <th onclick="sortTable(6)">Previous Close</th>
                    <th onclick="sortTable(7)">Volume</th>
                    <th onclick="sortTable(8)">Turnover</th>
                    <th onclick="sortTable(9)">52 Week High</th>
                    <th onclick="sortTable(10)">52 Week Low</th>
                    <th onclick="sortTable(11)">Down From High (%)</th>
                    <th onclick="sortTable(12)">Up From Low (%)</th>
                </tr>
            </thead>
            <tbody>
                {% for row in merged_data %}
                <tr class="{{ 'negative' if row['Change%'].startswith('-') else 'positive' if row['Change%'] != '0.00' else 'neutral' }}">
                    <td>{{ row['SN'] }}</td>
                    <td>{{ row['Symbol'] }}</td>
                    <td>{{ row['LTP'] }}</td>
                    <td>{{ row['Change%'] }}</td>
                    <td>{{ row['Day High'] }}</td>
                    <td>{{ row['Day Low'] }}</td>
                    <td>{{ row['Previous Close'] }}</td>
                    <td>{{ row['Volume'] }}</td>
                    <td>{{ row['Turnover'] }}</td>
                    <td>{{ row['52 Week High'] }}</td>
                    <td>{{ row['52 Week Low'] }}</td>
                    <td>{{ row['Down From High (%)'] }}</td>
                    <td>{{ row['Up From Low (%)'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <script>
            // Sort table function
            function sortTable(n) {
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("tradingTable");
                switching = true;
                dir = "asc"; 
                while (switching) {
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];
                        if (dir == "asc") {
                            if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                                shouldSwitch = true;
                                break;
                            }
                        } else if (dir == "desc") {
                            if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                                shouldSwitch = true;
                                break;
                            }
                        }
                    }
                    if (shouldSwitch) {
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount++;
                    } else {
                        if (switchcount == 0 && dir == "asc") {
                            dir = "desc";
                            switching = true;
                        }
                    }
                }
            }

            // Highlight row on click
            document.querySelectorAll("#tradingTable tbody tr").forEach(row => {
                row.addEventListener("click", () => {
                    document.querySelectorAll("#tradingTable tbody tr").forEach(r => r.classList.remove("highlight"));
                    row.classList.add("highlight");
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(template, merged_data=merged_data)

if __name__ == "__main__":
    app.run(port=PORT)
