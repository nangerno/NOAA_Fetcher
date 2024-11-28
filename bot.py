import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
NOAA_URL = "https://www.charts.noaa.gov/ENCs/ENCs.shtml"
DOWNLOAD_PREFIX_URL = 'https://www.charts.noaa.gov/ENCs/'
last_update = None
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def check_noaa_updates():
    global last_update
    try:
        response = requests.get(NOAA_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr') if table else []
        updates = []
        for row in rows[1:]:
            columns = row.find_all('td')
            if len(columns) > 1:
                filename = columns[0].text.strip()
                dates = columns[3].text.strip()
                link = columns[0].find('a', href=True)
                if link and link.get('href'):
                    download_url = link['href']
                    if download_url.endswith('.zip'):
                        download_url = DOWNLOAD_PREFIX_URL + download_url
                        updates.append((filename, download_url, dates))
        if updates and updates != last_update:
            last_update = updates
            return updates
    except Exception as e:
        print(f"Error checking NOAA updates: {e}")
    return None

async def monitor_noaa_updates():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    
    while True:
        updates = check_noaa_updates()
        if updates and channel:
            for filename, download_url, dates in updates:
                await channel.send(f'🚨 Date: {dates}\n 📥 Download: {download_url}')
        await asyncio.sleep(3600)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Bot is ready and online!')
    bot.loop.create_task(monitor_noaa_updates())

@bot.command(name='hello')
async def hello(ctx):
    await ctx.send(f'Hello {ctx.author.name}! 👋')

@bot.command(name='role')
async def role(ctx):
    await ctx.send(f'😍 My role is to notify you of NOAA chart updates!')

@bot.command(name='update')
async def update(ctx, message: str = "A new update is available!"):
    await ctx.send(f'🚨 {message}')

bot.run(TOKEN)
