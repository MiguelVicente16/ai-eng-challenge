"""Push-to-talk voice call simulator for the DEUS Bank /chat endpoint.

Press ENTER to start recording from your mic, press ENTER again to stop
and send. The recorded audio is transcribed by Deepgram Nova on the
server, routed through the agents, and the bot's reply is played back
through your speakers. Press Ctrl+C to hang up.

This is the batch counterpart to `simulate_call_live.py` — simpler and
more deterministic because *you* decide when a turn ends, so it doesn't
depend on Flux's server-side end-of-turn detection.

Requires:
    - A running server (`make run`).
    - `DEEPGRAM_API_KEY` set in `.env` — used by the server for STT, and
      by this script directly for TTS playback.
    - A working microphone and speakers (uses OS defaults).

Usage:
    make simulate-call-ptt
    # or: PYTHONPATH=. uv run python scripts/simulate_call_ptt.py
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import io
import sys
import threading
import time
import wave

import httpx
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
BLOCK_SAMPLES = 320  # 20 ms — tight ENTER-to-stop latency
MIN_RECORDING_SECONDS = 0.3


def _pcm_to_wav_bytes(pcm: bytes) -> bytes:
    """Wrap raw PCM in a WAV container so Deepgram auto-detects the format."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm)
    return buf.getvalue()


def _record_until_enter() -> bytes:
    """Capture mic audio until the user presses ENTER again."""
    frames: list[bytes] = []
    recording = threading.Event()
    recording.set()

    def callback(indata, _frames, _time_info, _status):
        if recording.is_set():
            frames.append(bytes(indata))

    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        blocksize=BLOCK_SAMPLES,
        callback=callback,
    )

    with stream:
        try:
            input()
        except EOFError:
            pass

    recording.clear()
    return b"".join(frames)


async def _send_hello(
    client: httpx.AsyncClient,
    url: str,
    caller_phone: str | None,
) -> dict:
    """Dial the bank — empty first turn that triggers the opener phrase."""
    payload: dict = {
        "message": "",
        "audio_encoding": "linear16",
        "audio_sample_rate": SAMPLE_RATE,
    }
    if caller_phone:
        payload["caller_phone"] = caller_phone
    response = await client.post(url, json=payload, timeout=60.0)
    response.raise_for_status()
    return response.json()


async def _send_turn(
    client: httpx.AsyncClient,
    url: str,
    session_id: str | None,
    pcm: bytes,
) -> dict:
    wav_bytes = _pcm_to_wav_bytes(pcm)
    payload: dict = {
        "message": "",
        "audio_base64": base64.b64encode(wav_bytes).decode("ascii"),
        # ask the server to synthesize linear16 @ 16kHz so we can play the
        # returned bytes directly without decoding MP3 or making a second
        # Deepgram round trip from the client
        "audio_encoding": "linear16",
        "audio_sample_rate": SAMPLE_RATE,
    }
    if session_id:
        payload["session_id"] = session_id
    response = await client.post(url, json=payload, timeout=60.0)
    response.raise_for_status()
    return response.json()


async def _play_pcm_bytes(audio_b64: str | None) -> None:
    """Play linear16 PCM audio bytes returned from the server."""
    if not audio_b64:
        return
    audio = base64.b64decode(audio_b64)
    pcm = np.frombuffer(audio, dtype=np.int16)
    sd.play(pcm, samplerate=SAMPLE_RATE, blocking=False)
    await asyncio.to_thread(sd.wait)


async def _main(url: str, caller_phone: str | None) -> int:
    print("DEUS Bank voice call simulator — push-to-talk mode")
    print(f"server: {url}")
    if caller_phone:
        print(f"caller ID: {caller_phone}")
    print("workflow: ENTER to start speaking, ENTER again to send. Ctrl+C to hang up.\n")
    session_id: str | None = None

    async with httpx.AsyncClient() as client:
        # Dial the bank — server runs the opener, we play the greeting
        print("dialing...")
        start = time.perf_counter()
        try:
            reply = await _send_hello(client, url, caller_phone)
        except httpx.HTTPError as exc:
            print(f"couldn't connect: {exc}", file=sys.stderr)
            return 1
        server_ms = round((time.perf_counter() - start) * 1000)
        session_id = reply.get("session_id")
        greeting = reply.get("response") or ""
        print(f"Bot: {greeting}  [turn: {server_ms}ms]\n")
        await _play_pcm_bytes(reply.get("audio_base64"))

        while True:
            try:
                await asyncio.to_thread(input, "[Press ENTER to start speaking] ")
            except EOFError:
                return 0
            print("recording... press ENTER again to send")
            pcm = await asyncio.to_thread(_record_until_enter)

            duration = len(pcm) / (SAMPLE_RATE * 2)
            if duration < MIN_RECORDING_SECONDS:
                print(f"(too short: {duration:.1f}s — try again)\n")
                continue
            print(f"sending {duration:.1f}s of audio...")

            start = time.perf_counter()
            try:
                reply = await _send_turn(client, url, session_id, pcm)
            except httpx.HTTPError as exc:
                print(f"HTTP error: {exc}\n")
                continue
            server_ms = round((time.perf_counter() - start) * 1000)

            session_id = reply.get("session_id")
            transcript = reply.get("transcript") or "(no transcript)"
            response_text = reply.get("response") or ""
            print(f"You: {transcript}")
            print(f"Bot: {response_text}  [turn: {server_ms}ms]\n")

            await _play_pcm_bytes(reply.get("audio_base64"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Push-to-talk call simulator")
    parser.add_argument("--url", default="http://localhost:8000/chat")
    parser.add_argument(
        "--caller-phone",
        default=None,
        help="Optional caller ID in E.164 format (e.g. +1122334455 for Lisa)",
    )
    args = parser.parse_args()
    try:
        return asyncio.run(_main(args.url, args.caller_phone))
    except KeyboardInterrupt:
        print("\nhung up.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
