import os
import requests

HF_TOKEN = os.getenv("HF_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

async def generate_music(prompt):
    return "🎵 سیستم آهنگ هنوز وصل نشده"

async def generate_video(prompt):
    return "🎬 سیستم ویدیو هنوز وصل نشده"

async def generate_voice(prompt):
    return "🎤 سیستم صدا هنوز وصل نشده"
