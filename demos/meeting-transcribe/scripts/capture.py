"""Windows-side: capture system audio (WASAPI loopback) to rolling WAV chunks.

Run on Windows host (NOT in WSL):
    "C:\\Program Files\\Python312\\python.exe" capture.py

Saves CHUNK_SECONDS-second WAV chunks to OUTPUT_DIR. WSL-side transcribe.py
watches the dir, runs faster-whisper on each new chunk, appends transcript.

Stop with Ctrl+C.
"""
from __future__ import annotations

import datetime
import os
import sys
import time
import wave

import pyaudiowpatch as pa

CHUNK_SECONDS = 30
OUTPUT_DIR = r"C:\temp\meeting-audio"
SAMPLE_RATE = 16000  # whisper expects 16kHz; downsample at write
CHANNELS = 1
BUFFER_FRAMES = 1024


def find_loopback_device(p: pa.PyAudio) -> dict:
    """Pick the loopback device matching the default WASAPI output."""
    try:
        default_out = p.get_default_wasapi_device(d_out=True)
    except Exception:
        default_out = None

    candidates = list(p.get_loopback_device_info_generator())
    if not candidates:
        sys.exit("error: no WASAPI loopback devices found")

    if default_out:
        # match by name prefix
        out_name = default_out["name"].split(" (")[0]
        for d in candidates:
            if out_name in d["name"]:
                return d
    return candidates[0]


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sys.stdout.reconfigure(encoding="utf-8")

    with pa.PyAudio() as p:
        device = find_loopback_device(p)
        rate_native = int(device["defaultSampleRate"])
        ch_native = device["maxInputChannels"]
        print(f"capture: {device['name']}")
        print(f"native: rate={rate_native} ch={ch_native}")
        print(f"output: {OUTPUT_DIR}\\chunk_*.wav (mono 16k, {CHUNK_SECONDS}s each)")
        print()

        stream = p.open(
            format=pa.paInt16,
            channels=ch_native,
            rate=rate_native,
            input=True,
            input_device_index=device["index"],
            frames_per_buffer=BUFFER_FRAMES,
        )

        try:
            chunk_idx = 0
            while True:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(OUTPUT_DIR, f"chunk_{ts}.wav")
                target_frames = rate_native * CHUNK_SECONDS
                frames = bytearray()
                read = 0
                while read < target_frames:
                    n = min(BUFFER_FRAMES, target_frames - read)
                    data = stream.read(n, exception_on_overflow=False)
                    frames.extend(data)
                    read += n

                # downsample to 16k mono via wave + average
                # raw is int16 little-endian, ch_native channels interleaved
                import audioop
                if ch_native > 1:
                    frames = audioop.tomono(bytes(frames), 2, 0.5, 0.5)
                if rate_native != SAMPLE_RATE:
                    frames, _ = audioop.ratecv(bytes(frames), 2, 1, rate_native, SAMPLE_RATE, None)

                with wave.open(path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(bytes(frames))
                size_kb = os.path.getsize(path) // 1024
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] saved chunk_{ts}.wav ({size_kb} KB)")
                chunk_idx += 1
        except KeyboardInterrupt:
            print("\nstopped.")
        finally:
            stream.close()


if __name__ == "__main__":
    main()
