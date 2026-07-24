<?php
/**
 * リンクカードのショートコード。
 *
 * 使い方: [himeji_card id="123"]
 * ID で参照するので、参照先のタイトル・アイキャッチ・URL が
 * 変わっても常に最新の状態で表示される。
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Assistant_Shortcode {

	public static function init() {
		add_shortcode( 'himeji_card', array( __CLASS__, 'render' ) );
		add_action( 'wp_enqueue_scripts', array( __CLASS__, 'register_style' ) );
	}

	public static function register_style() {
		wp_register_style(
			'himeji-assistant-card',
			HIMEJI_ASSISTANT_URL . 'assets/css/card.css',
			array(),
			HIMEJI_ASSISTANT_VERSION
		);
	}

	public static function render( $atts ) {
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
