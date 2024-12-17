import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from dotenv import load_dotenv

# .env फाइल लोड गर्नुहोस्
load_dotenv()

# Flask app सेटअप
app = Flask(__name__)

# Telegram Application Instance
application = None  # Define application globally for accessibility

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

# Telegram Handlers
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
        response = f"Symbol '{symbol}' मिलेन, ल्या के पो बिग्य्रो ? 😂 Symbol चेक गरेर कृपया पुन: प्रयास गर्नुहोस्।"

    await update.message.reply_text(response, parse_mode=ParseMode.HTML)

# Flask Route to Handle Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    update = Update.de_json(data, application.bot)  # Parse incoming update data
    application.process_update(update)  # Process the update synchronously
    return "Webhook received!", 200

@app.route('/')
def home():
    return "Flask App is Running and Webhook is set!"

# Main Function
if __name__ == '__main__':
    # Environment Variables
    TOKEN = os.getenv("TELEGRAM_API_KEY")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Your Render-provided URL
    
    # Telegram Bot Setup
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stock_symbol))

    # Set Webhook
    print("Setting Webhook...")
    application.bot.set_webhook(url=WEBHOOK_URL + "/webhook")
    print(f"Webhook set to: {WEBHOOK_URL}/webhook")

    # Start Flask App
    print("Starting Flask Server...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))