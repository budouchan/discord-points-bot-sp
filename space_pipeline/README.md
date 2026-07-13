# ブドキン スペース自動化パイプライン

X(Twitter)スペースをMacで録音し、文字起こしして、
配信後のコンテンツを **`space start` 一発で全部** 作るツールです。

```
space start
  ↓
録音(BlackHole経由・無音検知で自動停止)
  ↓
文字起こし(whisper-1 / gpt-4o-transcribe を .env で切り替え)
  ↓
X投稿(ブドキン形式) → Threads → Discord(自動投稿対応)
  ↓
WordPress(title/slug/excerpt/html/tags/category)
  ↓
Obsidian(「2026-07-13 ブドキン.md」として自動保存)
  ↓
切り抜き動画(clip01.mp4 + clip01.srt)
  ↓
全部完了
```

## セットアップ(初回のみ)

### 1. BlackHoleのインストール(システム音声の録音に必要)

MacはOS標準ではシステム音声(スピーカーから出る音)を録音できないため、
仮想オーディオデバイス [BlackHole](https://existential.audio/blackhole/) を使います。

```bash
brew install blackhole-2ch
```

インストール後、**音声を聞きながら録音する**ために「複数出力装置」を作成します:

1. 「Audio MIDI設定」アプリを開く
2. 左下の「+」→「複数出力装置を作成」
3. 「BlackHole 2ch」と普段使うスピーカー(またはAirPods等)の両方にチェック
4. Macのサウンド出力をこの「複数出力装置」に切り替える

### 2. ffmpegのインストール(音声変換・切り抜き動画生成に必要)

```bash
brew install ffmpeg
```

### 3. `space` コマンドのインストール

リポジトリのルートで:

```bash
pip install -e .
```

これで `space` コマンドがどこからでも使えるようになります。

### 4. 設定

```bash
cp space_pipeline/.env.example space_pipeline/.env
```

`.env` を編集して最低限 `OPENAI_API_KEY` を設定してください。
番組設定(MC名、曜日パーソナリティ、Webhook等)もここで変更できます。

## 使い方

### 毎日の運用はこれだけ

スペースが始まる直前(または直後)に:

```bash
space start
```

- 音声が鳴り始めると自動的に録音開始
- スペースが終わって無音が90秒続くと自動停止
- そのまま文字起こし → 全コンテンツ生成 → Discord投稿 →
  Obsidian保存 → 切り抜き動画生成まで自動で完了します
- Ctrl+C で録音を手動停止してもそのまま次の工程に進みます

### その他のコマンド

```bash
space start --input recording.m4a   # 録音済みファイルから
space start --no-clips              # 切り抜き動画をスキップ
space start --no-generate           # 文字起こしまでで止める
space generate recordings/20260713_2100   # 生成だけやり直す
space clip recordings/20260713_2100       # 切り抜きだけ作り直す
space devices                       # オーディオデバイス一覧(BlackHole確認用)
```

## 出力

セッションごとに `recordings/日付_時刻/` に保存されます:

| ファイル | 内容 |
|---|---|
| `recording.wav` | 録音した音声 |
| `transcript.txt` / `transcript_timestamps.txt` | 文字起こし(全文/タイムスタンプ付き) |
| `segments.json` | セグメント生データ |
| `summary.md` | 要約 |
| `x_post.md` | X投稿(ブドキン形式テンプレート) |
| `threads_post.md` | Threads投稿案 |
| `hashtags.md` | ハッシュタグ |
| `clips.md` / `clips.json` | 切り抜き候補 |
| `clips/clip01.mp4` ... | 切り抜き動画(音声波形の映像付き) |
| `clips/clip01.srt` ... | 切り抜き用字幕 |
| `youtube_description.md` | YouTube概要欄 |
| `wordpress.json` / `blog.html` / `blog.md` | WordPress用記事データ |
| `discord_post.md` | Discord用まとめ |
| `all_content.md` | 上記まとめ(Obsidianにもこれが保存される) |

### X投稿(ブドキン形式)

```
【タイトル】

📅 日付
🎙 MC:
🗓 曜日パーソナリティ:

📌 本日のトピック
・
・

👥 ゲスト:
🪙 幻のごじゃトークン:

🎧 録音はこちら
(URL)

#ブドキン
```

### WordPress(wordpress.json)

```json
{
  "title": "...",
  "slug": "...",
  "excerpt": "...",
  "html": "...",
  "tags": ["..."],
  "category": "ブドキン"
}
```

このJSONをそのままWordPress REST API(`POST /wp-json/wp/v2/posts`)に
渡せる形式です。本文HTMLだけ欲しい場合は `blog.html` を使ってください。

### Discord(discord_post.md)

```
## 今日のまとめ

・
・
・

**明日のテーマ**
(テーマ)
```

`.env` に `DISCORD_WEBHOOK_URL` を設定すると、生成と同時に自動投稿されます。

### Obsidian

`.env` に `OBSIDIAN_VAULT_DIR` を設定すると、
`2026-07-13 ブドキン.md` のようなファイル名でVaultに自動保存されます
(フロントマター付き、タグ: ブドキン/スペース)。

## 設定の調整(.env)

| 変数 | 説明 |
|---|---|
| `TRANSCRIBE_MODEL` | `whisper-1` / `gpt-4o-transcribe` / `gpt-4o-mini-transcribe` |
| `GPT_MODEL` | コンテンツ生成モデル |
| `SILENCE_STOP_SEC` | 自動停止までの無音秒数(長い沈黙がある番組なら大きめに) |
| `SILENCE_THRESHOLD` | 無音判定の音量しきい値(誤停止するなら下げる) |
| `SHOW_NAME` | 番組名(Obsidianのファイル名等に使用) |
| `MC_NAME` / `WEEKDAY_PERSONALITIES` | X投稿テンプレートに使用(空なら文字起こしから推定) |
| `RECORDING_URL` / `DEFAULT_HASHTAGS` | X投稿テンプレートに使用 |
| `WP_DEFAULT_CATEGORY` | WordPressのカテゴリ |
| `CLIP_ENABLED` / `CLIP_MAX_COUNT` / `CLIP_RESOLUTION` | 切り抜き動画 |
| `OBSIDIAN_VAULT_DIR` | Obsidian Vaultのパス |
| `DISCORD_WEBHOOK_URL` | Discord自動投稿用Webhook |

補足:
- `whisper-1` 以外の文字起こしモデルは詳細タイムスタンプ(verbose_json)非対応のため、
  切り抜き候補・YouTube概要欄のタイムスタンプ精度はチャンク単位(デフォルト10分)に
  粗くなります。**切り抜き動画を活用するなら `whisper-1` を推奨**します。
- 旧コマンド `python -m space_pipeline.main` も `space start` 相当として動作します。

## 注意事項

- 録音にはマイク入力の権限が必要です。初回実行時にターミナルへの
  マイクアクセス許可を求められたら「許可」してください
- スペースの録音・二次利用はスピーカーの許可を得た上で行ってください
