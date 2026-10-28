"""Windows-side: capture microphone input (your own voice) to rolling WAV chunks.

Run on Windows host (NOT in WSL):
    "C:\\Program Files\\Python312\\python.exe" capture-mic.py

Companion to capture.py. capture.py grabs speaker loopback (other people's voices
in a meeting); this script grabs the default microphone (your voice). Run both
in parallel and merge the two transcripts with merge-transcripts.py to recover
basic 2-class diarization (you vs. everyone else).

List input devices first:
    python capture-mic.py --list

Pick a non-default device (e.g. headset mic instead of laptop builtin):
    python capture-mic.py --device-index 7

Saves CHUNK_SECONDS-second WAV chunks to OUTPUT_DIR. WSL-side transcribe.py with
`--watch-dir /mnt/c/temp/meeting-audio-mic --source local-mic` consumes them.

Stop with Ctrl+C.
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
import wave

import pyaudio

CHUNK_SECONDS = 30
OUTPUT_DIR = r"C:\temp\meeting-audio-mic"
SAMPLE_RATE = 16000  # whisper expects 16kHz; downsample at write
BUFFER_FRAMES = 1024


def list_input_devices(p: pyaudio.PyAudio) -> None:
    print("Available input devices:\n")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            default_marker = " (default)" if info["index"] == p.get_default_input_device_info()["index"] else ""
            print(f"  [{info['index']}] {info['name']}{default_marker}")
            print(f"        ch={info['maxInputChannels']} rate={int(info['defaultSampleRate'])}")
    print()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device-index", type=int, default=None,
                    help="Input device index (default: system default mic)")
    ap.add_argument("--output-dir", default=OUTPUT_DIR,
                    help=f"Output directory (default: {OUTPUT_DIR})")
    ap.add_argument("--chunk-seconds", type=int, default=CHUNK_SECONDS,
                    help=f"Chunk length in seconds (default: {CHUNK_SECONDS})")
    ap.add_argument("--list", action="store_true",
                    help="List input devices and exit")
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    sys.stdout.reconfigure(encoding="utf-8")

    p = pyaudio.PyAudio()
    try:
        if args.list:
            list_input_devices(p)
            return

        if args.device_index is not None:
            device = p.get_device_info_by_index(args.device_index)
        else:
            device = p.get_default_input_device_info()

        if device["maxInputChannels"] == 0:
            sys.exit(f"error: device [{device['index']}] {device['name']} is not an input device")

        rate_native = int(device["defaultSampleRate"])
        ch_native = min(device["maxInputChannels"], 2)  # cap at stereo
        print(f"capture: {device['name']} (idx={device['index']})")
        print(f"native:  rate={rate_native} ch={ch_native}")
        print(f"output:  {args.output_dir}\\chunk_*.wav (mono 16k, {args.chunk_seconds}s each)")
        print()

        stream = p.open(
            format=pyaudio.paInt16,
            channels=ch_native,
            rate=rate_native,
            input=True,
            input_device_index=device["index"],
            frames_per_buffer=BUFFER_FRAMES,
        )

        try:
            while True:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                path = os.path.join(args.output_dir, f"chunk_{ts}.wav")
                target_frames = rate_native * args.chunk_seconds
                frames = bytearray()
                read = 0
                while read < target_frames:
                    n = min(BUFFER_FRAMES, target_frames - read)
                    data = stream.read(n, exception_on_overflow=False)
                    frames.extend(data)
                    read += n

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
        except KeyboardInterrupt:
            print("\nstopped.")
        finally:
            stream.close()
    finally:
        p.terminate()


if __name__ == "__main__":
    main()
