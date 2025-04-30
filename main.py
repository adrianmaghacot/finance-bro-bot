import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yfinance as yf
import pytz
import os
import pandas as pd
import requests

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Replace with your actual Discord channel ID
CHANNEL_ID = 1367012539686453259

# -----------------------------------------
# Helper function to get gainers and losers
# -----------------------------------------
def get_gainers_losers():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        gainers_url = "https://finance.yahoo.com/gainers"
        gainers_response = requests.get(gainers_url, headers=headers)

        if gainers_response.status_code != 200:
            print("Failed to fetch gainers page:", gainers_response.status_code)
            return None, None

        gainers_html = gainers_response.text
        tables = pd.read_html(gainers_html)

        if not tables:
            print("No tables found on gainers page.")
            return None, None

        gainers = tables[0].head(5)
        print("Gainers Columns:", gainers.columns.tolist())

        losers_url = "https://finance.yahoo.com/losers"
        losers_response = requests.get(losers_url, headers=headers)

        if losers_response.status_code != 200:
            print("Failed to fetch losers page:", losers_response.status_code)
            return None, None

        losers_html = losers_response.text
        tables = pd.read_html(losers_html)

        if not tables:
            print("No tables found on losers page.")
            return None, None

        losers = tables[0].head(5)
        print("Losers Columns:", losers.columns.tolist())

        return gainers, losers

    except Exception as e:
        print("Error getting gainers/losers:", e)
        return None, None
# -----------------------------------------
# Fetch summary and send message
# -----------------------------------------
def fetch_stock_summary():
    try:
        indices = {
            "S&P 500": "^GSPC",
            "Dow Jones": "^DJI",
            "Nasdaq": "^IXIC",
            "VIX": "^VIX"
        }

        message = "**Market Close Summary:**\n"
        for name, symbol in indices.items():
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if data.empty:
                continue
            last = data["Close"].iloc[-1]
            change = last - data["Open"].iloc[-1]
            pct = (change / data["Open"].iloc[-1]) * 100
            message += f"{name}: {last:.2f} ({change:+.2f}, {pct:+.2f}%)\n"

        # Get gainers and losers
        gainers, losers = get_gainers_losers()
        if gainers is None or losers is None:
            return "Error fetching top gainers/losers from Yahoo Finance."

        message += "\n**Top 5 Gainers:**\n"
        for i, row in gainers.iterrows():
            message += f"{i+1}. {row['Symbol']} - {row['Name']} (+{row['% Change']})\n"

        message += "\n**Top 5 Losers:**\n"
        for i, row in losers.iterrows():
            message += f"{i+1}. {row['Symbol']} - {row['Name']} ({row['% Change']})\n"

        return message
    except Exception as e:
        return f"Error fetching stock data: {e}"

# -----------------------------------------
# Events and scheduling
# -----------------------------------------
@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    scheduler.start()

@bot.command(name="stocks")
async def stocks(ctx):
    message = fetch_stock_summary()
    await ctx.send(message)

# Daily schedule at 4 PM US Eastern
scheduler = AsyncIOScheduler(timezone=pytz.timezone("US/Eastern"))

@scheduler.scheduled_job("cron", hour=16, minute=0)
async def scheduled_post():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        message = fetch_stock_summary()
        await channel.send(message)

# Run the bot using the token stored in secrets
#bot.run(os.getenv("DISCORD_TOKEN"))
print("DISCORD_TOKEN IS:", os.getenv("DISCORD_TOKEN"))
