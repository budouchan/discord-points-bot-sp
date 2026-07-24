<?php
/**
 * Plugin Name: 姫路の種アシスタント
 * Description: 投稿編集画面に「姫路の種」編集支援パネルを追加します。第1弾はリンクカード検索。ライターがHTMLを書かずに関連記事カードを挿入できます。
 * Version: 0.1.0
 * Author: 姫路の種
 * License: GPL-2.0-or-later
 * Text Domain: himeji-assistant
 */

defined( 'ABSPATH' ) || exit;

define( 'HIMEJI_ASSISTANT_VERSION', '0.1.0' );
define( 'HIMEJI_ASSISTANT_DIR', plugin_dir_path( __FILE__ ) );
define( 'HIMEJI_ASSISTANT_URL', plugin_dir_url( __FILE__ ) );

require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-rest.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-shortcode.php';
require_once HIMEJI_ASSISTANT_DIR . 'includes/class-himeji-assistant-admin.php';

Himeji_Assistant_REST::init();
Himeji_Assistant_Shortcode::init();
Himeji_Assistant_Admin::init();
