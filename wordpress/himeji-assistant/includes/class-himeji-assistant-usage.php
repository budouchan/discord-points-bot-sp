<?php
/**
 * パネル利用回数の記録。
 *
 * 「どのパネルが実際に使われているか」を計測し、
 * 常時表示する価値のあるパネル・削るべきパネルの判断材料にする。
 *
 * - カウント対象は「挿入」などの実アクション(パネルを開いただけでは数えない)
 * - 日別×パネル別のサイト全体の集計。個人を特定する記録はしない
 * - 保持は直近90日。古い日付は記録時に自動削除
 * - 集計は 設定 → 姫路の種アシスタント で確認できる
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Assistant_Usage {

	const OPTION         = 'himeji_assistant_usage';
	const RETENTION_DAYS = 90;

	public static function init() {
		add_action( 'rest_api_init', array( __CLASS__, 'register_routes' ) );
	}

	public static function register_routes() {
		register_rest_route(
			Himeji_Assistant_REST::NAMESPACE,
			'/usage',
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => array( __CLASS__, 'track' ),
				'permission_callback' => array( 'Himeji_Assistant_REST', 'can_use' ),
				'args'                => array(
					'panel' => array(
						'type'              => 'string',
						'required'          => true,
						'sanitize_callback' => 'sanitize_key',
					),
				),
			)
		);
	}

	public static function track( WP_REST_Request $request ) {
		$panel = $request['panel'];
		if ( ! isset( Himeji_Assistant_Core::instance()->panels()[ $panel ] ) ) {
			return new WP_Error( 'himeji_usage_unknown_panel', '不明なパネルです。', array( 'status' => 400 ) );
		}
		self::record( $panel );
		return rest_ensure_response( array( 'ok' => true ) );
	}

	public static function record( $panel ) {
		$data = get_option( self::OPTION, array() );
		if ( ! is_array( $data ) ) {
			$data = array();
		}

		$today = current_time( 'Y-m-d' );
		if ( ! isset( $data[ $today ][ $panel ] ) ) {
			$data[ $today ][ $panel ] = 0;
		}
		$data[ $today ][ $panel ]++;

		// 保持期間より古い日付を削除。
		$cutoff = gmdate( 'Y-m-d', current_time( 'timestamp' ) - self::RETENTION_DAYS * DAY_IN_SECONDS );
		foreach ( array_keys( $data ) as $day ) {
			if ( $day < $cutoff ) {
				unset( $data[ $day ] );
			}
		}

		update_option( self::OPTION, $data, false );
	}

	/**
	 * 直近N日のパネル別合計。
	 *
	 * @return array panel_id => count(多い順)
	 */
	public static function totals( $days ) {
		$data = get_option( self::OPTION, array() );
		if ( ! is_array( $data ) ) {
			return array();
		}

		$cutoff = gmdate( 'Y-m-d', current_time( 'timestamp' ) - ( $days - 1 ) * DAY_IN_SECONDS );
		$totals = array();
		foreach ( $data as $day => $counts ) {
			if ( $day < $cutoff || ! is_array( $counts ) ) {
				continue;
			}
			foreach ( $counts as $panel => $count ) {
				$totals[ $panel ] = ( isset( $totals[ $panel ] ) ? $totals[ $panel ] : 0 ) + (int) $count;
			}
		}
		arsort( $totals );
		return $totals;
	}
}
