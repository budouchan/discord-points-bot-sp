<?php
/**
 * パネルの基底クラス。
 *
 * 1機能 = 1パネル。新機能はこのクラスを継承して
 * himeji_assistant_register_panels アクションで登録する。
 */

defined( 'ABSPATH' ) || exit;

abstract class Himeji_Assistant_Panel {

	/** パネルID(英数字とハイフン)。 */
	abstract public function id();

	/** サイドバーに表示するパネル名。 */
	abstract public function title();

	/** パネル設定UIに表示する説明文。 */
	public function description() {
		return '';
	}

	/** サイドバー内の表示順(小さいほど上)。 */
	public function order() {
		return 10;
	}

	/**
	 * フック登録(REST ルート・ショートコード・フロントアセットなど)。
	 * パネル登録時に1回呼ばれる。
	 */
	public function register() {}

	/**
	 * ブロックエディタで読み込むパネルUIのスクリプト。
	 *
	 * 'data' を指定すると wp_localize_script でJSへ渡される。
	 *
	 * @return array|null array(
	 *     'handle' => string,
	 *     'src'    => string,
	 *     'deps'   => string[],
	 *     'data'   => array( 'name' => string, 'value' => array ), // 省略可
	 * )
	 */
	public function editor_script() {
		return null;
	}
}
