# 姫路の種アシスタント — 姫路の種 編集OS

WordPress の投稿編集画面に「姫路の種アシスタント」サイドバーを追加するプラグインです。
単機能ツールではなく、ライター全員が使う **「編集OS」** として設計されています:

- すべての機能は「パネル」として実装され、1つのサイドバーに並ぶ
- **お気に入り(★)**: ライターごとによく使うパネルを上に固定できる。
  お気に入りだけ開いた状態で表示され、他は畳まれるのでサイドバーが長くならない
- パネルはユーザーごとに表示/非表示を切り替えられる(サイドバー内の「パネル設定」)
- **利用状況の計測**: 「挿入」などの実アクションをパネル別・日別に記録(90日保持)。
  設定 → 姫路の種アシスタント で直近7日/30日の集計を確認でき、
  どのパネルを前面に出すか・削るかをデータで判断できる
- 外部プラグインからもパネルを追加できる(アクションフック1つ)
- AI機能は独立した「AIサービス層」経由で使い、ChatGPT / Claude / Gemini などの
  プロバイダーを差し替え・追加できる

## 搭載パネル

| パネル | 状態 |
| --- | --- |
| リンクカード検索 | ✅ v0.1.0〜 |
| Googleマップ検索 | ✅ v0.3.0 |
| よく使うショートコード | ✅ v0.3.0 |
| AI関連記事推薦 | ✅ v0.3.0(AI未設定でも動作) |
| 公開前チェック / カテゴリー提案 / タグ提案 / パーマリンク生成 / SEOチェック / 定型文 / ライター向けチェックリスト | 🚧 ロードマップ(この基盤に順次追加) |

### リンクカード検索

- キーワードで公開済み記事をインクリメンタル検索(350ms デバウンス、軽量 REST API)。
  タイトルだけでなく**本文・抜粋も検索対象**
- 並び順を選択可能: **関連度順 / 新着順 / 人気順**
  - 人気順は既定でコメント数順。閲覧数プラグイン(WP-PostViews等)を使っている場合は
    `himeji_assistant_views_meta_key` フィルターでメタキーを指定すると閲覧数順になる
- 検索結果にタイトル・URL・アイキャッチを表示
- 「カードを挿入」で現在のカーソル位置に `[himeji_card id="123"]` を挿入
- フロントではアイキャッチ+ラベル+タイトル+抜粋のリンクカードとして表示。
  ID 参照なので、リンク先のタイトルやアイキャッチが変わっても常に最新表示
- クラシックエディタでもメタボックスとして利用可能

```
[himeji_card id="123"]
[himeji_card id="123" label="関連記事"]
```

### Googleマップ検索

Googleマップをブラウザで開いて埋め込みコードをコピーする作業を、
編集画面内で完結させるパネル。

- 店名・住所を入力すると候補を表示(名称・住所・**緯度経度**)
- 「地図を挿入」でカーソル位置に `[himeji_map]` を挿入
- 「緯度経度をコピー」でクリップボードにコピー
- 候補検索には Google **Places API** のAPIキーが必要
  (設定 → 姫路の種アシスタント。キーはサーバー側でのみ使用され、結果は1時間キャッシュ)
- キー未設定でも「検索語をそのまま地図にして挿入」は利用可能
- 埋め込み表示自体はAPIキー不要の iframe を使うため、閲覧数課金は発生しない

```
[himeji_map q="餃子のかっちゃん 姫路駅前店" lat="34.826" lng="134.690" zoom="16" height="360"]
```

出力の `data-name` / `data-lat` / `data-lng` 属性は、将来の
「公開前チェック」(地図・住所の有無チェック)から機械的に読める形にしてある。

### よく使うショートコード

吹き出し(左右)・関連記事カード・ボタン・SNS埋め込みをワンクリック挿入。
一覧は `himeji_assistant_snippets` フィルターで自由に変更でき、
テーマ独自のショートコードや定型文(あいさつ文など)も同じ仕組みで並べられる。

