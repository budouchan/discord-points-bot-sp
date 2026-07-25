<?php
/**
 * プラグイン削除時の後始末。
 *
 * 管理画面からプラグインを「削除」したときだけ実行される
 * (無効化では実行されず、データは保持される)。
 * このプラグインが作成したオプションとユーザーメタをすべて削除する。
 */

defined( 'WP_UNINSTALL_PLUGIN' ) || exit;

// オプション
$himeji_assistant_options = array(
	'himeji_assistant_db_version',
	'himeji_assistant_install_version',
	'himeji_assistant_upgrading',
	'himeji_assistant_usage',
	'himeji_assistant_gmaps_api_key',
	'himeji_assistant_ai_provider',
);
foreach ( $himeji_assistant_options as $himeji_assistant_option ) {
	delete_option( $himeji_assistant_option );
}

// 地図検索のキャッシュ(transient)
global $wpdb;
$wpdb->query(
	"DELETE FROM {$wpdb->options}
	 WHERE option_name LIKE '_transient_himeji_maps_%'
	    OR option_name LIKE '_transient_timeout_himeji_maps_%'"
);

// 全ユーザーのパネル設定
delete_metadata( 'user', 0, 'himeji_assistant_hidden_panels', '', true );
delete_metadata( 'user', 0, 'himeji_assistant_favorite_panels', '', true );
