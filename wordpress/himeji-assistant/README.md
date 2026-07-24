# 姫路の種アシスタント — 姫路の種 編集OS

WordPress の投稿編集画面に「姫路の種アシスタント」サイドバーを追加するプラグインです。
単機能ツールではなく、ライター全員が使う **「編集OS」** として設計されています:

- すべての機能は「パネル」として実装され、1つのサイドバーに並ぶ
- パネルはユーザーごとに表示/非表示を切り替えられる(サイドバー内の「パネル設定」)
- 外部プラグインからもパネルを追加できる(アクションフック1つ)
- AI機能は独立した「AIサービス層」経由で使い、ChatGPT / Claude / Gemini などの
  プロバイダーを差し替え・追加できる

## 搭載パネル

| パネル | 状態 |
| --- | --- |
| リンクカード検索 | ✅ v0.2.0 |
| AI関連記事推薦 / カテゴリー提案 / タグ提案 / パーマリンク生成 / 公開前チェック / SEOチェック / 地図・住所検索 / Googleマップ埋め込み / よく使うショートコード / 定型文 / ライター向けチェックリスト | 🚧 ロードマップ(この基盤に順次追加) |

### リンクカード検索

- キーワードで公開済み記事をインクリメンタル検索(350ms デバウンス、軽量 REST API)
- 検索結果にタイトル・URL・アイキャッチを表示
- 「カードを挿入」で現在のカーソル位置に `[himeji_card id="123"]` を挿入
- フロントではアイキャッチ+ラベル+タイトル+抜粋のリンクカードとして表示。
  ID 参照なので、リンク先のタイトルやアイキャッチが変わっても常に最新表示
- クラシックエディタでもメタボックスとして利用可能

```
[himeji_card id="123"]
[himeji_card id="123" label="関連記事"]
```

## インストール

1. この `himeji-assistant` フォルダを ZIP 圧縮する
   (またはフォルダごと `wp-content/plugins/` にアップロード)
2. 管理画面 → プラグイン → 新規追加 → プラグインのアップロード → ZIP を選択して有効化
3. 投稿編集画面の右上・電球アイコンから「姫路の種アシスタント」を開く

要件: WordPress 5.9 以上 / PHP 7.4 以上。ビルド工程は不要です。

## アーキテクチャ

```
┌───────────────────────────────────────────────┐
│  サイドバー「姫路の種アシスタント」(assistant-core.js)  │
│  ├── パネル: リンクカード検索                        │
│  ├── パネル: (今後追加…)                           │
│  └── パネル設定(ユーザーごとの表示/非表示)            │
└──────────────┬────────────────────────────────┘
               │ REST (himeji-assistant/v1)
┌──────────────┴────────────────────────────────┐
│  PHP コア                                      │
│  ├── Himeji_Assistant_Core   … パネルレジストリ   │
│  ├── Himeji_Assistant_Panel  … パネル基底クラス    │
│  ├── Himeji_Assistant_REST   … /prefs(設定保存)  │
│  ├── Himeji_Assistant_AI     … AIサービス層       │
│  └── panels/…               … 各パネルの実装      │
└───────────────────────────────────────────────┘
```

```
himeji-assistant/
├── himeji-assistant.php                     # ブートストラップ + 内蔵パネル登録
├── includes/
│   ├── class-himeji-assistant-core.php      # パネルレジストリ
│   ├── class-himeji-assistant-panel.php     # パネル基底クラス
│   ├── class-himeji-assistant-rest.php      # コアREST(パネル表示設定)
│   ├── class-himeji-assistant-ai.php        # AIサービス層(プロバイダー登録制)
│   ├── class-himeji-assistant-admin.php     # 編集画面への組み込み
│   └── panels/
│       └── class-himeji-panel-link-card-search.php
└── assets/
    ├── js/assistant-core.js                 # サイドバーの器 + パネル登録API + AIヘルパー
    ├── js/panels/link-card-search.js        # リンクカード検索パネルUI
    ├── js/classic-metabox.js                # クラシックエディタ用
    ├── css/admin.css
    └── css/card.css
```

