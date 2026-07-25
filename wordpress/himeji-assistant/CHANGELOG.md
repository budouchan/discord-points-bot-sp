# 変更履歴

このプロジェクトの変更点を記録する。形式は [Keep a Changelog](https://keepachangelog.com/ja/) に、
バージョン番号は [セマンティック バージョニング](https://semver.org/lang/ja/) に従う。

- **メジャー (1.x → 2.x)**: 後方互換のない変更(ショートコードの出力・属性の廃止、パネルAPIの破壊的変更など)
- **マイナー (0.4 → 0.5)**: 機能追加(新パネル、新オプション)。後方互換は維持
- **パッチ (0.4.0 → 0.4.1)**: バグ修正・文言修正のみ

## [0.4.1] - 2026-07-25

### 追加
- バージョン管理とデータマイグレーションの基盤(`Himeji_Assistant_Upgrade`)。
  オプション `himeji_assistant_db_version` でデータ形式のバージョンを管理し、
  プラグイン更新時に必要なマイグレーションを古い順に自動実行する
- `uninstall.php`: プラグイン削除時にオプション・ユーザーメタ・キャッシュを全削除
- `CHANGELOG.md`(このファイル)と README の開発者向けドキュメント

## [0.4.0] - 2026-07-25

### 追加
- お気に入りパネル(★): ライターごとによく使うパネルをサイドバー上部に固定
- サイドバーの省スペース化: 開いた状態で表示するのはお気に入り(未設定時は先頭の1つ)のみ
- パネル利用回数の記録(`POST /usage`、パネル別・日別・90日保持・個人は記録しない)
- 設定画面に「パネル利用状況」(直近7日/30日の集計と比較バー)
- コアJS: `HimejiAssistant.trackUsage()`、`ArticleList` の `panel` プロパティ

### 変更
- `POST /prefs` が `hidden` / `favorites` の部分更新に対応(どちらも省略可)

## [0.3.0] - 2026-07-25

### 追加
- Googleマップ検索パネル: 店名・住所 → 候補表示(緯度経度付き)→ `[himeji_map]` 挿入。
  候補検索は Places API(サーバー側・1時間キャッシュ)、埋め込みはAPIキー不要の iframe
- よく使うショートコードパネル(`himeji_assistant_snippets` フィルターで変更可)
- AI関連記事推薦パネル: 「WordPressが検索 → AIが並び替え」構成。AI未設定時はスコア順
- リンクカード検索に並び順(関連度順/新着順/人気順)を追加
- 設定画面(設定 → 姫路の種アシスタント): Google Maps APIキー・AIプロバイダー選択
- コアJSに共通部品: `insertShortcode` / `insertBlockAtCursor` / `ui.ArticleList`

## [0.2.0] - 2026-07-24

### 変更
- 「編集OS」基盤へ再設計。全機能をパネルとして登録する構造
  (`Himeji_Assistant_Core` / `Himeji_Assistant_Panel` /
  `himeji_assistant_register_panels` アクション)
- パネルの表示/非表示設定(ユーザーごと、`GET/POST /prefs`)
- AIサービス層(`Himeji_Assistant_AI_Provider` インターフェース +
  `himeji_assistant_ai_providers` フィルター + `POST /ai/complete`)

## [0.1.0] - 2026-07-24

### 追加
- 初版。リンクカード検索(`GET /search`)、`[himeji_card]` ショートコード、
  ブロックエディタ用サイドバー、クラシックエディタ用メタボックス
