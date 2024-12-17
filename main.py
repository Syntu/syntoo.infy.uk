import os
import requests
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

from telegram import Update, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# .env फाइल लोड गर्नुहोस्
load_dotenv()

# ------------------- Flask App Setup -------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Flask App is Running! Use Telegram Bot for Stock Data."

# ------------------- Fetch Stock Data -------------------
def fetch_stock_data_by_symbol(symbol):
    """
    Fetch stock data from the website for a given symbol.
    """
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table')
    rows = table.find_all('tr')[1:]  # Skip header row

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

# ------------------- Telegram Bot Handlers -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Welcome Message Handler.
    """
    await update.message.reply_text(
        "सन्तोषको NEPSEBOT मा स्वागत छ।\n"
        "के को डाटा चाहियो? कृपया स्टकको सिम्बोल दिनुहोस्।\n"
        "उदाहरण: NABIL, SCB, PRVU"
    )

async def handle_stock_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle stock symbol input from users.
    """
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

# ------------------- Telegram Bot Setup -------------------
def run_telegram_bot():
    """
    Initialize and start the Telegram Bot.
    """
    TOKEN = os.getenv("TELEGRAM_API_KEY")
    application = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stock_symbol))

    # Run Bot
    print("Starting Telegram Bot...")
    application.run_polling()

# ------------------- Main Function -------------------
if __name__ == "__main__":
    # Run Flask App in Thread
    def run_flask():
        port = int(os.getenv("PORT", 8080))
        app.run(host="0.0.0.0", port=port)

    # Start Flask App and Telegram Bot simultaneously
    Thread(target=run_flask).start()
    run_telegram_bot()