```php
add_filter( 'himeji_assistant_snippets', function ( $items ) {
    $items[] = array(
        'id'          => 'greeting',
        'label'       => '書き出しあいさつ',
        'template'    => 'こんにちは、姫路の種です!',
        'description' => '記事冒頭の定型あいさつ',
    );
    return $items;
} );
```

### AI関連記事推薦

構成は **「WordPressが検索 → AIが選ぶ」**。AIは検索エンジンではなく並び替え役。

1. WordPress がタイトル検索+同カテゴリー+新着から候補を最大20件収集(高速なインデックス検索)
2. AIプロバイダー設定済みなら、候補の**タイトル一覧だけ**をAIに渡して最適な記事を選ばせる
   (毎回全記事を読ませない = 高速・低コスト。AIの回答は候補に実在するIDのみ採用)
3. AI未設定なら、共通カテゴリー数によるスコア順で表示(この状態でも実用になる)

結果はリンクカード検索と同じUIなので、そのまま「カードを挿入」できる。

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
├── uninstall.php                            # プラグイン削除時のデータ後始末
├── CHANGELOG.md                             # 変更履歴
├── includes/
│   ├── class-himeji-assistant-core.php      # パネルレジストリ
│   ├── class-himeji-assistant-panel.php     # パネル基底クラス
│   ├── class-himeji-assistant-rest.php      # コアREST(パネル設定)
│   ├── class-himeji-assistant-ai.php        # AIサービス層(プロバイダー登録制)
│   ├── class-himeji-assistant-usage.php     # パネル利用回数の記録
│   ├── class-himeji-assistant-upgrade.php   # DBバージョン管理・マイグレーション
│   ├── class-himeji-assistant-settings.php  # 設定画面(APIキー・AIプロバイダー・利用状況)
│   ├── class-himeji-assistant-admin.php     # 編集画面への組み込み
│   └── panels/
│       ├── class-himeji-panel-link-card-search.php
│       ├── class-himeji-panel-map-search.php
│       ├── class-himeji-panel-snippets.php
│       └── class-himeji-panel-related-suggest.php
└── assets/
    ├── js/assistant-core.js                 # サイドバーの器 + パネル登録API + 共通UI + AIヘルパー
    ├── js/panels/link-card-search.js
    ├── js/panels/map-search.js
    ├── js/panels/snippets.js
    ├── js/panels/related-suggest.js
    ├── js/classic-metabox.js                # クラシックエディタ用
    ├── css/admin.css
    └── css/card.css
