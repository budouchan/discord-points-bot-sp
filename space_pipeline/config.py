"""スペース録音パイプラインの設定。

すべて環境変数(.env)で上書き可能。デフォルト値はこのファイルの通り。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ===== OpenAI =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# 文字起こしモデル
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")
# コンテンツ生成モデル
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-5.5")

# ===== 録音 =====
# 入力デバイス名の部分一致で検索(BlackHole等の仮想オーディオデバイス)
INPUT_DEVICE = os.getenv("INPUT_DEVICE", "BlackHole")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "48000"))
CHANNELS = int(os.getenv("CHANNELS", "1"))
# この秒数だけ無音が続いたら自動停止(スペース終了とみなす)
SILENCE_STOP_SEC = float(os.getenv("SILENCE_STOP_SEC", "90"))
# 無音判定のRMSしきい値(0.0〜1.0)。環境ノイズが大きい場合は上げる
SILENCE_THRESHOLD = float(os.getenv("SILENCE_THRESHOLD", "0.01"))
# 録音の最大時間(秒)。保険として設定(デフォルト6時間)
MAX_RECORD_SEC = float(os.getenv("MAX_RECORD_SEC", str(6 * 60 * 60)))

# ===== 文字起こし =====
# Whisper APIのファイルサイズ上限対策として音声を分割する長さ(秒)
CHUNK_SEC = int(os.getenv("CHUNK_SEC", "600"))
TRANSCRIBE_LANGUAGE = os.getenv("TRANSCRIBE_LANGUAGE", "ja")

# ===== 出力 =====
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "recordings"))
