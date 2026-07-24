<?php
/**
 * Plugin Name: 姫路の種アシスタント
 * Description: 投稿編集画面に「姫路の種 編集OS」サイドバーを追加します。機能はパネルとして自由に追加・非表示にでき、AIプロバイダー(ChatGPT/Claude/Geminiなど)も差し替え可能な構造です。第1号パネルはリンクカード検索。
 * Version: 0.2.0
 * Author: 姫路の種
 * License: GPL-2.0-or-later
 * Text Domain: himeji-assistant
 */

defined( 'ABSPATH' ) || exit;

define( 'HIMEJI_ASSISTANT_VERSION', '0.2.0' );
define( 'HIMEJI_ASSISTANT_DIR', plugin_dir_path( __FILE__ ) );
define( 'HIMEJI_ASSISTANT_URL', plugin_dir_url( __FILE__ ) );

// コア(編集OS基盤)
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-core.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-panel.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-rest.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-ai.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-admin.php';

// 内蔵パネル
require_once HIMEJI_ASSISTANT_DIR . 'includes/panels/class-himeji-panel-link-card-search.php';

Himeji_Assistant_Core::init();
Himeji_Assistant_REST::init();
Himeji_Assistant_AI::init();
Himeji_Assistant_Admin::init();

// 内蔵パネルの登録。外部プラグインも同じアクションでパネルを追加できる。
add_action(
	'himeji_assistant_register_panels',
	function ( Himeji_Assistant_Core $core ) {
		$core->register_panel( new Himeji_Panel_Link_Card_Search() );
	}
);