```

コアJSは共通部品も提供する。パネル実装から使える:

- `HimejiAssistant.insertShortcode( text )` … カーソル位置にショートコード挿入
- `HimejiAssistant.insertBlockAtCursor( block )` … 任意ブロック挿入
- `HimejiAssistant.ui.ArticleList` … 記事リストUI(検索・AI推薦で共用。`panel` を渡すと挿入時に利用記録)
- `HimejiAssistant.trackUsage( panelId )` … 利用記録(実アクション時にパネルから呼ぶ)
- `HimejiAssistant.ai.complete( prompt, opts )` … AIサービス層

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
| `GET /himeji-assistant/v1/search?q=…&orderby=relevance\|date\|popular` | 記事検索 |
| `GET /himeji-assistant/v1/maps/search?q=…` | 地図候補検索(要APIキー、1時間キャッシュ) |
| `POST /himeji-assistant/v1/recommend` | 関連記事推薦(WPが検索→AIが並び替え) |
| `GET/POST /himeji-assistant/v1/prefs` | パネル設定の取得/保存(hidden=非表示, favorites=お気に入り。ユーザーごと) |
| `POST /himeji-assistant/v1/usage` | パネル利用の記録(パネル別・日別のサイト全体集計) |
| `POST /himeji-assistant/v1/ai/complete` | AIサービス層への窓口 |

すべて `edit_posts` 権限(ライター以上)が必要です。

## 主なフック

| フック | 用途 |
| --- | --- |
| `himeji_assistant_register_panels` (action) | パネルの追加 |
| `himeji_assistant_ai_providers` (filter) | AIプロバイダーの追加 |
| `himeji_assistant_ai_active_provider` (filter) | 使用プロバイダーの強制指定 |
| `himeji_assistant_post_types` (filter) | アシスタントを出す投稿タイプ |
| `himeji_assistant_search_post_types` (filter) | 検索・推薦対象の投稿タイプ |
| `himeji_assistant_views_meta_key` (filter) | 人気順で使う閲覧数メタキー |
| `himeji_assistant_snippets` (filter) | よく使うショートコードの一覧 |
| `himeji_assistant_card_label` (filter) | リンクカードの既定ラベル |

## 保存データ一覧

このプラグインがDBに保存するデータの全リスト。形式を変えるときは必ず
マイグレーションを書くこと(後述「バージョンアップ時の注意」)。

| 種類 | キー | 内容 |
| --- | --- | --- |
| option | `himeji_assistant_db_version` | データ形式のバージョン(マイグレーション判定用) |
| option | `himeji_assistant_install_version` | 初回インストール時のバージョン |
| option | `himeji_assistant_usage` | パネル利用回数(日別×パネル別、90日分) |
| option | `himeji_assistant_gmaps_api_key` | Google Maps APIキー |
| option | `himeji_assistant_ai_provider` | 使用するAIプロバイダーID |
| user meta | `himeji_assistant_hidden_panels` | 非表示パネル(ユーザーごと) |
| user meta | `himeji_assistant_favorite_panels` | お気に入りパネル(ユーザーごと) |
| transient | `himeji_maps_*` | 地図検索キャッシュ(1時間) |

カスタムテーブルは作らない方針。プラグイン削除時は `uninstall.php` が
上記をすべて削除する(無効化では消えない)。

---

# 開発者向けドキュメント

## 新しいパネルを追加する手順

新機能 = 新パネル。コアには手を入れず、以下のチェックリストで追加する。

1. **パネルID を決める** — 英小文字とハイフン(例: `pre-publish-check`)。
   PHP と JS で同じIDを使う。**一度リリースしたIDは変更しない**
   (お気に入り・非表示設定・利用統計がIDに紐づくため)
2. **PHPクラスを作る** — `includes/panels/class-himeji-panel-<id>.php` に
   `Himeji_Assistant_Panel` を継承したクラスを作成
   - `id()` / `title()` / `description()` / `order()` を実装
   - RESTが必要なら `register()` 内で `rest_api_init` にフックし、
     名前空間は `Himeji_Assistant_REST::NAMESPACE`、権限は
     `Himeji_Assistant_REST::can_use` を使う
   - ショートコードを出す場合も `register()` で登録する
3. **JSを作る** — `assets/js/panels/<id>.js` に UI を実装し、
   `window.HimejiAssistant.registerPanel({ name, title, order, render })` で登録。
   PHP側 `editor_script()` でこのファイルを宣言する(`data` でJSへ設定値を渡せる)
4. **利用記録を入れる** — 挿入などの主要アクションで
   `HimejiAssistant.trackUsage('<id>')` を呼ぶ
   (`ui.ArticleList` を使う場合は `panel` プロパティ指定で自動)
5. **登録する** — `himeji-assistant.php` の require と
   `himeji_assistant_register_panels` アクションに1行ずつ追加
   (別プラグインとして作る場合は、そのプラグインから同じアクションを使う)
6. **AIを使う場合** — 直接APIを叩かず、必ず `HimejiAssistant.ai.complete()`
   (JS)または `Himeji_Assistant_AI::active_provider()`(PHP)経由にする。
   `ai.available` が false でも壊れないフォールバックを必ず用意する
7. **ドキュメント** — README の搭載パネル表・REST表・フック表と
   CHANGELOG.md を更新し、マイナーバージョンを上げる

## バージョンアップ時の注意

### バージョン番号

セマンティック バージョニングに従う(詳細は CHANGELOG.md 冒頭)。
リリース時は次の2箇所を必ず同時に更新する:

- `himeji-assistant.php` ヘッダーの `Version:`
- 定数 `HIMEJI_ASSISTANT_VERSION`

`HIMEJI_ASSISTANT_VERSION` はJS/CSSのキャッシュバスターにも使われるため、
これを上げ忘れるとライターのブラウザに古いJSが残る。

### 保存データの形式を変えるとき

「保存データ一覧」にあるデータの形式・キー名を変える場合は、
**必ず `Himeji_Assistant_Upgrade::migrations()` にマイグレーションを追加**する:

```php
private static function migrations() {
    return array(
        '0.5.0' => array( __CLASS__, 'migrate_0_5_0' ),
    );
}

