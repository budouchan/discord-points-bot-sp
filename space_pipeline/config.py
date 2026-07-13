"""スペース録音パイプラインの設定。

すべて環境変数(.env)で上書き可能。デフォルト値はこのファイルの通り。
.env はカレントディレクトリ(またはその上位)と space_pipeline/ の両方を探す。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # カレントディレクトリから上位に向かって探索
load_dotenv(Path(__file__).parent / ".env")  # パッケージ直下(既存の値は上書きしない)


def _bool(name: str, default: str) -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes", "on")


# ===== OpenAI =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# 文字起こしモデル: whisper-1 / gpt-4o-transcribe / gpt-4o-mini-transcribe など
# (旧設定名 WHISPER_MODEL も後方互換のため読み込む)
TRANSCRIBE_MODEL = os.getenv("TRANSCRIBE_MODEL", os.getenv("WHISPER_MODEL", "whisper-1"))
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
# APIのファイルサイズ上限対策として音声を分割する長さ(秒)
CHUNK_SEC = int(os.getenv("CHUNK_SEC", "600"))
TRANSCRIBE_LANGUAGE = os.getenv("TRANSCRIBE_LANGUAGE", "ja")

# ===== 番組(ブドキン)設定 =====
SHOW_NAME = os.getenv("SHOW_NAME", "ブドキン")
# MC名(空なら文字起こしから推定)
MC_NAME = os.getenv("MC_NAME", "")
# 曜日パーソナリティ: 「月:名前,火:名前,...」形式。空なら文字起こしから推定
WEEKDAY_PERSONALITIES = os.getenv("WEEKDAY_PERSONALITIES", "")
# X投稿の「録音はこちら」に入れるURL(空ならプレースホルダー)
RECORDING_URL = os.getenv("RECORDING_URL", "")
# 毎回必ず付けるハッシュタグ(スペース区切り)
DEFAULT_HASHTAGS = os.getenv("DEFAULT_HASHTAGS", "#ブドキン")

# ===== WordPress =====
WP_DEFAULT_CATEGORY = os.getenv("WP_DEFAULT_CATEGORY", "ブドキン")

# ===== 切り抜き動画 =====
CLIP_ENABLED = _bool("CLIP_ENABLED", "true")
# 動画として書き出す切り抜きの最大本数
CLIP_MAX_COUNT = int(os.getenv("CLIP_MAX_COUNT", "5"))
# 切り抜き動画の解像度(音声波形を描画した映像を生成する)
CLIP_RESOLUTION = os.getenv("CLIP_RESOLUTION", "1280x720")

# ===== Obsidian =====
# Obsidian VaultのパスIを指定すると「YYYY-MM-DD ブドキン.md」として保存
OBSIDIAN_VAULT_DIR = os.getenv("OBSIDIAN_VAULT_DIR", "")

# ===== Discord =====
# Webhook URLを設定すると、Discord用まとめを自動投稿する(空なら生成のみ)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# ===== 出力 =====
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "recordings"))
