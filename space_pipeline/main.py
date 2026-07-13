"""スペース録音 → Whisper文字起こし → コンテンツ一括生成パイプライン。

使い方:
    # フルパイプライン(録音から)
    python -m space_pipeline.main

    # 既存の音声ファイルから(録音をスキップ)
    python -m space_pipeline.main --input recording.m4a

    # 既存の文字起こしから(録音・文字起こしをスキップ)
    python -m space_pipeline.main --transcript-dir recordings/20260713_2100

    # オーディオデバイスの一覧を表示
    python -m space_pipeline.main --list-devices
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from . import config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="スペース録音 → Whisper文字起こし → コンテンツ一括生成"
    )
    parser.add_argument("--input", type=Path, help="録音をスキップして音声ファイルから開始")
    parser.add_argument(
        "--transcript-dir", type=Path,
        help="transcript.txt / segments.json があるディレクトリから開始(録音・文字起こしをスキップ)",
    )
    parser.add_argument("--list-devices", action="store_true", help="オーディオデバイス一覧を表示")
    parser.add_argument("--no-generate", action="store_true", help="文字起こしまでで終了")
    args = parser.parse_args()

    if args.list_devices:
        from . import recorder
        recorder.list_devices()
        return

    if not config.OPENAI_API_KEY:
        sys.exit("エラー: 環境変数 OPENAI_API_KEY を設定してください(.env に記載可)。")

    # 出力ディレクトリ(セッションごとに日時で作成)
    if args.transcript_dir:
        session_dir = args.transcript_dir
    else:
        session_dir = config.OUTPUT_DIR / datetime.now().strftime("%Y%m%d_%H%M")

    # 1. 録音 (--input / --transcript-dir 指定時はスキップ)
    if args.transcript_dir:
        audio_path = None
    elif args.input:
        audio_path = args.input
        if not audio_path.exists():
            sys.exit(f"エラー: 音声ファイルが見つかりません: {audio_path}")
    else:
        from . import recorder
        audio_path = recorder.record(session_dir / "recording.wav")

    # 2. 文字起こし
    if args.transcript_dir:
        transcript_path = session_dir / "transcript.txt"
        segments_path = session_dir / "segments.json"
        if not transcript_path.exists() or not segments_path.exists():
            sys.exit(f"エラー: {session_dir} に transcript.txt / segments.json がありません。")
        transcript = transcript_path.read_text(encoding="utf-8")
        segments = json.loads(segments_path.read_text(encoding="utf-8"))
    else:
        from . import transcriber
        transcript, segments = transcriber.transcribe(audio_path, session_dir)

    if args.no_generate:
        print("文字起こしまで完了しました(--no-generate 指定のため生成はスキップ)。")
        return

    # 3. コンテンツ生成
    from . import content_generator
    content_generator.generate_all(transcript, segments, session_dir)

    print("\n=== 完了 ===")
    print(f"出力先: {session_dir.resolve()}")


if __name__ == "__main__":
    main()
