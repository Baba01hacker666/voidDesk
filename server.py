# server.py
import subprocess
import asyncio
import websockets

async def stream(ws):
    ffmpeg = subprocess.Popen([
        "ffmpeg",
        "-f", "x11grab",
        "-video_size", "1024x768",
        "-i", ":0",
        "-vcodec", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-f", "mpegts",
        "-"
    ], stdout=subprocess.PIPE)

    try:
        while True:
            data = ffmpeg.stdout.read(1024)
            if not data:
                break
            await ws.send(data)
    finally:
        ffmpeg.kill()

async def main():
    async with websockets.serve(stream, "0.0.0.0", 8765):
        await asyncio.Future()

asyncio.run(main())
