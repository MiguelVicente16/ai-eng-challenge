"""Realtime voice call simulator for the DEUS Bank /voice endpoint.

Captures your microphone at 16 kHz linear16 mono, streams it to the
/voice WebSocket, prints each turn's transcript + bot reply as it
arrives, and plays the synthesized reply out loud. Roughly simulates a
phone call with the bot.

Requires:
    - A running server (`make run`) with DEEPGRAM_API_KEY set.
    - A working microphone and speakers (sounddevice uses the OS defaults).

Usage:
    make simulate-call-live
    # or: uv run python scripts/simulate_call_live.py
    # press Ctrl+C to hang up.

Protocol details: see `src/routers/voice.py`. The server sends linear16 PCM
so this script can write straight to an audio output stream with zero
decoding — no ffmpeg or MP3 decoder needed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import numpy as np
import sounddevice as sd
import websockets

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
CHUNK_SAMPLES = 1600  # 100 ms per frame
MIC_QUEUE_MAX = 64


async def _main(url: str) -> int:
    print(f"connecting to {url} ...")
    try:
        async with websockets.connect(url) as ws:
            print("connected. speak into the mic. press Ctrl+C to hang up.\n")
            await _call(ws)
    except (websockets.InvalidStatus, websockets.InvalidHandshake) as exc:
        print(f"handshake failed: {exc}", file=sys.stderr)
        return 1
    except ConnectionRefusedError:
        print("connection refused — is `make run` running?", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nhung up.")
    return 0


async def _call(ws: websockets.ClientConnection) -> None:
    loop = asyncio.get_running_loop()
    mic_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=MIC_QUEUE_MAX)
    playing = asyncio.Event()  # set while the bot reply is playing
    done = asyncio.Event()

    def _safe_put(data: bytes) -> None:
        try:
            mic_queue.put_nowait(data)
        except asyncio.QueueFull:
            pass  # drop oldest implicit via maxsize

    def mic_callback(indata, frames, time_info, status) -> None:  # noqa: ARG001
        if status:
            return
        if playing.is_set():
            return  # mute the mic while the bot is speaking to avoid feedback
        loop.call_soon_threadsafe(_safe_put, bytes(indata))

    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        blocksize=CHUNK_SAMPLES,
        callback=mic_callback,
    )

    async def sender() -> None:
        while not done.is_set():
            try:
                chunk = await asyncio.wait_for(mic_queue.get(), timeout=0.5)
            except TimeoutError:
                continue
            try:
                await ws.send(chunk)
            except websockets.ConnectionClosed:
                done.set()
                return

    async def receiver() -> None:
        while not done.is_set():
            try:
                frame = await ws.recv()
            except websockets.ConnectionClosed:
                done.set()
                return
            if isinstance(frame, str):
                payload = json.loads(frame)
                kind = payload.get("type")
                if kind == "turn":
                    print(f"You: {payload.get('transcript', '')}")
                    print(f"Bot: {payload.get('response', '')}\n")
                elif kind == "done":
                    done.set()
                    return
            else:
                await _play_pcm(frame, playing)

    with stream:
        sender_task = asyncio.create_task(sender())
        receiver_task = asyncio.create_task(receiver())
        try:
            await done.wait()
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await ws.send("__end__")
            except websockets.ConnectionClosed:
                pass
            sender_task.cancel()
            receiver_task.cancel()
            for task in (sender_task, receiver_task):
                try:
                    await task
                except (asyncio.CancelledError, Exception):  # noqa: BLE001
                    pass


async def _play_pcm(audio: bytes, playing: asyncio.Event) -> None:
    """Play linear16 PCM audio via the default output device."""
    playing.set()
    try:
        pcm = np.frombuffer(audio, dtype=np.int16)
        sd.play(pcm, samplerate=SAMPLE_RATE, blocking=False)
        await asyncio.to_thread(sd.wait)
    finally:
        playing.clear()


def main() -> int:
    parser = argparse.ArgumentParser(description="Live mic call simulator")
    parser.add_argument("--url", default="ws://localhost:8000/voice")
    args = parser.parse_args()

    try:
        return asyncio.run(_main(args.url))
    except KeyboardInterrupt:
        print("\nhung up.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