## パネルの追加方法

新機能 = 新パネル。手順は2ステップです。

### 1. PHP: パネルクラスを作って登録

```php
class Himeji_Panel_Category_Suggest extends Himeji_Assistant_Panel {
    public function id()          { return 'category-suggest'; }
    public function title()       { return 'カテゴリー提案'; }
    public function description() { return '本文からカテゴリーを提案します。'; }
    public function order()       { return 30; }

    public function register() {
        // 必要なら REST ルートやショートコードをここで登録
    }

    public function editor_script() {
        return array(
            'handle' => 'himeji-panel-category-suggest',
            'src'    => plugin_dir_url( __FILE__ ) . 'category-suggest.js',
            'deps'   => array(),
        );
    }
}

add_action( 'himeji_assistant_register_panels', function ( $core ) {
    $core->register_panel( new Himeji_Panel_Category_Suggest() );
} );
```

このアクションは外部プラグインからも使えるので、パネルを別プラグインとして
配布・管理することもできます。

### 2. JS: パネルUIを登録

```js
window.HimejiAssistant.registerPanel( {
    name: 'category-suggest',      // PHP側の id と揃える
    title: 'カテゴリー提案',
    order: 30,
    render: MyPanelComponent,      // wp.element コンポーネント(ビルド不要)
} );
```

登録したパネルは自動的にサイドバーに並び、「パネル設定」での表示/非表示の
対象になります。パネルIDは PHP と JS で揃えてください。

## AIサービス層

パネルとAIは疎結合です。パネル側は共通ヘルパーを呼ぶだけ:

```js
if ( window.HimejiAssistant.ai.available ) {
    window.HimejiAssistant.ai.complete( prompt, { task: 'category-suggest', postId: 123 } )
        .then( function ( res ) {
            console.log( res.provider, res.result );
        } );
}
```

背後のAIは「プロバイダー」として追加します。ChatGPT / Claude / Gemini の
どれを使うかはパネル側のコードに一切影響しません:

```php
class Himeji_Claude_Provider implements Himeji_Assistant_AI_Provider {
    public function id()            { return 'claude'; }
    public function label()         { return 'Claude (Anthropic)'; }
    public function is_configured() { return (bool) get_option( 'my_claude_api_key' ); }

    public function complete( $prompt, array $args = array() ) {
        // wp_remote_post() で API を呼び、結果テキストを返す。
        // 失敗時は WP_Error を返す。
    }
}

add_filter( 'himeji_assistant_ai_providers', function ( $providers ) {
    $provider = new Himeji_Claude_Provider();
    $providers[ $provider->id() ] = $provider;
    return $providers;
} );
```

- 使用プロバイダーの選択: オプション `himeji_assistant_ai_provider` に ID を設定
  (未設定なら「設定済みの最初のプロバイダー」が使われる)
- REST: `POST /himeji-assistant/v1/ai/complete` `{ prompt, task, post_id }`
- プロバイダー未設定時は 501 を返し、JS側は `ai.available` で事前判定できる

## REST API

| エンドポイント | 内容 |
| --- | --- |
| `GET /himeji-assistant/v1/search?q=…` | 記事検索(リンクカード検索パネル) |
| `GET/POST /himeji-assistant/v1/prefs` | パネル表示設定の取得/保存(ユーザーごと) |
| `POST /himeji-assistant/v1/ai/complete` | AIサービス層への窓口 |

すべて `edit_posts` 権限(ライター以上)が必要です。

## 主なフック

| フック | 用途 |
| --- | --- |
| `himeji_assistant_register_panels` (action) | パネルの追加 |
| `himeji_assistant_ai_providers` (filter) | AIプロバイダーの追加 |
| `himeji_assistant_ai_active_provider` (filter) | 使用プロバイダーの強制指定 |
| `himeji_assistant_post_types` (filter) | アシスタントを出す投稿タイプ |
| `himeji_assistant_search_post_types` (filter) | 検索対象の投稿タイプ |
| `himeji_assistant_card_label` (filter) | リンクカードの既定ラベル |
