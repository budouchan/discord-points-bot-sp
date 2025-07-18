# ポイントシステムBot Ver.2

取引ログ方式を採用した高機能ポイントシステムBotの実装です。メッセージ投稿日を基準として過去の任意の期間のポイント集計が可能です。

## 機能

- リアクションによるポイント付与/減算（取引ログ方式）
- 全期間ランキング表示
- 月間ランキング表示
- 個人ポイント確認
- データベースによる永続的なデータ保存

## 必要条件

- Python 3.8 以上
- 必要なパッケージは requirements.txt に記載されています

## セットアップ

1. 必要なパッケージをインストール：
```bash
pip install -r requirements.txt
```

2. `.env` ファイルを作成し、Discord Bot Tokenを設定：
```
DISCORD_BOT_TOKEN=your_token_here
```

3. Botを実行：
```bash
python main.py
```

## 使用方法

### ポイント付与/減算

- 権限者（ブドウちゃん、さおりんごさん）のみがポイントの付与/減算が可能です
- 対象のリアクション：
  - <:glucose_man:1360489607010975975>: 1ポイント
  - <:saoringo:1378640284358938685>: 1ポイント
  - <:budouchan:1378640247474094180>: 3ポイント
- 自分自身のメッセージやBotのメッセージへのリアクションはポイント対象外です

### コマンド

- `!ランキング`: 全期間のランキングを表示
- `!月間ランキング [YYYY-MM]`: 指定された月のランキングを表示（引数なしで現在の月）
- `!ポイント`: 自分の現在のポイントを表示
