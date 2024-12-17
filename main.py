import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app initialization
app = Flask(__name__)

# Stock data fetching function
def fetch_stock_data_by_symbol(symbol):
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table')
    rows = table.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('td')
        row_symbol = cols[1].text.strip()
        if row_symbol.upper() == symbol.upper():
            return {
                'Symbol': symbol,
                'Day High': cols[4].text.strip(),
                'Day Low': cols[5].text.strip(),
                'Closing Price': cols[6].text.strip(),
                'Change Percent': cols[14].text.strip(),
                'Volume': cols[8].text.strip(),
                'Turnover': cols[10].text.strip()
            }
    return None

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "सन्तोषको NEPSEBOT मा स्वागत छ।\n"
        "के को डाटा चाहियो? कृपया स्टकको सिम्बोल दिनुहोस्।\n"
        "उदाहरण: NABIL, SCB, PRVU"
    )

async def handle_stock_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()
    data = fetch_stock_data_by_symbol(symbol)

    if data:
        response = (
            f"Stock Data for <b>{data['Symbol']}</b>:\n\n"
            f"Day High: {data['Day High']}\n"
            f"Day Low: {data['Day Low']}\n"
            f"Closing Price: {data['Closing Price']}\n"
            f"Change Percent: {data['Change Percent']}\n"
            f"Volume: {data['Volume']}\n"
            f"Turnover: {data['Turnover']}"
        )
    else:
        response = f"Symbol '{symbol}' मिलेन, कृपया पुन: प्रयास गर्नुहोस्।"
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)

# Webhook Endpoint for Telegram Bot
@app.route("/set_webhook", methods=["GET", "POST"])
def set_webhook():
    TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
    webhook_url = f"{os.getenv('WEBHOOK_URL')}/webhook"
    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/setWebhook",
        json={"url": webhook_url}
    )
    return response.text

@app.route("/webhook", methods=["POST"])
async def webhook():
    json_data = request.get_json()
    update = Update.de_json(json_data, bot)
    await application.process_update(update)
    return "OK"

# Main Function
if __name__ == "__main__":
    TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
    global application
    application = ApplicationBuilder().token(TELEGRAM_API_KEY).build()

    # Add Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stock_symbol))

    # Start Flask Server
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))