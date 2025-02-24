import os
import logging
import requests
import pymongo
from pymongo import MongoClient
from pytube import YouTube
from apscheduler.schedulers.background import BackgroundScheduler
from bot import Bot
from pyrogram import filters

# Configure logging
logging.basicConfig(level=logging.INFO)

# YouTube and Telegram configuration
YOUTUBE_CHANNEL_ID = 'UCoL2Zo2GEuMIsHVJyPwSyJg'
YOUTUBE_API_KEY = 'YOUR_YOUTUBE_API_KEY'
TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID'
MONGO_URI = 'YOUR_MONGO_URI'

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client['youtube_videos']
collection = db['video_titles']

scheduler = BackgroundScheduler()

def check_youtube_channel():
    url = f'https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={YOUTUBE_CHANNEL_ID}&part=snippet,id&order=date&maxResults=5'
    response = requests.get(url)
    videos = response.json().get('items', [])

    for video in videos:
        if video['id']['kind'] == 'youtube#video':
            video_id = video['id']['videoId']
            video_title = video['snippet']['title']
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            video_length = YouTube(video_url).length

            if 'Battle Through The Heavens' in video_title and video_length < 240:
                if not collection.find_one({"title": video_title}):
                    download_and_upload_video(video_url, video_title)
                    collection.insert_one({"title": video_title})
                    logging.info(f'Uploaded and saved video: {video_title}')
                else:
                    logging.info(f'Video already processed: {video_title}')

def download_and_upload_video(video_url, video_title):
    try:
        yt = YouTube(video_url)
        stream = yt.streams.filter(file_extension='mp4').first()
        file_path = stream.download()

        Bot.send_video(chat_id=TELEGRAM_CHAT_ID, video=open(file_path, 'rb'), caption=video_title)
        os.remove(file_path)
        logging.info(f'Uploaded video to Telegram: {video_title}')
    except Exception as e:
        logging.error(f'Failed to download or upload video: {e}')

@Bot.on_message(filters.command("on") & filters.user(bot.OWNER_ID))
async def start_checking(client, message):
    if not scheduler.running:
        scheduler.add_job(check_youtube_channel, 'interval', minutes=1)
        scheduler.start()
        await message.reply("Started checking the YouTube channel for new videos.")
    else:
        await message.reply("The process is already running.")

@Bot.on_message(filters.command("off") & filters.user(bot.OWNER_ID))
async def stop_checking(client, message):
    if scheduler.running:
        scheduler.shutdown()
        await message.reply("Stopped checking the YouTube channel for new videos.")
    else:
        await message.reply("The process is not running.")