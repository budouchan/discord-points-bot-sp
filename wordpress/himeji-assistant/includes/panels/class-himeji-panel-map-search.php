<?php
/**
 * パネル: Googleマップ検索。
 *
 * 店名・住所を入力 → 候補を表示 → ワンクリックで地図埋め込みを挿入。
 * 緯度経度も取得できる。
 *
 * - 候補検索: Google Places API (Text Search)。APIキーは
 *   設定 → 姫路の種アシスタント で設定(サーバー側で呼ぶのでキーは
 *   ブラウザに出ない)。結果は1時間キャッシュ。
 * - 埋め込み: [himeji_map] ショートコード。表示は Google Maps の
 *   キー不要 iframe (output=embed) を使うため、閲覧側にAPIキーは不要。
 * - APIキー未設定でも「検索語をそのまま地図にして挿入」は使える。
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Panel_Map_Search extends Himeji_Assistant_Panel {

	public function id() {
		return 'map-search';
	}

	public function title() {
		return 'Googleマップ検索';
	}

	public function description() {
		return '店名・住所から地図を検索して、埋め込みをワンクリックで挿入します。';
	}

	public function order() {
		return 20;
	}

	public function editor_script() {
		return array(
			'handle' => 'himeji-panel-map-search',
			'src'    => HIMEJI_ASSISTANT_URL . 'assets/js/panels/map-search.js',
			'deps'   => array(),
			'data'   => array(
				'name'  => 'HimejiMapSearchData',
				'value' => array(
					'configured' => '' !== Himeji_Assistant_Settings::gmaps_key(),
				),
			),
		);
	}

	public function register() {
		add_action( 'rest_api_init', array( $this, 'register_routes' ) );
		add_shortcode( 'himeji_map', array( $this, 'render_shortcode' ) );
	}

	// ---- REST ----------------------------------------------------------

	public function register_routes() {
		register_rest_route(
			Himeji_Assistant_REST::NAMESPACE,
			'/maps/search',
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => array( $this, 'search' ),
				'permission_callback' => array( 'Himeji_Assistant_REST', 'can_use' ),
				'args'                => array(
					'q' => array(
						'type'              => 'string',
						'required'          => true,
						'sanitize_callback' => 'sanitize_text_field',
					),
				),
			)
		);
	}

	public function search( WP_REST_Request $request ) {
		$key = Himeji_Assistant_Settings::gmaps_key();
		if ( '' === $key ) {
			return new WP_Error(
				'himeji_maps_unconfigured',
				'Google Maps APIキーが未設定です。設定 → 姫路の種アシスタント で設定してください。',
				array( 'status' => 501 )
			);
		}

		$q         = $request['q'];
		$cache_key = 'himeji_maps_' . md5( $q );
		$cached    = get_transient( $cache_key );
		if ( false !== $cached ) {
			return rest_ensure_response( $cached );
		}

		$response = wp_remote_get(
			add_query_arg(
				array(
					'query'    => rawurlencode( $q ),
					'language' => 'ja',
					'region'   => 'jp',
					'key'      => $key,
				),
				'https://maps.googleapis.com/maps/api/place/textsearch/json'
			),
			array( 'timeout' => 10 )
		);

		if ( is_wp_error( $response ) ) {
			return new WP_Error( 'himeji_maps_error', '地図検索に失敗しました。', array( 'status' => 502 ) );
		}

		$body = json_decode( wp_remote_retrieve_body( $response ), true );
		if ( ! is_array( $body ) || empty( $body['results'] ) ) {
			$status = isset( $body['status'] ) ? $body['status'] : 'UNKNOWN';
			if ( 'ZERO_RESULTS' === $status ) {
				set_transient( $cache_key, array(), HOUR_IN_SECONDS );
				return rest_ensure_response( array() );
			}
			return new WP_Error(
				'himeji_maps_error',
				'地図検索に失敗しました(' . $status . ')。APIキーの設定を確認してください。',
				array( 'status' => 502 )
			);
		}

		$items = array();
		foreach ( array_slice( $body['results'], 0, 8 ) as $place ) {
			if ( empty( $place['geometry']['location'] ) ) {
				continue;
			}
			$items[] = array(
				'name'    => isset( $place['name'] ) ? $place['name'] : '',
				'address' => isset( $place['formatted_address'] ) ? $place['formatted_address'] : '',
				'lat'     => (float) $place['geometry']['location']['lat'],
				'lng'     => (float) $place['geometry']['location']['lng'],
			);
		}

		set_transient( $cache_key, $items, HOUR_IN_SECONDS );
		return rest_ensure_response( $items );
	}

	// ---- ショートコード -------------------------------------------------

	/**
	 * [himeji_map q="餃子のかっちゃん 姫路駅前店" lat="34.82" lng="134.69" zoom="16" height="360"]
	 *
	 * lat/lng があれば座標ベース、無ければ q の検索結果を埋め込む。
	 * data-* 属性に緯度経度・名称を残すので、将来の公開前チェック
	 * (地図・住所の有無チェック)からも機械的に読める。
	 */
	public function render_shortcode( $atts ) {
		$atts = shortcode_atts(
			array(
				'q'      => '',
				'lat'    => '',
				'lng'    => '',
				'zoom'   => 16,
				'height' => 360,
			),
			$atts,
			'himeji_map'
		);

		$q = trim( (string) $atts['q'] );
		if ( '' === $q && ( '' === $atts['lat'] || '' === $atts['lng'] ) ) {
			return '';
		}

		$center = ( '' !== $atts['lat'] && '' !== $atts['lng'] )
			? $atts['lat'] . ',' . $atts['lng']
			: '';

		// 検索語があればマーカー名付きで、無ければ座標で埋め込む。
		$embed_q = $q ? $q : $center;
		$src     = 'https://maps.google.com/maps?q=' . rawurlencode( $embed_q )
			. ( $center ? '&ll=' . rawurlencode( $center ) : '' )
			. '&z=' . (int) $atts['zoom'] . '&hl=ja&output=embed';

		return sprintf(
			'<div class="himeji-map" data-name="%s" data-lat="%s" data-lng="%s">' .
			'<iframe src="%s" width="100%%" height="%d" style="border:0;" loading="lazy" ' .
			'referrerpolicy="no-referrer-when-downgrade" allowfullscreen title="%s"></iframe></div>',
			esc_attr( $q ),
			esc_attr( $atts['lat'] ),
			esc_attr( $atts['lng'] ),
			esc_url( $src ),
			(int) $atts['height'],
			esc_attr( $q ? $q . 'の地図' : '地図' )
		);
	}
}
