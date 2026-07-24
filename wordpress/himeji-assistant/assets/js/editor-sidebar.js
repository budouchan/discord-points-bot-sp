/**
 * 姫路の種アシスタント — ブロックエディタ用サイドバー。
 *
 * ビルド不要で動くよう wp.element.createElement で書いている。
 * 新しい機能(地図検索・カテゴリ提案など)は
 * window.HimejiAssistant.registerPanel({ name, title, render }) で
 * パネルを1つ登録するだけで、このサイドバーに追加される。
 */
( function ( wp ) {
	'use strict';

	var el = wp.element.createElement;
	var useState = wp.element.useState;
	var useRef = wp.element.useRef;
	var registerPlugin = wp.plugins.registerPlugin;
	// WP 6.6 以降は wp.editor、それ以前は wp.editPost に PluginSidebar がある。
	var editorPkg = ( wp.editor && wp.editor.PluginSidebar ) ? wp.editor : wp.editPost;
	var PluginSidebar = editorPkg.PluginSidebar;
	var PluginSidebarMoreMenuItem = editorPkg.PluginSidebarMoreMenuItem;
	var components = wp.components;
	var PanelBody = components.PanelBody;
	var TextControl = components.TextControl;
	var Button = components.Button;
	var Spinner = components.Spinner;
	var dispatch = wp.data.dispatch;
	var select = wp.data.select;
	var apiFetch = wp.apiFetch;

	// ---- パネルレジストリ(将来の機能追加ポイント) -------------------------
	var registry = window.HimejiAssistant = window.HimejiAssistant || { panels: [] };
	registry.registerPanel = registry.registerPanel || function ( panel ) {
		registry.panels.push( panel );
	};

	// ---- カーソル位置へショートコードブロックを挿入 -----------------------
	function insertCard( postId ) {
		var block = wp.blocks.createBlock( 'core/shortcode', {
			text: '[himeji_card id="' + postId + '"]',
		} );
		var point = select( 'core/block-editor' ).getBlockInsertionPoint();
		dispatch( 'core/block-editor' ).insertBlocks( block, point.index, point.rootClientId );
	}

	// ---- リンクカード検索パネル -------------------------------------------
	function LinkCardPanel() {
		var queryState = useState( '' );
		var query = queryState[ 0 ];
		var setQuery = queryState[ 1 ];
		var resultsState = useState( null ); // null = 未検索, [] = 0件
		var results = resultsState[ 0 ];
		var setResults = resultsState[ 1 ];
		var loadingState = useState( false );
		var loading = loadingState[ 0 ];
		var setLoading = loadingState[ 1 ];
		var timerRef = useRef( null );
		var latestRef = useRef( 0 );

		function runSearch( q ) {
			if ( ! q ) {
				setResults( null );
				setLoading( false );
				return;
			}
			var token = ++latestRef.current;
			setLoading( true );
			apiFetch( {
				path: '/himeji-assistant/v1/search?q=' + encodeURIComponent( q ),
			} ).then( function ( items ) {
				if ( token !== latestRef.current ) {
					return; // 古いレスポンスは捨てる
				}
				setResults( items );
				setLoading( false );
			} ).catch( function () {
				if ( token === latestRef.current ) {
					setResults( [] );
					setLoading( false );
				}
			} );
		}

		function onChange( value ) {
			setQuery( value );
			if ( timerRef.current ) {
				clearTimeout( timerRef.current );
			}
			timerRef.current = setTimeout( function () {
				runSearch( value.trim() );
			}, 350 );
		}

		var children = [
			el( TextControl, {
				key: 'search',
				label: 'キーワードで過去記事を検索',
				placeholder: '例: 姫路城 桜',
				value: query,
				onChange: onChange,
				__nextHasNoMarginBottom: true,
			} ),
		];

		if ( loading ) {
			children.push( el( 'div', { key: 'spinner', className: 'himeji-assistant__spinner' }, el( Spinner ) ) );
		} else if ( results && results.length === 0 ) {
			children.push( el( 'p', { key: 'empty', className: 'himeji-assistant__help' }, '該当する記事が見つかりませんでした。' ) );
		} else if ( results ) {
			children.push( el(
				'ul',
				{ key: 'results', className: 'himeji-assistant__results' },
				results.map( function ( item ) {
					return el(
						'li',
						{ key: item.id, className: 'himeji-assistant__item' },
						item.thumbnail
							? el( 'img', { className: 'himeji-assistant__thumb', src: item.thumbnail, alt: '' } )
							: el( 'span', { className: 'himeji-assistant__thumb himeji-assistant__thumb--empty' } ),
						el(
							'div',
							{ className: 'himeji-assistant__meta' },
							el( 'div', { className: 'himeji-assistant__title', title: item.title }, item.title ),
							el( 'a', {
								className: 'himeji-assistant__url',
								href: item.url,
								target: '_blank',
								rel: 'noreferrer noopener',
							}, item.url.replace( /^https?:\/\//, '' ) ),
							el( Button, {
								variant: 'secondary',
								isSmall: true,
								className: 'himeji-assistant__insert',
								onClick: function () {
									insertCard( item.id );
								},
							}, 'カードを挿入' )
						)
					);
				} )
			) );
		} else {
			children.push( el( 'p', { key: 'help', className: 'himeji-assistant__help' },
				'キーワードを入力すると既存記事を検索し、リンクカードを本文に挿入できます。HTMLの知識は不要です。' ) );
		}

		return el( 'div', { className: 'himeji-assistant__panel' }, children );
	}

	// 標準搭載パネルとして登録
	registry.registerPanel( {
		name: 'link-card-search',
		title: 'リンクカード検索',
		render: LinkCardPanel,
	} );

	// ---- サイドバー本体 ---------------------------------------------------
	function Sidebar() {
		return el(
			wp.element.Fragment,
			null,
			PluginSidebarMoreMenuItem
				? el( PluginSidebarMoreMenuItem, { target: 'himeji-assistant-sidebar', icon: 'lightbulb' }, '姫路の種アシスタント' )
				: null,
			el(
				PluginSidebar,
				{ name: 'himeji-assistant-sidebar', title: '姫路の種アシスタント', icon: 'lightbulb' },
				registry.panels.map( function ( panel, i ) {
					return el(
						PanelBody,
						{ key: panel.name, title: panel.title, initialOpen: i === 0 },
						el( panel.render )
					);
				} )
			)
		);
	}

	registerPlugin( 'himeji-assistant', {
		render: Sidebar,
		icon: 'lightbulb',
	} );
} )( window.wp );
