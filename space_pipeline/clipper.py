"""切り抜き候補から動画(mp4)と字幕(srt)を自動生成するモジュール。

- clips.json の各候補について、録音音声をffmpegで切り出し、
  音声波形を描画した映像付きの clipNN.mp4 を生成する
- segments.json のタイムスタンプから、切り抜き区間に対応する
  clipNN.srt 字幕ファイルを生成する
"""

import subprocess
from pathlib import Path

from . import config


def _srt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def make_srt(segments: list[dict], clip_start: float, clip_end: float) -> str:
    """切り抜き区間に重なるセグメントから、切り抜き開始基準のSRTを作る。"""
    entries = []
    index = 1
    for seg in segments:
        if seg["end"] <= clip_start or seg["start"] >= clip_end:
            continue
        start = max(seg["start"], clip_start) - clip_start
        end = min(seg["end"], clip_end) - clip_start
        text = seg["text"].strip()
        if not text or end <= start:
            continue
        entries.append(f"{index}\n{_srt_time(start)} --> {_srt_time(end)}\n{text}\n")
        index += 1
    return "\n".join(entries)


def _cut_clip(audio_path: Path, start: float, end: float, output_mp4: Path) -> None:
    """音声を切り出し、波形を描画した映像付きmp4を書き出す。"""
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
        "-i", str(audio_path),
        "-filter_complex",
        f"[0:a]showwaves=s={config.CLIP_RESOLUTION}:mode=cline:colors=white[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        str(output_mp4),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpegによる切り抜きに失敗しました:\n{result.stderr[-2000:]}")


def generate_clips(
    audio_path: Path,
    clips: list[dict],
    segments: list[dict],
    output_dir: Path,
) -> list[Path]:
    """切り抜き候補から clipNN.mp4 と clipNN.srt を生成する。"""
    if not clips:
        print("切り抜き候補がないため、動画生成をスキップします。")
        return []
    if not audio_path or not Path(audio_path).exists():
        print("録音音声が見つからないため、切り抜き動画の生成をスキップします。")
        return []

    clips_dir = output_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    targets = clips[: config.CLIP_MAX_COUNT]
    print(f"切り抜き動画を生成中: {len(targets)} 本")
    for i, clip in enumerate(targets, 1):
        name = f"clip{i:02d}"
        mp4_path = clips_dir / f"{name}.mp4"
        srt_path = clips_dir / f"{name}.srt"
        print(f"  {name}: {clip['title']} "
              f"({clip['end'] - clip['start']:.0f}秒)")

        _cut_clip(Path(audio_path), clip["start"], clip["end"], mp4_path)
        srt_path.write_text(
            make_srt(segments, clip["start"], clip["end"]), encoding="utf-8"
        )
        created.extend([mp4_path, srt_path])

    print(f"切り抜き完了: {clips_dir}")
    return created
