/**
 * パネル: よく使うショートコード。
 *
 * HimejiSnippetsData.items(PHP側 himeji_assistant_snippets フィルター)を
 * ボタンとして並べ、ワンクリックでカーソル位置に挿入する。
 */
( function ( wp ) {
	'use strict';

	var el = wp.element.createElement;
	var Button = wp.components.Button;
	var assistant = window.HimejiAssistant;
	var data = window.HimejiSnippetsData || { items: [] };

	function insertSnippet( item ) {
		if ( 'embed' === item.type ) {
			assistant.insertBlockAtCursor( wp.blocks.createBlock( 'core/embed' ) );
		} else {
			assistant.insertShortcode( item.template || '' );
		}
		assistant.trackUsage( 'snippets' );
	}

	function SnippetsPanel() {
		if ( ! data.items.length ) {
			return el( 'p', { className: 'himeji-assistant__help' }, 'スニペットが登録されていません。' );
		}

		return el(
			'div',
			{ className: 'himeji-assistant__panel' },
			data.items.map( function ( item ) {
				return el(
					'div',
					{ key: item.id, className: 'himeji-assistant__snippet' },
					el( Button, {
						variant: 'secondary',
						isSmall: true,
						onClick: function () {
							insertSnippet( item );
						},
					}, item.label ),
					item.description
						? el( 'span', { className: 'himeji-assistant__snippet-desc' }, item.description )
						: null
				);
			} )
		);
	}

	assistant.registerPanel( {
		name: 'snippets',
		title: 'よく使うショートコード',
		order: 30,
		render: SnippetsPanel,
	} );
} )( window.wp );
