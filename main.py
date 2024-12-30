import os
import time
import requests
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from flask import Flask

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_URL = os.getenv("API_URL")

# Initialize bot
bot = Bot(token=BOT_TOKEN)

def fetch_data():
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()  # Assuming the API returns JSON data
    else:
        return None

def format_data(data):
    # Format the data received from API to a readable string
    formatted_data = (
        f"Data for Symbol\n\n"
        f"LTP: {data.get('LTP')}\n"
        f"Change Point: {data.get('Change Point')}\n"
        f"Day High: {data.get('Day High')}\n"
        f"Day Low: {data.get('Day Low')}\n"
        f"Previous Close: {data.get('Previous Close')}\n"
        f"Volume: {data.get('Volume')}\n"
        f"Turn Over: {data.get('Turn Over')}\n"
        f"52 Week High: {data.get('52 Week High')}\n"
        f"52 Week Low: {data.get('52 Week Low')}\n"
        f"Down From 52 Week High: {data.get('Down From 52 Week High')}\n"
        f"Up From 52 Week Low: {data.get('Up From 52 Week Low')}\n"
    )
    return formatted_data

def send_message():
    data = fetch_data()
    if data:
        message = format_data(data)
        bot.send_message(chat_id=CHAT_ID, text=message)
    else:
        bot.send_message(chat_id=CHAT_ID, text="Failed to fetch data from API.")

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome to the NEPSE Telegram Bot!')

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add command handler for /start
    dispatcher.add_handler(CommandHandler("start", start))

    # Start the bot
    updater.start_polling()
    updater.idle()

app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is running."

if __name__ == '__main__':
    # Start the bot in a separate thread
    import threading
    bot_thread = threading.Thread(target=main)
    bot_thread.start()

    # Start Flask server
    app.run(host='0.0.0.0', port=5000)
    
    # Schedule data fetching and sending message every hour
    while True:
        send_message()
        time.sleep(3600)  # Sleep for 1 hour
