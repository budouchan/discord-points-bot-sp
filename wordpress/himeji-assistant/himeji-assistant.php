<?php
/**
 * Plugin Name: 姫路の種アシスタント
 * Description: 投稿編集画面に「姫路の種 編集OS」サイドバーを追加します。リンクカード検索・Googleマップ検索・よく使うショートコード・AI関連記事推薦を搭載。機能はパネルとして自由に追加・非表示にでき、AIプロバイダーも差し替え可能な構造です。
 * Version: 0.4.0
 * Author: 姫路の種
 * License: GPL-2.0-or-later
 * Text Domain: himeji-assistant
 */

defined( 'ABSPATH' ) || exit;

define( 'HIMEJI_ASSISTANT_VERSION', '0.4.0' );
define( 'HIMEJI_ASSISTANT_DIR', plugin_dir_path( __FILE__ ) );
define( 'HIMEJI_ASSISTANT_URL', plugin_dir_url( __FILE__ ) );

// コア(編集OS基盤)
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-core.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-panel.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-rest.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-ai.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-usage.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-settings.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-admin.php';

// 内蔵パネル
require_once HIMEJI_ASSISTANT_DIR . 'includes/panels/class-himeji-panel-link-card-search.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/panels/class-himeji-panel-map-search.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/panels/class-himeji-panel-snippets.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/panels/class-himeji-panel-related-suggest.php';

Himeji_Assistant_Core::init();
Himeji_Assistant_REST::init();
Himeji_Assistant_AI::init();
Himeji_Assistant_Usage::init();
Himeji_Assistant_Settings::init();
Himeji_Assistant_Admin::init();

// 内蔵パネルの登録。外部プラグインも同じアクションでパネルを追加できる。
add_action(
	'himeji_assistant_register_panels',
	function ( Himeji_Assistant_Core $core ) {
		$core->register_panel( new Himeji_Panel_Link_Card_Search() );
		$core->register_panel( new Himeji_Panel_Map_Search() );
		$core->register_panel( new Himeji_Panel_Snippets() );
		$core->register_panel( new Himeji_Panel_Related_Suggest() );
	}
);
