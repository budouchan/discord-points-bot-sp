<?php
/**
 * パネル: よく使うショートコード。
 *
 * 吹き出し・ボタン・関連記事カード・SNS埋め込みなどを
 * ワンクリックでカーソル位置に挿入する。
 *
 * 一覧は himeji_assistant_snippets フィルターで自由に追加・変更できるので、
 * テーマ独自のショートコードや定型文もここに並べられる。
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Panel_Snippets extends Himeji_Assistant_Panel {

	public function id() {
		return 'snippets';
	}

	public function title() {
		return 'よく使うショートコード';
	}

	public function description() {
		return '吹き出し・ボタン・SNS埋め込みなどをワンクリックで挿入します。';
	}

	public function order() {
		return 30;
	}

	/**
	 * スニペット定義。
	 *
	 * - type 'shortcode' (既定): template をショートコードブロックとして挿入
	 * - type 'embed': 空の埋め込みブロックを挿入(URLを貼るだけでSNS埋め込みになる)
	 *
	 * テーマのショートコード名に合わせて himeji_assistant_snippets で
	 * 上書きしてください。定型文(あいさつ文など)も template に
	 * 文字列を入れれば同じ仕組みで挿入できる。
	 */
	public function snippets() {
		$defaults = array(
			array(
				'id'          => 'speech-bubble-left',
				'label'       => '吹き出し(左)',
				'template'    => '[speech_bubble align="left" name="名前"]セリフをここに[/speech_bubble]',
				'description' => '左向きの吹き出し',
			),
			array(
				'id'          => 'speech-bubble-right',
				'label'       => '吹き出し(右)',
				'template'    => '[speech_bubble align="right" name="名前"]セリフをここに[/speech_bubble]',
				'description' => '右向きの吹き出し',
			),
			array(
				'id'          => 'himeji-card',
				'label'       => '関連記事カード',
				'template'    => '[himeji_card id=""]',
				'description' => 'IDは「リンクカード検索」パネルから挿入すると自動で入ります',
			),
			array(
				'id'          => 'button',
				'label'       => 'ボタン',
				'template'    => '[button url="https://" text="ボタンの文言"]',
				'description' => 'リンクボタン',
			),
			array(
				'id'          => 'sns-embed',
				'label'       => 'SNS埋め込み',
				'type'        => 'embed',
				'description' => '埋め込みブロックを挿入します。X/Instagram等の投稿URLを貼るだけでOK',
			),
		);
		return apply_filters( 'himeji_assistant_snippets', $defaults );
	}

	public function editor_script() {
		return array(
			'handle' => 'himeji-panel-snippets',
			'src'    => HIMEJI_ASSISTANT_URL . 'assets/js/panels/snippets.js',
			'deps'   => array(),
			'data'   => array(
				'name'  => 'HimejiSnippetsData',
				'value' => array( 'items' => $this->snippets() ),
			),
		);
	}
}
