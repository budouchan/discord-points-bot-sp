<?php
/**
 * 記事検索用の軽量 REST エンドポイント。
 *
 * GET /wp-json/himeji-assistant/v1/search?q=キーワード
 * → [ { id, title, url, date, thumbnail }, ... ]
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Assistant_REST {

	const NAMESPACE = 'himeji-assistant/v1';

	public static function init() {
		add_action( 'rest_api_init', array( __CLASS__, 'register_routes' ) );
	}

	public static function register_routes() {
		register_rest_route(
			self::NAMESPACE,
			'/search',
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => array( __CLASS__, 'search' ),
				'permission_callback' => array( __CLASS__, 'can_use' ),
				'args'                => array(
					'q'        => array(
						'type'              => 'string',
						'required'          => true,
						'sanitize_callback' => 'sanitize_text_field',
					),
					'per_page' => array(
						'type'    => 'integer',
						'default' => 10,
						'minimum' => 1,
						'maximum' => 20,
					),
				),
			)
		);
	}

	public static function can_use() {
		return current_user_can( 'edit_posts' );
	}

	public static function search( WP_REST_Request $request ) {
		$post_types = apply_filters( 'himeji_assistant_search_post_types', array( 'post', 'page' ) );

		$query = new WP_Query(
			array(
				's'                      => $request['q'],
				'post_type'              => $post_types,
				'post_status'            => 'publish',
				'posts_per_page'         => (int) $request['per_page'],
				'orderby'                => 'relevance',
				'no_found_rows'          => true,
				'update_post_term_cache' => false,
				'ignore_sticky_posts'    => true,
			)
		);

		$items = array();
		foreach ( $query->posts as $post ) {
			$items[] = array(
				'id'        => $post->ID,
				'title'     => html_entity_decode( get_the_title( $post ), ENT_QUOTES, 'UTF-8' ),
				'url'       => get_permalink( $post ),
				'date'      => get_the_date( 'Y-m-d', $post ),
				'thumbnail' => get_the_post_thumbnail_url( $post, 'thumbnail' ) ?: '',
			);
		}

		return rest_ensure_response( $items );
	}
}
