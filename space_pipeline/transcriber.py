"""OpenAIの音声認識APIで音声を文字起こしするモジュール。

対応モデル(.env の TRANSCRIBE_MODEL で切り替え):
- whisper-1: セグメント単位のタイムスタンプ付き(verbose_json)
- gpt-4o-transcribe / gpt-4o-mini-transcribe など新しいモデル:
  セグメントタイムスタンプ非対応のため、チャンク単位のタイムスタンプで代替

APIのファイルサイズ上限(25MB)を回避するため、
ffmpegで音声を一定時間ごとに分割してから順番に文字起こしし、
タイムスタンプをオフセット補正して結合する。
"""

import json
import subprocess
import tempfile
from pathlib import Path

from openai import OpenAI

from . import config


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"コマンド失敗: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout


def _probe_duration(path: Path) -> float:
    out = _run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    return float(out.strip())


def _split_audio(source: Path, workdir: Path) -> list[Path]:
    """音声を16kHzモノラルのm4aに変換しつつCHUNK_SECごとに分割する。"""
    pattern = workdir / "chunk_%04d.m4a"
    _run([
        "ffmpeg", "-y", "-i", str(source),
        "-ac", "1", "-ar", "16000", "-b:a", "64k",
        "-f", "segment", "-segment_time", str(config.CHUNK_SEC),
        str(pattern),
    ])
    chunks = sorted(workdir.glob("chunk_*.m4a"))
    if not chunks:
        raise RuntimeError("音声の分割に失敗しました。")
    return chunks


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


# セグメント単位のタイムスタンプ(verbose_json)に対応しているモデル
SEGMENT_CAPABLE_MODELS = {"whisper-1"}


def _supports_segments(model: str) -> bool:
    return model in SEGMENT_CAPABLE_MODELS


def transcribe(audio_path: Path, output_dir: Path) -> tuple[str, list[dict]]:
    """音声ファイルを文字起こしし、(全文, セグメントのリスト) を返す。

    セグメントは {"start": 秒, "end": 秒, "text": 文字列} の辞書。
    verbose_json 非対応のモデルではチャンク全体を1セグメントとして扱う。
    全文は transcript.txt、タイムスタンプ付きは transcript_timestamps.txt、
    生データは segments.json として output_dir に保存する。
    """
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    model = config.TRANSCRIBE_MODEL
    use_segments = _supports_segments(model)
    segments: list[dict] = []
    offset = 0.0

    with tempfile.TemporaryDirectory() as tmp:
        chunks = _split_audio(audio_path, Path(tmp))
        print(f"文字起こし開始: {len(chunks)} チャンク (モデル: {model})")
        if not use_segments:
            print("  ※ このモデルは詳細タイムスタンプ非対応のため、"
                  f"{config.CHUNK_SEC}秒チャンク単位のタイムスタンプになります")

        for i, chunk in enumerate(chunks, 1):
            print(f"  チャンク {i}/{len(chunks)} を処理中...")
            duration = _probe_duration(chunk)
            with open(chunk, "rb") as f:
                result = client.audio.transcriptions.create(
                    model=model,
                    file=f,
                    language=config.TRANSCRIBE_LANGUAGE,
                    response_format="verbose_json" if use_segments else "json",
                )
            if use_segments:
                for seg in result.segments or []:
                    segments.append({
                        "start": seg.start + offset,
                        "end": seg.end + offset,
                        "text": seg.text.strip(),
                    })
            else:
                text = (result.text or "").strip()
                if text:
                    segments.append({
                        "start": offset,
                        "end": offset + duration,
                        "text": text,
                    })
            offset += duration

    full_text = "\n".join(s["text"] for s in segments)
    timestamped = "\n".join(
        f"[{format_timestamp(s['start'])}] {s['text']}" for s in segments
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "transcript.txt").write_text(full_text, encoding="utf-8")
    (output_dir / "transcript_timestamps.txt").write_text(timestamped, encoding="utf-8")
    (output_dir / "segments.json").write_text(
        json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"文字起こし完了: {output_dir / 'transcript.txt'}")
    return full_text, segments
