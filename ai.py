import requests
from config import HF_TOKEN

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}


def hf_generate(model, payload):
    url = f"https://api-inference.huggingface.co/models/{model}"
    r = requests.post(url, headers=HEADERS, json=payload)
    return r.content


# 🎵 Music (Khala / MusicGen)
def generate_music(text):
    return hf_generate(
        "facebook/musicgen-small",
        {"inputs": text}
    )


# 🎬 Video (CogVideoX)
def generate_video(text):
    return hf_generate(
        "zai-org/CogVideoX-5b",
        {"inputs": text}
    )


# 🗣️ Voice (TTS)
def generate_voice(text):
    return hf_generate(
        "NAMAA-Space/NAMAA-Saudi-TTS-V2",
        {"inputs": text}
    )
