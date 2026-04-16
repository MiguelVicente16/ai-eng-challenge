"""Stream a raw PCM file to the /voice WebSocket and print replies.

Usage:
    uv run python scripts/simulate_voice.py path/to/audio.raw

Expected format: linear16 PCM, 16 kHz, mono. Convert any source with:
    ffmpeg -i input.mp3 -f s16le -ar 16000 -ac 1 -y out.raw
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import websockets


async def _run(url: str, raw_path: Path, chunk_size: int) -> None:
    audio = raw_path.read_bytes()
    print(f"streaming {len(audio)} bytes from {raw_path} to {url}")
    async with websockets.connect(url) as ws:
        sender = asyncio.create_task(_send_frames(ws, audio, chunk_size))
        receiver = asyncio.create_task(_receive_frames(ws))
        await sender
        await ws.send("__end__")
        await receiver


async def _send_frames(ws, audio: bytes, chunk_size: int) -> None:
    for i in range(0, len(audio), chunk_size):
        await ws.send(audio[i : i + chunk_size])
        await asyncio.sleep(0.05)  # simulate real-time pacing


async def _receive_frames(ws) -> None:
    reply_counter = 0
    while True:
        try:
            frame = await ws.recv()
        except websockets.ConnectionClosed:
            return
        if isinstance(frame, str):
            payload = json.loads(frame)
            print(f"[TEXT] {payload}")
            if payload.get("type") == "done":
                return
        else:
            reply_counter += 1
            out = Path(f"reply_{reply_counter}.mp3")
            out.write_bytes(frame)
            print(f"[AUDIO] saved {len(frame)} bytes -> {out}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stream audio to /voice")
    parser.add_argument("audio", type=Path, help="linear16 16kHz mono PCM file")
    parser.add_argument("--url", default="ws://localhost:8000/voice")
    parser.add_argument("--chunk-size", type=int, default=2560)
    args = parser.parse_args()

    if not args.audio.exists():
        print(f"file not found: {args.audio}", file=sys.stderr)
        return 2

    asyncio.run(_run(args.url, args.audio, args.chunk_size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
