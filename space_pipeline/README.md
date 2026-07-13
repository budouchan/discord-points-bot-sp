# スペース録音 → 文字起こし → コンテンツ一括生成パイプライン

X(Twitter)スペースをMacで録音し、Whisperで文字起こしして、
GPTで以下のコンテンツを全部まとめて生成するツールです。

- 要約
- X投稿(3パターン)
- Threads投稿(2パターン)
- ハッシュタグ
- 切り抜き候補(タイムスタンプ付き)
- YouTube概要欄
- ブログ記事

## 仕組み

```
スペース開始
  ↓
Macが音声を録音(BlackHole経由でシステム音声をキャプチャ)
  ↓
終了したら自動停止(無音が90秒続いたらスペース終了とみなす)
  ↓
Whisper APIで文字起こし(長時間音声は自動分割)
  ↓
GPTで全コンテンツを生成 → Markdownで保存
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

これでスペースの音声がスピーカーとBlackHoleの両方に流れ、
聞きながら録音できるようになります。

### 2. ffmpegのインストール(音声変換・分割に必要)

```bash
brew install ffmpeg
```

### 3. Pythonパッケージのインストール

```bash
cd space_pipeline
pip install -r requirements.txt
```

### 4. APIキーの設定

`.env.example` をコピーして `.env` を作成し、OpenAI APIキーを設定します:

```bash
cp .env.example .env
# .env を編集して OPENAI_API_KEY を記入
```

## 使い方

### フルパイプライン(録音から全部)

スペースが始まる直前(または直後)にリポジトリのルートで実行:

```bash
python -m space_pipeline.main
```

- 音声が鳴り始めると自動的に「録音中」になります
- スペースが終わって無音が90秒続くと自動停止し、
  そのまま文字起こし → コンテンツ生成まで自動で進みます
- Ctrl+C で手動停止もできます(停止後は自動で次の工程に進みます)

### 録音済みの音声ファイルから

```bash
python -m space_pipeline.main --input recording.m4a
```

### 文字起こし済みのデータから(生成だけやり直す)

```bash
python -m space_pipeline.main --transcript-dir recordings/20260713_2100
```

### その他のオプション

```bash
# オーディオデバイスの一覧を確認(BlackHoleが見えるかチェック)
python -m space_pipeline.main --list-devices

# 文字起こしまでで止める(コンテンツ生成しない)
python -m space_pipeline.main --no-generate
```

## 出力

セッションごとに `recordings/日付_時刻/` に保存されます:

| ファイル | 内容 |
|---|---|
| `recording.wav` | 録音した音声 |
| `transcript.txt` | 文字起こし全文 |
| `transcript_timestamps.txt` | タイムスタンプ付き文字起こし |
| `segments.json` | セグメント生データ |
| `summary.md` | 要約 |
| `x_post.md` | X投稿案 |
| `threads_post.md` | Threads投稿案 |
| `hashtags.md` | ハッシュタグ |
| `clips.md` | 切り抜き候補 |
| `youtube_description.md` | YouTube概要欄 |
| `blog.md` | ブログ記事 |
| `all_content.md` | 上記まとめ |

## 設定の調整

`.env` で変更できます(詳細は `config.py` 参照):

- `SILENCE_STOP_SEC` — 自動停止までの無音秒数(デフォルト90秒)。
  スペース中に長い沈黙がありそうなら大きめに
- `SILENCE_THRESHOLD` — 無音判定の音量しきい値。誤停止する場合は下げる、
  いつまでも止まらない場合は上げる
- `GPT_MODEL` / `WHISPER_MODEL` — 使用するモデル

## 注意事項

- 録音にはマイク入力の権限が必要です。初回実行時にターミナルへの
  マイクアクセス許可を求められたら「許可」してください
- スペースの録音・二次利用はスピーカーの許可を得た上で行ってください
