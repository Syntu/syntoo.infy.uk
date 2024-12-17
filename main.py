import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# .env फाइल लोड गर्नुहोस्
load_dotenv()

# Environment Variables
TOKEN = os.getenv("TELEGRAM_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Ensure .env has correct URL

# Flask App Setup
app = Flask(__name__)

# Telegram Application Setup
application = ApplicationBuilder().token(TOKEN).build()

# Function to Fetch Stock Data
def fetch_stock_data_by_symbol(symbol):
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")[1:]

    for row in rows:
        cols = row.find_all("td")
        row_symbol = cols[1].text.strip()
        if row_symbol.upper() == symbol.upper():
            return {
                "Symbol": symbol,
                "Day High": cols[4].text.strip(),
                "Day Low": cols[5].text.strip(),
                "Closing Price": cols[6].text.strip(),
                "Change Percent": cols[14].text.strip(),
                "Volume": cols[8].text.strip(),
                "Turnover": cols[10].text.strip(),
            }
    return None

# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Syntu's NEPSE Bot!\nSend a stock symbol (e.g., NABIL, SCB) to get stock details."
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
        response = f"Symbol '{symbol}' not found. Please check the spelling and try again."
    await update.message.reply_text(response, parse_mode="HTML")

# Flask Route to Handle Webhook (POST method)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()  # Receive JSON data from Telegram
    update = Update.de_json(data, application.bot)  # Parse the data
    application.process_update(update)  # Process the update
    return "Webhook received!", 200

@app.route("/")
def home():
    return "Flask App is Running and Webhook is set!"

# Main Function
if __name__ == "__main__":
    # Add Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stock_symbol))

    # Set Webhook (use the .env file value for the URL)
    print(f"Setting webhook to {WEBHOOK_URL}/webhook...")
    application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print(f"Webhook set to: {WEBHOOK_URL}/webhook")

    # Start Flask App
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))