/** 例: 利用統計をユーザー別集計に拡張する場合の移行 */
public static function migrate_0_5_0() {
    // 旧形式を読み、新形式に変換して保存する。
    // 冪等に書くこと(2回実行されても壊れない)。
    // 旧データは可能な限り捨てずに変換する。
}
```

- マイグレーションは古い順に自動実行され、完了ごとに
  `himeji_assistant_db_version` が進む(途中失敗しても次回続きから)
- **冪等に書く**(多重実行ガードはあるが、それに頼らない)
- 新規インストールではマイグレーションは走らない。
  「新規インストール直後の形式」=「全マイグレーション適用後の形式」に
  なるようコード側の初期値も揃えること

### 後方互換性のルール

メジャーバージョンを上げない限り、以下は**壊さない**:

- **ショートコード**: `[himeji_card]` `[himeji_map]` の既存属性と出力の意味。
  属性の追加はOK、削除・意味変更はNG(過去記事の表示が壊れるため。
  これはメジャーアップでも原則やらない — 記事は資産)
- **REST API**: 既存エンドポイントのパス・既存パラメータ・レスポンスの既存フィールド。
  フィールド追加はOK。廃止するときは新エンドポイントを追加し、旧を1マイナー版
  以上残してから消す
- **パネルAPI**: `Himeji_Assistant_Panel` の既存メソッドのシグネチャ、
  `himeji_assistant_register_panels` / `himeji_assistant_ai_providers` の呼び出し規約、
  `window.HimejiAssistant.*` の公開関数
- **パネルID・保存データのキー名**(変更するならマイグレーション必須)

廃止予定のものは CHANGELOG に「非推奨」として1マイナー版以上前に予告する。

### リリース前チェックリスト

- [ ] `php -l` が全ファイル通る / `node --check` が全JS通る
- [ ] バージョン2箇所(ヘッダー・定数)を更新した
- [ ] データ形式を変えた場合、マイグレーションを追加した
- [ ] CHANGELOG.md に変更内容を書いた
- [ ] 検証環境で「旧バージョンからの上書き更新」を一度試した
      (新規インストールだけでなく、更新経路を必ず通す)
- [ ] ブロックエディタとクラシックエディタの両方で開いて動作確認した

## 運用ルール

### リリース手順

1. CHANGELOG.md を確定し、バージョンを上げてコミット
2. `himeji-assistant` フォルダをZIP化
3. 検証環境(または管理者の1サイト)で上書きアップデートして動作確認
4. 本番へ。プラグイン画面から「プラグインのアップロード → 置き換え」
   (WP 5.5以降は既存プラグインの上書きインストールが可能)
5. 更新後、設定 → 姫路の種アシスタント を開いてエラーが出ないこと・
   `himeji_assistant_db_version` が新版になっていることを確認

### 運用フェーズの方針(現在)

- **機能追加は凍結中**。変更はバグ修正(パッチ版)のみ
- 週1回程度、設定 → 姫路の種アシスタント の「パネル利用状況」を確認し、
  記録を貯める。次の開発フェーズの優先順位はこのデータで決める
- ライターからの要望は Issue やメモに貯めておき、その場では実装しない
- 使われていないパネルは、削除ではなくまず「既定で非表示」を検討する
  (削除はメジャーバージョンアップまで温存)

### データの扱い

- 利用統計はサイト全体の集計のみで、個人のライターを特定する記録はしない。
  この方針を変える場合はライター全員に事前に伝えること
- Google Maps APIキーはサーバー側でのみ使用され、ブラウザには渡らない。
  キーのローテーション時は設定画面で差し替えるだけでよい
- プラグインの「無効化」ではデータは消えない。「削除」で全データが消える
  (uninstall.php)。アンインストール前に利用統計が必要ならメモしておく
