/**
 * パネル: リンクカード検索(編集OSの第1号パネル)。
 *
 * キーワードで過去記事を検索(タイトル+本文)し、「カードを挿入」で
 * カーソル位置に [himeji_card id="…"] を挿入する。
 * 並び順は 関連度順 / 新着順 / 人気順 を選べる。
 */
( function ( wp ) {
	'use strict';

	var el = wp.element.createElement;
	var useState = wp.element.useState;
	var useRef = wp.element.useRef;
	var TextControl = wp.components.TextControl;
	var SelectControl = wp.components.SelectControl;
	var Spinner = wp.components.Spinner;
	var apiFetch = wp.apiFetch;
	var assistant = window.HimejiAssistant;

	function LinkCardPanel() {
		var queryState = useState( '' );
		var query = queryState[ 0 ];
		var setQuery = queryState[ 1 ];
		var orderState = useState( 'relevance' );
		var orderby = orderState[ 0 ];
		var setOrderby = orderState[ 1 ];
		var resultsState = useState( null ); // null = 未検索, [] = 0件
		var results = resultsState[ 0 ];
		var setResults = resultsState[ 1 ];
		var loadingState = useState( false );
		var loading = loadingState[ 0 ];
		var setLoading = loadingState[ 1 ];
		var timerRef = useRef( null );
		var latestRef = useRef( 0 );

		function runSearch( q, order ) {
			if ( ! q ) {
				setResults( null );
				setLoading( false );
				return;
			}
			var token = ++latestRef.current;
			setLoading( true );
			apiFetch( {
				path: '/himeji-assistant/v1/search?q=' + encodeURIComponent( q ) + '&orderby=' + order,
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
				runSearch( value.trim(), orderby );
			}, 350 );
		}

		function onChangeOrderby( value ) {
			setOrderby( value );
			runSearch( query.trim(), value );
		}

		var children = [
			el( TextControl, {
				key: 'search',
				label: 'キーワードで過去記事を検索',
				placeholder: '例: 姫路城 桜',
				value: query,
				onChange: onChange,
				help: 'タイトルと本文が検索対象です。',
				__nextHasNoMarginBottom: true,
			} ),
			el( SelectControl, {
				key: 'orderby',
				label: '並び順',
				value: orderby,
				options: [
					{ value: 'relevance', label: '関連度順' },
					{ value: 'date', label: '新着順' },
					{ value: 'popular', label: '人気順' },
				],
				onChange: onChangeOrderby,
				__nextHasNoMarginBottom: true,
			} ),
		];

		if ( loading ) {
			children.push( el( 'div', { key: 'spinner', className: 'himeji-assistant__spinner' }, el( Spinner ) ) );
		} else if ( results && results.length === 0 ) {
			children.push( el( 'p', { key: 'empty', className: 'himeji-assistant__help' }, '該当する記事が見つかりませんでした。' ) );
		} else if ( results ) {
			children.push( el( assistant.ui.ArticleList, { key: 'results', items: results, panel: 'link-card-search' } ) );
		} else {
			children.push( el( 'p', { key: 'help', className: 'himeji-assistant__help' },
				'キーワードを入力すると既存記事を検索し、リンクカードを本文に挿入できます。HTMLの知識は不要です。' ) );
		}

		return el( 'div', { className: 'himeji-assistant__panel' }, children );
	}

	assistant.registerPanel( {
		name: 'link-card-search',
		title: 'リンクカード検索',
		order: 10,
		render: LinkCardPanel,
	} );
} )( window.wp );
