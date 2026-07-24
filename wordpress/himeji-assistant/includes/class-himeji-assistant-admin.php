<?php
/**
 * 管理画面への組み込み。
 *
 * - ブロックエディタ(Gutenberg): 右サイドバー「姫路の種アシスタント」
 * - クラシックエディタ: サイドバーのメタボックス
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Assistant_Admin {

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

		wp_enqueue_script(
			'himeji-assistant-editor',
			HIMEJI_ASSISTANT_URL . 'assets/js/editor-sidebar.js',
			array( 'wp-plugins', 'wp-edit-post', 'wp-element', 'wp-components', 'wp-data', 'wp-blocks', 'wp-api-fetch' ),
			HIMEJI_ASSISTANT_VERSION,
			true
		);
		wp_enqueue_style(
			'himeji-assistant-admin',
			HIMEJI_ASSISTANT_URL . 'assets/css/admin.css',
			array(),
			HIMEJI_ASSISTANT_VERSION
		);
	}

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
