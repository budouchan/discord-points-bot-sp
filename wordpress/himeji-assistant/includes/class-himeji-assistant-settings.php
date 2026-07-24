<?php
/**
 * 設定画面(設定 → 姫路の種アシスタント)。
 *
 * - Google Maps APIキー(地図検索パネルの候補検索に使用)
 * - AIプロバイダーの選択
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Assistant_Settings {

	const OPTION_GMAPS_KEY   = 'himeji_assistant_gmaps_api_key';
	const OPTION_AI_PROVIDER = 'himeji_assistant_ai_provider';

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'add_page' ) );
		add_action( 'admin_init', array( __CLASS__, 'register_settings' ) );
	}

	public static function gmaps_key() {
		return trim( (string) get_option( self::OPTION_GMAPS_KEY, '' ) );
	}

	public static function add_page() {
		add_options_page(
			'姫路の種アシスタント',
			'姫路の種アシスタント',
			'manage_options',
			'himeji-assistant',
			array( __CLASS__, 'render_page' )
		);
	}

	public static function register_settings() {
		register_setting(
			'himeji_assistant',
			self::OPTION_GMAPS_KEY,
			array( 'sanitize_callback' => 'sanitize_text_field' )
		);
		register_setting(
			'himeji_assistant',
			self::OPTION_AI_PROVIDER,
			array( 'sanitize_callback' => 'sanitize_key' )
		);
	}

	public static function render_page() {
		$providers = Himeji_Assistant_AI::providers();
		$current   = get_option( self::OPTION_AI_PROVIDER, '' );
		?>
		<div class="wrap">
			<h1>姫路の種アシスタント</h1>
			<form method="post" action="options.php">
				<?php settings_fields( 'himeji_assistant' ); ?>
				<table class="form-table" role="presentation">
					<tr>
						<th scope="row">
							<label for="himeji-gmaps-key">Google Maps APIキー</label>
						</th>
						<td>
							<input type="text" id="himeji-gmaps-key" class="regular-text code"
								name="<?php echo esc_attr( self::OPTION_GMAPS_KEY ); ?>"
								value="<?php echo esc_attr( self::gmaps_key() ); ?>"
								autocomplete="off" />
							<p class="description">
								「Googleマップ検索」パネルの候補検索(店名・住所 → 緯度経度)に使います。
								Google Cloud で <strong>Places API</strong> を有効にしたキーを入力してください。
								未設定でも、検索語をそのまま地図として挿入する機能は使えます。
							</p>
						</td>
					</tr>
					<tr>
						<th scope="row">
							<label for="himeji-ai-provider">AIプロバイダー</label>
						</th>
						<td>
							<select id="himeji-ai-provider" name="<?php echo esc_attr( self::OPTION_AI_PROVIDER ); ?>">
								<option value="">自動(設定済みの最初のプロバイダー)</option>
								<?php foreach ( $providers as $provider ) : ?>
									<option value="<?php echo esc_attr( $provider->id() ); ?>" <?php selected( $current, $provider->id() ); ?>>
										<?php echo esc_html( $provider->label() ); ?>
										<?php echo $provider->is_configured() ? '' : '(未設定)'; ?>
									</option>
								<?php endforeach; ?>
							</select>
							<p class="description">
								<?php if ( empty( $providers ) ) : ?>
									登録済みのAIプロバイダーはまだありません。
									プロバイダーは <code>himeji_assistant_ai_providers</code> フィルターで追加できます(README参照)。
									AIが無くても各パネルは通常どおり動作します。
								<?php else : ?>
									AI関連記事推薦などのAI機能で使うプロバイダーを選択します。
								<?php endif; ?>
							</p>
						</td>
					</tr>
				</table>
				<?php submit_button(); ?>
			</form>
		</div>
		<?php
	}
}
