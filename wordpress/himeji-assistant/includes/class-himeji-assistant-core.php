<?php
/**
 * 編集OSのコア: パネルレジストリ。
 *
 * すべての機能(関連記事検索・カテゴリ提案・公開前チェック…)は
 * Himeji_Assistant_Panel を継承した「パネル」として登録する。
 * このプラグイン内蔵のパネルも、外部プラグインが追加するパネルも
 * 同じ仕組みに乗る:
 *
 *   add_action( 'himeji_assistant_register_panels', function ( $core ) {
 *       $core->register_panel( new My_Panel() );
 *   } );
 */

defined( 'ABSPATH' ) || exit;

final class Himeji_Assistant_Core {

	/** @var Himeji_Assistant_Core|null */
	private static $instance = null;

	/** @var Himeji_Assistant_Panel[] id => パネル */
	private $panels = array();

	public static function instance() {
		if ( null === self::$instance ) {
			self::$instance = new self();
		}
		return self::$instance;
	}

	public static function init() {
		// rest_api_init より前にパネルを確定させる。
		add_action( 'init', array( self::instance(), 'collect_panels' ), 5 );
	}

	public function collect_panels() {
		do_action( 'himeji_assistant_register_panels', $this );
	}

	public function register_panel( Himeji_Assistant_Panel $panel ) {
		if ( isset( $this->panels[ $panel->id() ] ) ) {
			return;
		}
		$this->panels[ $panel->id() ] = $panel;
		$panel->register();
	}

	/** @return Himeji_Assistant_Panel[] */
	public function panels() {
		return $this->panels;
	}

	/** サイドバーJS・パネル設定UIに渡すメタ情報。 */
	public function panels_meta() {
		$meta = array();
		foreach ( $this->panels as $panel ) {
			$meta[] = array(
				'id'          => $panel->id(),
				'title'       => $panel->title(),
				'description' => $panel->description(),
				'order'       => $panel->order(),
			);
		}
		usort(
			$meta,
			function ( $a, $b ) {
				return $a['order'] - $b['order'];
			}
		);
		return $meta;
	}
}
