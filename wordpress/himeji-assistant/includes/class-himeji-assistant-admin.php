<?php
/**
 * 管理画面への組み込み。
 *
 * - ブロックエディタ(Gutenberg): 右サイドバー「姫路の種アシスタント」。
 *   コアJS(サイドバーの器 + パネル設定)を読み込んだあと、
 *   各パネルの editor_script() を依存付きで読み込む。
 * - クラシックエディタ: サイドバーのメタボックス(現状はリンクカード検索のみ)。
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Assistant_Admin {

	const CORE_HANDLE = 'himeji-assistant-core';

	public static function init() {
		add_action( 'enqueue_block_editor_assets', array( __CLASS__, 'enqueue_block_editor' ) );
		add_action( 'add_meta_boxes', array( __CLASS__, 'add_classic_meta_box' ) );
		add_action( 'admin_enqueue_scripts', array( __CLASS__, 'enqueue_classic' ) );
	}

	/** アシスタントを表示する投稿タイプ。 */
	public static function post_types() {
		return apply_filters( 'himeji_assistant_post_types', array( 'post', 'page' ) );
	}

	public static function enqueue_block_editor() {
		$screen = function_exists( 'get_current_screen' ) ? get_current_screen() : null;
		if ( $screen && ! in_array( $screen->post_type, self::post_types(), true ) ) {
			return;
		}

		$core = Himeji_Assistant_Core::instance();

		wp_enqueue_script(
			self::CORE_HANDLE,
			HIMEJI_ASSISTANT_URL . 'assets/js/assistant-core.js',
			array( 'wp-plugins', 'wp-edit-post', 'wp-element', 'wp-components', 'wp-data', 'wp-api-fetch' ),
			HIMEJI_ASSISTANT_VERSION,
			true
		);

		wp_localize_script(
			self::CORE_HANDLE,
			'HimejiAssistantData',
			array(
				'panels'       => $core->panels_meta(),
				'hiddenPanels' => Himeji_Assistant_REST::hidden_panels(),
				'aiAvailable'  => Himeji_Assistant_AI::is_available(),
			)
		);

		// 各パネルのUIスクリプト。コアの後に読み込む。
		foreach ( $core->panels() as $panel ) {
			$script = $panel->editor_script();
			if ( ! $script || empty( $script['handle'] ) || empty( $script['src'] ) ) {
				continue;
			}
			$deps   = isset( $script['deps'] ) ? (array) $script['deps'] : array();
			$deps[] = self::CORE_HANDLE;
			wp_enqueue_script( $script['handle'], $script['src'], $deps, HIMEJI_ASSISTANT_VERSION, true );
		}

		wp_enqueue_style(
			'himeji-assistant-admin',
			HIMEJI_ASSISTANT_URL . 'assets/css/admin.css',
			array(),
			HIMEJI_ASSISTANT_VERSION
		);
	}

	// ---- クラシックエディタ ---------------------------------------------

	public static function add_classic_meta_box() {
		add_meta_box(
			'himeji-assistant',
			'姫路の種アシスタント',
			array( __CLASS__, 'render_classic_meta_box' ),
			self::post_types(),
			'side',
			'high',
			// ブロックエディタでは JS サイドバー側を使うのでメタボックスは出さない。
			array( '__back_compat_meta_box' => true )
		);
	}

	public static function render_classic_meta_box() {
		?>
		<div id="himeji-assistant-classic">
			<p class="himeji-assistant__heading">リンクカード検索</p>
			<p class="himeji-assistant__help">キーワードで過去記事を検索して、カーソル位置にリンクカードを挿入できます。</p>
			<input type="search" id="himeji-assistant-q" class="widefat"
				placeholder="記事のキーワード…" autocomplete="off" />
			<div id="himeji-assistant-results" class="himeji-assistant__results" aria-live="polite"></div>
		</div>
		<?php
	}

	public static function enqueue_classic( $hook ) {
		if ( 'post.php' !== $hook && 'post-new.php' !== $hook ) {
			return;
		}
		$screen = get_current_screen();
		if ( ! $screen || $screen->is_block_editor() ) {
			return; // ブロックエディタは enqueue_block_editor_assets 側で対応。
		}
		if ( ! in_array( $screen->post_type, self::post_types(), true ) ) {
			return;
		}

		wp_enqueue_script(
			'himeji-assistant-classic',
			HIMEJI_ASSISTANT_URL . 'assets/js/classic-metabox.js',
			array(),
			HIMEJI_ASSISTANT_VERSION,
			true
		);
		wp_localize_script(
			'himeji-assistant-classic',
			'HimejiAssistantConfig',
			array(
				'restUrl' => esc_url_raw( rest_url( Himeji_Assistant_REST::NAMESPACE . '/search' ) ),
				'nonce'   => wp_create_nonce( 'wp_rest' ),
			)
		);
		wp_enqueue_style(
			'himeji-assistant-admin',
			HIMEJI_ASSISTANT_URL . 'assets/css/admin.css',
			array(),
			HIMEJI_ASSISTANT_VERSION
		);
	}
}
