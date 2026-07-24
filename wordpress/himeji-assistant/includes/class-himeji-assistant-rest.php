<?php
/**
 * 編集OSコアの REST エンドポイント。
 *
 * - GET  /himeji-assistant/v1/prefs  … パネル表示設定の取得
 * - POST /himeji-assistant/v1/prefs  … パネル表示設定の保存(ユーザーごと)
 *
 * 各パネル固有のエンドポイント(検索など)は各パネルクラスが
 * 同じ名前空間に register する。
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Assistant_REST {

	const NAMESPACE = 'himeji-assistant/v1';

	const META_HIDDEN_PANELS = 'himeji_assistant_hidden_panels';

	public static function init() {
		add_action( 'rest_api_init', array( __CLASS__, 'register_routes' ) );
	}

	public static function can_use() {
		return current_user_can( 'edit_posts' );
	}

	public static function register_routes() {
		register_rest_route(
			self::NAMESPACE,
			'/prefs',
			array(
				array(
					'methods'             => WP_REST_Server::READABLE,
					'callback'            => array( __CLASS__, 'get_prefs' ),
					'permission_callback' => array( __CLASS__, 'can_use' ),
				),
				array(
					'methods'             => WP_REST_Server::CREATABLE,
					'callback'            => array( __CLASS__, 'save_prefs' ),
					'permission_callback' => array( __CLASS__, 'can_use' ),
					'args'                => array(
						'hidden' => array(
							'type'     => 'array',
							'required' => true,
							'items'    => array( 'type' => 'string' ),
						),
					),
				),
			)
		);
	}

	/** 現在のユーザーが非表示にしているパネルIDの配列。 */
	public static function hidden_panels( $user_id = 0 ) {
		$user_id = $user_id ?: get_current_user_id();
		$hidden  = get_user_meta( $user_id, self::META_HIDDEN_PANELS, true );
		return is_array( $hidden ) ? array_values( array_map( 'sanitize_key', $hidden ) ) : array();
	}

	public static function get_prefs() {
		return rest_ensure_response( array( 'hidden' => self::hidden_panels() ) );
	}

	public static function save_prefs( WP_REST_Request $request ) {
		$known  = array_keys( Himeji_Assistant_Core::instance()->panels() );
		$hidden = array_values( array_intersect( array_map( 'sanitize_key', (array) $request['hidden'] ), $known ) );
		update_user_meta( get_current_user_id(), self::META_HIDDEN_PANELS, $hidden );
		return rest_ensure_response( array( 'hidden' => $hidden ) );
	}
}
