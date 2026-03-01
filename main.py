import os
import re
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class AskRequest(BaseModel):
    video_url: str
    topic: str

class AskResponse(BaseModel):
    timestamp: str
    video_url: str
    topic: str


def download_subtitles(video_url: str):
    command = [
        "yt-dlp",
        "--write-auto-sub",
        "--skip-download",
        "--sub-lang", "en",
        "--sub-format", "vtt",
        video_url
    ]
    subprocess.run(command, check=True)


def find_timestamp(topic: str) -> str:
    # Find downloaded VTT file
    vtt_files = [f for f in os.listdir() if f.endswith(".vtt")]
    if not vtt_files:
        raise Exception("No subtitles found")

    with open(vtt_files[0], "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.split("\n\n")

    for block in blocks:
        if topic.lower() in block.lower():
            match = re.search(r"\d{2}:\d{2}:\d{2}", block)
            if match:
                return match.group(0)

    return "00:00:00"


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):

    try:
        download_subtitles(req.video_url)
        timestamp = find_timestamp(req.topic)

        # Cleanup subtitle files
        for f in os.listdir():
            if f.endswith(".vtt"):
                os.remove(f)

        return {
            "timestamp": timestamp,
            "video_url": req.video_url,
            "topic": req.topic
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
