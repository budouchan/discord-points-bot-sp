"""`space` コマンドのCLI。

    space start                      # 録音 → 文字起こし → 全コンテンツ生成 → 配信・保存
    space start --input rec.m4a      # 録音済みファイルから
    space start --no-clips           # 切り抜き動画をスキップ
    space generate <セッションDIR>    # 文字起こし済みデータから生成だけやり直す
    space clip <セッションDIR>        # 切り抜き動画・字幕だけ作り直す
    space devices                    # オーディオデバイス一覧
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from . import config


def _require_api_key() -> None:
    if not config.OPENAI_API_KEY:
        sys.exit("エラー: 環境変数 OPENAI_API_KEY を設定してください(.env に記載可)。")


def _load_session(session_dir: Path) -> tuple[str, list[dict]]:
    transcript_path = session_dir / "transcript.txt"
    segments_path = session_dir / "segments.json"
    if not transcript_path.exists() or not segments_path.exists():
        sys.exit(f"エラー: {session_dir} に transcript.txt / segments.json がありません。")
    return (
        transcript_path.read_text(encoding="utf-8"),
        json.loads(segments_path.read_text(encoding="utf-8")),
    )


def _find_audio(session_dir: Path) -> Path | None:
    for name in ("recording.wav", "recording.m4a", "recording.mp3"):
        path = session_dir / name
        if path.exists():
            return path
    return None


def _publish(results: dict, audio_path: Path | None, segments: list[dict],
             session_dir: Path, skip_clips: bool) -> None:
    """生成結果を配信・保存する(Discord投稿 / Obsidian保存 / 切り抜き動画)。"""
    from . import exporter

    exporter.post_to_discord(results["discord"])
    exporter.save_to_obsidian(results["combined_path"])

    if skip_clips or not config.CLIP_ENABLED:
        print("切り抜き動画: スキップしました。")
    else:
        from . import clipper
        clipper.generate_clips(audio_path, results["clips"], segments, session_dir)


def cmd_start(args) -> None:
    _require_api_key()
    session_dir = config.OUTPUT_DIR / datetime.now().strftime("%Y%m%d_%H%M")

    # 1. 録音
    if args.input:
        audio_path = Path(args.input)
        if not audio_path.exists():
            sys.exit(f"エラー: 音声ファイルが見つかりません: {audio_path}")
    else:
        from . import recorder
        audio_path = recorder.record(session_dir / "recording.wav")

    # 2. 文字起こし
    from . import transcriber
    transcript, segments = transcriber.transcribe(audio_path, session_dir)

    if args.no_generate:
        print("文字起こしまで完了しました(--no-generate 指定のため生成はスキップ)。")
        return

    # 3. コンテンツ生成 → 4. 配信・保存・切り抜き
    from . import content_generator
    results = content_generator.generate_all(transcript, segments, session_dir)
    _publish(results, audio_path, segments, session_dir, args.no_clips)

    print("\n=== 全部完了 ===")
    print(f"出力先: {session_dir.resolve()}")


def cmd_generate(args) -> None:
    _require_api_key()
    session_dir = Path(args.session_dir)
    transcript, segments = _load_session(session_dir)

    from . import content_generator
    results = content_generator.generate_all(transcript, segments, session_dir)
    _publish(results, _find_audio(session_dir), segments, session_dir, args.no_clips)

    print("\n=== 完了 ===")
    print(f"出力先: {session_dir.resolve()}")


def cmd_clip(args) -> None:
    session_dir = Path(args.session_dir)
    clips_path = session_dir / "clips.json"
    if not clips_path.exists():
        sys.exit(f"エラー: {clips_path} がありません。先に space generate を実行してください。")
    _, segments = _load_session(session_dir)
    clips = json.loads(clips_path.read_text(encoding="utf-8"))

    from . import clipper
    clipper.generate_clips(_find_audio(session_dir), clips, segments, session_dir)


def cmd_devices(_args) -> None:
    from . import recorder
    recorder.list_devices()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="space",
        description="スペース録音 → 文字起こし → コンテンツ生成・配信を一発実行",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="フルパイプラインを実行(録音から全部)")
    p_start.add_argument("--input", type=Path, help="録音をスキップして音声ファイルから開始")
    p_start.add_argument("--no-generate", action="store_true", help="文字起こしまでで終了")
    p_start.add_argument("--no-clips", action="store_true", help="切り抜き動画の生成をスキップ")
    p_start.set_defaults(func=cmd_start)

    p_gen = sub.add_parser("generate", help="文字起こし済みセッションから生成だけやり直す")
    p_gen.add_argument("session_dir", type=Path, help="transcript.txt があるセッションディレクトリ")
    p_gen.add_argument("--no-clips", action="store_true", help="切り抜き動画の生成をスキップ")
    p_gen.set_defaults(func=cmd_generate)

    p_clip = sub.add_parser("clip", help="切り抜き動画・字幕だけ作り直す")
    p_clip.add_argument("session_dir", type=Path, help="clips.json があるセッションディレクトリ")
    p_clip.set_defaults(func=cmd_clip)

    p_dev = sub.add_parser("devices", help="オーディオデバイス一覧を表示")
    p_dev.set_defaults(func=cmd_devices)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
