<?php
/**
 * AIサービス層。
 *
 * パネル本体とAIを疎結合にするための独立レイヤー。
 * ChatGPT / Claude / Gemini などは「プロバイダー」として追加する:
 *
 *   class My_Claude_Provider implements Himeji_Assistant_AI_Provider { ... }
 *
 *   add_filter( 'himeji_assistant_ai_providers', function ( $providers ) {
 *       $provider = new My_Claude_Provider();
 *       $providers[ $provider->id() ] = $provider;
 *       return $providers;
 *   } );
 *
 * 使うプロバイダーはオプション himeji_assistant_ai_provider
 * (または himeji_assistant_ai_active_provider フィルター)で選択。
 * パネル側は POST /himeji-assistant/v1/ai/complete を叩くだけで、
 * どのAIが背後にいるかを知る必要がない。
 */

defined( 'ABSPATH' ) || exit;

interface Himeji_Assistant_AI_Provider {

	/** プロバイダーID(例: 'claude', 'openai', 'gemini')。 */
	public function id();

	/** 表示名(例: 'Claude (Anthropic)')。 */
	public function label();

	/** APIキー設定済みなど、利用可能な状態か。 */
	public function is_configured();

	/**
	 * プロンプトを実行して結果テキストを返す。
	 *
	 * @param string $prompt プロンプト本文。
	 * @param array  $args   付加情報。'task'(例: 'category-suggest')や
	 *                       'post_id' などパネル側の文脈が入る。
	 * @return string|WP_Error
	 */
	public function complete( $prompt, array $args = array() );
}

final class Himeji_Assistant_AI {

	public static function init() {
		add_action( 'rest_api_init', array( __CLASS__, 'register_routes' ) );
	}

	/** @return Himeji_Assistant_AI_Provider[] id => プロバイダー */
	public static function providers() {
		$providers = apply_filters( 'himeji_assistant_ai_providers', array() );
		return is_array( $providers ) ? $providers : array();
	}

	/** @return Himeji_Assistant_AI_Provider|null */
	public static function active_provider() {
		$providers = self::providers();
		$id        = apply_filters(
			'himeji_assistant_ai_active_provider',
			get_option( 'himeji_assistant_ai_provider', '' )
		);

		if ( $id && isset( $providers[ $id ] ) && $providers[ $id ]->is_configured() ) {
			return $providers[ $id ];
		}

		// 明示指定がなければ、設定済みの最初のプロバイダーを使う。
		foreach ( $providers as $provider ) {
			if ( $provider->is_configured() ) {
				return $provider;
			}
		}
		return null;
	}

	public static function is_available() {
		return null !== self::active_provider();
	}

	public static function register_routes() {
		register_rest_route(
			Himeji_Assistant_REST::NAMESPACE,
			'/ai/complete',
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => array( __CLASS__, 'complete' ),
				'permission_callback' => array( 'Himeji_Assistant_REST', 'can_use' ),
				'args'                => array(
					'prompt'  => array(
						'type'     => 'string',
						'required' => true,
					),
					'task'    => array(
						'type'              => 'string',
						'default'           => '',
						'sanitize_callback' => 'sanitize_key',
					),
					'post_id' => array(
						'type'    => 'integer',
						'default' => 0,
					),
				),
			)
		);
	}

	public static function complete( WP_REST_Request $request ) {
		$provider = self::active_provider();
		if ( ! $provider ) {
			return new WP_Error(
				'himeji_ai_unconfigured',
				'AIプロバイダーが設定されていません。管理者に連絡してください。',
				array( 'status' => 501 )
			);
		}

		$result = $provider->complete(
			$request['prompt'],
			array(
				'task'    => $request['task'],
				'post_id' => (int) $request['post_id'],
			)
		);

		if ( is_wp_error( $result ) ) {
			return $result;
		}

		return rest_ensure_response(
			array(
				'provider' => $provider->id(),
				'result'   => $result,
			)
		);
	}
}
