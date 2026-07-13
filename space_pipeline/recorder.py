"""Macのシステム音声を録音するモジュール。

BlackHole等の仮想オーディオデバイス経由でスペースの音声を録音し、
一定時間の無音を検知したら「スペース終了」とみなして自動停止する。
"""

import math
import queue
import sys
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

from . import config


def list_devices() -> None:
    """利用可能なオーディオデバイスの一覧を表示する。"""
    print(sd.query_devices())


def find_input_device(name_hint: str) -> int:
    """名前の部分一致で入力デバイスを探してインデックスを返す。"""
    for idx, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0 and name_hint.lower() in dev["name"].lower():
            return idx
    raise RuntimeError(
        f"入力デバイス '{name_hint}' が見つかりません。"
        "`python -m space_pipeline.main --list-devices` で確認し、"
        ".env の INPUT_DEVICE を設定してください。"
    )


def record(output_wav: Path) -> Path:
    """録音を開始し、無音が続いたら自動停止してWAVファイルを返す。

    - 録音開始直後は音が鳴り始めるまで無音タイマーを作動させない
      (スペース開始前に起動しても誤停止しないようにするため)
    - 音が一度でも鳴った後、SILENCE_STOP_SEC 続けて無音なら停止
    - Ctrl+C でも安全に停止できる
    """
    device = find_input_device(config.INPUT_DEVICE)
    dev_info = sd.query_devices(device)
    print(f"録音デバイス: {dev_info['name']}")

    blocksize = int(config.SAMPLE_RATE * 0.5)  # 0.5秒ごとに無音判定
    audio_queue: queue.Queue = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print(f"[warn] {status}", file=sys.stderr)
        audio_queue.put(indata.copy())

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    heard_audio = False
    last_sound_at = time.monotonic()
    started_at = time.monotonic()

    with wave.open(str(output_wav), "wb") as wf:
        wf.setnchannels(config.CHANNELS)
        wf.setsampwidth(2)  # int16
        wf.setframerate(config.SAMPLE_RATE)

        stream = sd.InputStream(
            device=device,
            channels=config.CHANNELS,
            samplerate=config.SAMPLE_RATE,
            blocksize=blocksize,
            dtype="float32",
            callback=callback,
        )
        print("録音を開始しました。スペースの音声を待機中...")
        print(f"(無音が {config.SILENCE_STOP_SEC:.0f} 秒続いたら自動停止 / Ctrl+C で手動停止)")

        try:
            with stream:
                while True:
                    block = audio_queue.get()
                    wf.writeframes((block * 32767).astype(np.int16).tobytes())

                    rms = math.sqrt(float(np.mean(block**2)))
                    now = time.monotonic()

                    if rms >= config.SILENCE_THRESHOLD:
                        if not heard_audio:
                            print("音声を検知しました。録音中...")
                        heard_audio = True
                        last_sound_at = now
                    elif heard_audio and now - last_sound_at >= config.SILENCE_STOP_SEC:
                        print("無音が続いたため録音を自動停止します。")
                        break

                    if now - started_at >= config.MAX_RECORD_SEC:
                        print("最大録音時間に達したため停止します。")
                        break
        except KeyboardInterrupt:
            print("\n手動停止しました。")

    duration = time.monotonic() - started_at
    print(f"録音完了: {output_wav} ({duration / 60:.1f} 分)")
    return output_wav
