<?php
/**
 * パネル: リンクカード検索(編集OSの第1号パネル)。
 *
 * - REST: GET /himeji-assistant/v1/search?q=…
 * - ショートコード: [himeji_card id="123"]
 * - エディタUI: assets/js/panels/link-card-search.js
 *
 * AI関連記事推薦を追加するときは、このレスポンス形式
 * ( id, title, url, date, thumbnail )に合わせた推薦エンドポイントを
 * 作れば、結果リストUIと「カードを挿入」ボタンをそのまま流用できる。
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Panel_Link_Card_Search extends Himeji_Assistant_Panel {

	public function id() {
		return 'link-card-search';
	}

	public function title() {
		return 'リンクカード検索';
	}

	public function description() {
		return 'キーワードで過去記事を検索し、カーソル位置にリンクカードを挿入します。';
	}

	public function order() {
		return 10;
	}

	public function editor_script() {
		return array(
			'handle' => 'himeji-panel-link-card-search',
			'src'    => HIMEJI_ASSISTANT_URL . 'assets/js/panels/link-card-search.js',
			'deps'   => array( 'wp-blocks', 'wp-data' ),
		);
	}

	public function register() {
		add_action( 'rest_api_init', array( $this, 'register_routes' ) );
		add_shortcode( 'himeji_card', array( $this, 'render_shortcode' ) );
		add_action( 'wp_enqueue_scripts', array( $this, 'register_front_style' ) );
	}

	// ---- REST ----------------------------------------------------------

	public function register_routes() {
		register_rest_route(
			Himeji_Assistant_REST::NAMESPACE,
			'/search',
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => array( $this, 'search' ),
				'permission_callback' => array( 'Himeji_Assistant_REST', 'can_use' ),
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
					'orderby'  => array(
						'type'    => 'string',
						'default' => 'relevance',
						'enum'    => array( 'relevance', 'date', 'popular' ),
					),
				),
			)
		);
	}

	public function search( WP_REST_Request $request ) {
		$post_types = apply_filters( 'himeji_assistant_search_post_types', array( 'post', 'page' ) );

		// 検索(s)はタイトル・本文・抜粋が対象。並び順は3種類:
		// relevance = 関連度順 / date = 新着順 / popular = 人気順
		$args = array(
			's'                      => $request['q'],
			'post_type'              => $post_types,
			'post_status'            => 'publish',
			'posts_per_page'         => (int) $request['per_page'],
			'orderby'                => 'relevance',
			'no_found_rows'          => true,
			'update_post_term_cache' => false,
			'ignore_sticky_posts'    => true,
		);

		if ( 'date' === $request['orderby'] ) {
			$args['orderby'] = 'date';
			$args['order']   = 'DESC';
		} elseif ( 'popular' === $request['orderby'] ) {
			// 閲覧数プラグイン(WP-PostViews等)を使っている場合は
			// そのメタキーをフィルターで指定すると閲覧数順になる。
			// 未指定時はコメント数順。
			$views_key = apply_filters( 'himeji_assistant_views_meta_key', '' );
			if ( $views_key ) {
				$args['meta_key'] = $views_key;
				$args['orderby']  = 'meta_value_num';
			} else {
				$args['orderby'] = 'comment_count';
			}
			$args['order'] = 'DESC';
		}

		$query = new WP_Query( $args );

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

	// ---- ショートコード -------------------------------------------------

	public function register_front_style() {
		wp_register_style(
			'himeji-assistant-card',
			HIMEJI_ASSISTANT_URL . 'assets/css/card.css',
			array(),
			HIMEJI_ASSISTANT_VERSION
		);
	}

	public function render_shortcode( $atts ) {
		$atts = shortcode_atts(
			array(
				'id'    => 0,
				'label' => apply_filters( 'himeji_assistant_card_label', 'あわせて読みたい' ),
			),
			$atts,
			'himeji_card'
		);

		$post = get_post( (int) $atts['id'] );
		if ( ! $post || 'publish' !== $post->post_status ) {
			return '';
		}

		wp_enqueue_style( 'himeji-assistant-card' );

		$url     = get_permalink( $post );
		$title   = get_the_title( $post );
		$excerpt = wp_html_excerpt( get_the_excerpt( $post ), 80, '…' );
		$thumb   = get_the_post_thumbnail( $post, 'medium', array( 'loading' => 'lazy' ) );

		ob_start();
		?>
		<a class="himeji-card" href="<?php echo esc_url( $url ); ?>">
			<?php if ( $thumb ) : ?>
				<span class="himeji-card__thumb"><?php echo $thumb; ?></span>
			<?php endif; ?>
			<span class="himeji-card__body">
				<span class="himeji-card__label"><?php echo esc_html( $atts['label'] ); ?></span>
				<span class="himeji-card__title"><?php echo esc_html( $title ); ?></span>
				<?php if ( $excerpt ) : ?>
					<span class="himeji-card__excerpt"><?php echo esc_html( $excerpt ); ?></span>
				<?php endif; ?>
			</span>
		</a>
		<?php
		return trim( ob_get_clean() );
	}
}
