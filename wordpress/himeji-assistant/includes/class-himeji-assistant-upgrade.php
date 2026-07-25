<?php
/**
 * バージョン管理とデータマイグレーション。
 *
 * プラグイン本体の更新(ファイル差し替え・自動アップデート)と、
 * 保存データ(オプション・ユーザーメタ)の形式変更を分離するための仕組み。
 *
 * 仕組み:
 * - オプション himeji_assistant_db_version に「データが今どのバージョンの
 *   形式か」を記録する(プラグインのファイルバージョンとは別物)
 * - 管理画面の読み込み時に比較し、古ければ migrations() に登録された
 *   マイグレーションを古い順に1つずつ実行する
 * - 各ステップ完了ごとに db_version を進めるので、途中で失敗しても
 *   次回そのステップからやり直せる(各マイグレーションは
 *   何度実行しても安全=冪等に書くこと)
 *
 * データ形式を変えるときの手順は README の
 * 「バージョンアップ時の注意」を参照。
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Assistant_Upgrade {

	const OPTION_DB_VERSION      = 'himeji_assistant_db_version';
	const OPTION_INSTALL_VERSION = 'himeji_assistant_install_version';

	public static function init() {
		// フロントの表示速度に影響させないため管理画面でのみ判定する。
		add_action( 'admin_init', array( __CLASS__, 'maybe_upgrade' ), 1 );
	}

	/**
	 * マイグレーション一覧: 'バージョン' => callable。
	 * 「このバージョンでデータ形式が変わった」ものだけを登録する。
	 * バージョン順(古い順)に並べておくこと。
	 *
	 * 例:
	 *   '0.5.0' => array( __CLASS__, 'migrate_0_5_0' ),
	 */
	private static function migrations() {
		return array();
	}

	public static function maybe_upgrade() {
		$db_version = get_option( self::OPTION_DB_VERSION );

		// 新規インストール(または v0.4.x 以前からの更新)。
		// マイグレーション未登録の現時点では、現行版を基準として記録するだけ。
		if ( false === $db_version ) {
			add_option( self::OPTION_DB_VERSION, HIMEJI_ASSISTANT_VERSION, '', false );
			add_option( self::OPTION_INSTALL_VERSION, HIMEJI_ASSISTANT_VERSION, '', false );
			return;
		}

		if ( version_compare( $db_version, HIMEJI_ASSISTANT_VERSION, '>=' ) ) {
			return;
		}

		// 多重実行ガード(同時アクセスで二重に走らないように)。
		if ( false === add_option( 'himeji_assistant_upgrading', time(), '', false ) ) {
			$started = (int) get_option( 'himeji_assistant_upgrading' );
			if ( $started > time() - 5 * MINUTE_IN_SECONDS ) {
				return; // 別プロセスが実行中
			}
		}

		foreach ( self::migrations() as $version => $callback ) {
			if ( version_compare( $db_version, $version, '<' )
				&& version_compare( $version, HIMEJI_ASSISTANT_VERSION, '<=' ) ) {
				call_user_func( $callback );
				update_option( self::OPTION_DB_VERSION, $version, false );
				$db_version = $version;
			}
		}

		update_option( self::OPTION_DB_VERSION, HIMEJI_ASSISTANT_VERSION, false );
		delete_option( 'himeji_assistant_upgrading' );
	}
}
