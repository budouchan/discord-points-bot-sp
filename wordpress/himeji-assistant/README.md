# 姫路の種アシスタント (himeji-assistant)

WordPress の投稿編集画面に「姫路の種アシスタント」パネルを追加するプラグインです。
第1弾機能として **リンクカード検索** を搭載しています。ライターは HTML を書かずに、
キーワード検索 → 「カードを挿入」ボタンだけで関連記事カードを本文に入れられます。

## できること(v0.1.0)

- 投稿・固定ページの編集画面の右サイドバーに「姫路の種アシスタント」を表示
  - ブロックエディタ(Gutenberg): 右上の電球アイコン、またはオプションメニューから開くサイドバー
  - クラシックエディタ: サイドバーのメタボックス
- キーワードで公開済み記事をインクリメンタル検索(350ms デバウンス、専用の軽量 REST API)
- 検索結果にタイトル・URL・アイキャッチ(サムネイル)を表示
- 「カードを挿入」ボタンで、現在のカーソル位置に `[himeji_card id="123"]` ショートコードを挿入
  - ブロックエディタでは `core/shortcode` ブロックとして挿入
  - クラシックエディタでは TinyMCE / テキストエディタのカーソル位置に挿入
- ショートコードはフロントでリンクカード(アイキャッチ+ラベル+タイトル+抜粋)として表示
  - ID 参照なので、リンク先のタイトルやアイキャッチが後で変わっても常に最新表示

## インストール

1. この `himeji-assistant` フォルダを ZIP 圧縮する
   (またはフォルダごと `wp-content/plugins/` にアップロード)
2. WordPress 管理画面 → プラグイン → 新規追加 → プラグインのアップロード → ZIP を選択
3. 有効化する
4. 投稿編集画面を開き、右上の電球アイコン(またはメタボックス)から利用開始

要件: WordPress 5.9 以上 / PHP 7.4 以上を想定。ビルド工程は不要です。

## ショートコード

```
[himeji_card id="123"]
[himeji_card id="123" label="関連記事"]
```

- `id`: リンク先記事の投稿 ID(検索パネルが自動で入れるので手書き不要)
- `label`: カード左上のラベル。省略時は「あわせて読みたい」
  (`himeji_assistant_card_label` フィルターでサイト全体の既定値を変更可能)

## REST API

```
GET /wp-json/himeji-assistant/v1/search?q=キーワード&per_page=10
```

- 権限: `edit_posts` を持つログインユーザーのみ(ライター以上)
- レスポンス: `[{ id, title, url, date, thumbnail }, ...]`
- `no_found_rows` などで最適化した軽量クエリ。検索対象の投稿タイプは
  `himeji_assistant_search_post_types` フィルターで変更できます。

## 「編集OS」への拡張について

このプラグインは、将来的に以下のような機能を同じサイドバーに足していく前提で
設計しています(地図検索・過去記事検索・パーマリンク自動生成・カテゴリー/タグ提案・
公開前チェック・AI校正・AI関連記事推薦 など)。

新しいパネルの追加手順:

1. **PHP 側**: 必要なら REST エンドポイントを `himeji-assistant/v1` 名前空間に追加
   (`includes/class-himeji-assistant-rest.php` 参照)
2. **JS 側**: エディタで読み込まれるスクリプトから 1 回呼ぶだけ:

```js
window.HimejiAssistant.registerPanel( {
	name: 'category-suggest',
	title: 'カテゴリー提案',
	render: MyPanelComponent, // wp.element コンポーネント
} );
```

登録したパネルはサイドバー内に `PanelBody`(開閉パネル)として自動で並びます。
AI 関連記事推薦を追加する場合は、`/search` と同じレスポンス形式
(`id, title, url, thumbnail`)で推薦エンドポイントを作れば、
検索結果 UI と「カードを挿入」ボタンをそのまま流用できます。

## ファイル構成

```
himeji-assistant/
├── himeji-assistant.php                       # プラグイン本体(ブートストラップ)
├── includes/
│   ├── class-himeji-assistant-rest.php        # 検索 REST API
│   ├── class-himeji-assistant-shortcode.php   # [himeji_card] ショートコード
│   └── class-himeji-assistant-admin.php       # 編集画面への組み込み
└── assets/
    ├── js/editor-sidebar.js                   # ブロックエディタ用サイドバー
    ├── js/classic-metabox.js                  # クラシックエディタ用メタボックス
    ├── css/admin.css                          # 管理画面スタイル
    └── css/card.css                           # フロントのカードスタイル
```
