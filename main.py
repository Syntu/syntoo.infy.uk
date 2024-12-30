import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Website URL
url = "https://nepsealpha.com/live-market/"

# Send request and parse data
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Function to get text or default
def get_text_or_default(element, default="N/A"):
    return element.text.strip() if element else default

# Extract data
market_summary = soup.find('div', {'class': 'market-summary'})

# Parse individual data points
date = datetime.now().strftime('%Y-%m-%d')
current = get_text_or_default(market_summary.find('span', {'class': 'current-index'}))
daily_gain = get_text_or_default(market_summary.find('span', {'class': 'daily-gain'}))
total_turnover = get_text_or_default(market_summary.find('span', {'id': 'total-turnover'}))
total_traded_share = get_text_or_default(market_summary.find('span', {'id': 'total-traded-share'}))
total_transactions = get_text_or_default(market_summary.find('span', {'id': 'total-transactions'}))
total_scrips_traded = get_text_or_default(market_summary.find('span', {'id': 'total-scrips-traded'}))
float_market_cap = get_text_or_default(market_summary.find('span', {'id': 'float-market-cap'}))
nepse_market_cap = get_text_or_default(market_summary.find('span', {'id': 'nepse-market-cap'}))

# Determine daily gain color
if daily_gain.startswith('-'):
    daily_gain_color = "red"
elif daily_gain == "0" or daily_gain == "0.00":
    daily_gain_color = "blue"
else:
    daily_gain_color = "green"

# Generate HTML
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEPSE Market Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        .red {{ color: red; }}
        .green {{ color: green; }}
        .blue {{ color: blue; }}
    </style>
</head>
<body>
    <h1>NEPSE Market Summary</h1>
    <table>
        <tr><th>Date</th><td>{date}</td></tr>
        <tr><th>Current</th><td>{current}</td></tr>
        <tr><th>Daily Gain</th><td class="{daily_gain_color}">{daily_gain}</td></tr>
        <tr><th>Total Turnover</th><td>{total_turnover}</td></tr>
        <tr><th>Total Traded Share</th><td>{total_traded_share}</td></tr>
        <tr><th>Total Transactions</th><td>{total_transactions}</td></tr>
        <tr><th>Total Scrips Traded</th><td>{total_scrips_traded}</td></tr>
        <tr><th>Total Float Market Capitalization Rs:</th><td>{float_market_cap}</td></tr>
        <tr><th>NEPSE Market Cap</th><td>{nepse_market_cap}</td></tr>
    </table>
</body>
</html>
"""

# Save HTML to file
output_file = "nepse_market_summary.html"
with open(output_file, "w", encoding="utf-8") as file:
    file.write(html_content)

print(f"NEPSE Market Summary saved to {output_file}")
