import os
import logging
import yt_dlp
import asyncio
import requests
from bot import Bot
from config import OWNER_ID, CHANNEL_ID
from pyrogram import Client, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the scheduler
scheduler = AsyncIOScheduler()

def download_videos(search_term, max_duration):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'match_filter': yt_dlp.utils.match_filter_func(f"duration <= {max_duration} and title ~ '{search_term}'"),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(f"ytsearch10:{search_term}", download=True)
        video_files = [os.path.join('downloads', f"{entry['title']}.{entry['ext']}") for entry in info_dict['entries']]
    
    return video_files

async def upload_videos(video_files, channel_id):
    async with Bot:
        for video_file in video_files:
            if os.path.exists(video_file):
                await Bot.send_video(channel_id, video_file, caption=f"Uploading {os.path.basename(video_file)}")
                os.remove(video_file)

def check_youtube_channel():
    search_term = "Battle Through The Heavens"
    max_duration = 600  # 10 minutes

    # Download videos matching the search term and upload them
    video_files = download_videos(search_term, max_duration)
    asyncio.run(upload_videos(video_files, CHANNEL_ID))

@Bot.on_message(filters.command("on") & filters.user(OWNER_ID))
async def start_checking(client, message):
    if not scheduler.running:
        scheduler.add_job(check_youtube_channel, 'interval', minutes=10)
        scheduler.start()
        await message.reply("Started checking YouTube for new videos every 10 minutes.")
    else:
        await message.reply("The process is already running.")

@Bot.on_message(filters.command("off") & filters.user(OWNER_ID))
async def stop_checking(client, message):
    if scheduler.running:
        scheduler.shutdown()
        await message.reply("Stopped checking YouTube for new videos.")
    else:
        await message.reply("The process is not running.")

@Bot.on_message(filters.user(OWNER_ID) & filters.regex(r'https?://\S+'))
async def handle_owner_link(client, message):
    video_url = message.text.strip()
    video_files = download_videos(video_url, 600)
    await upload_videos(video_files, CHANNEL_ID)
    await message.reply("Video downloaded and uploaded to the channel.")