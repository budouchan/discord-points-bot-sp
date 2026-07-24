/**
 * パネル: Googleマップ検索。
 *
 * 店名・住所 → 候補表示 → 「地図を挿入」で [himeji_map] をカーソル位置へ。
 * 緯度経度の表示・コピーもできる。
 * APIキー未設定時は、検索語をそのまま地図にして挿入するフォールバック。
 */
( function ( wp ) {
	'use strict';

	var el = wp.element.createElement;
	var useState = wp.element.useState;
	var useRef = wp.element.useRef;
	var TextControl = wp.components.TextControl;
	var Button = wp.components.Button;
	var Spinner = wp.components.Spinner;
	var apiFetch = wp.apiFetch;
	var assistant = window.HimejiAssistant;
	var config = window.HimejiMapSearchData || { configured: false };

	// ショートコード属性を壊す文字を落とす。
	function attr( value ) {
		return String( value || '' ).replace( /["\[\]]/g, '' ).trim();
	}

	function insertMap( place ) {
		var q = attr( place.name ? place.name + ' ' + place.address : place.q );
		var sc = '[himeji_map q="' + q + '"';
		if ( place.lat && place.lng ) {
			sc += ' lat="' + place.lat.toFixed( 6 ) + '" lng="' + place.lng.toFixed( 6 ) + '"';
		}
		sc += ']';
		assistant.insertShortcode( sc );
		assistant.trackUsage( 'map-search' );
	}

	function MapSearchPanel() {
		var queryState = useState( '' );
		var query = queryState[ 0 ];
		var setQuery = queryState[ 1 ];
		var resultsState = useState( null );
		var results = resultsState[ 0 ];
		var setResults = resultsState[ 1 ];
		var loadingState = useState( false );
		var loading = loadingState[ 0 ];
		var setLoading = loadingState[ 1 ];
		var errorState = useState( '' );
		var error = errorState[ 0 ];
		var setError = errorState[ 1 ];
		var copiedState = useState( -1 );
		var copied = copiedState[ 0 ];
		var setCopied = copiedState[ 1 ];
		var timerRef = useRef( null );
		var latestRef = useRef( 0 );

		function runSearch( q ) {
			if ( ! q || ! config.configured ) {
				setResults( null );
				setLoading( false );
				return;
			}
			var token = ++latestRef.current;
			setLoading( true );
			setError( '' );
			apiFetch( {
				path: '/himeji-assistant/v1/maps/search?q=' + encodeURIComponent( q ),
			} ).then( function ( items ) {
				if ( token !== latestRef.current ) {
					return;
				}
				setResults( items );
				setLoading( false );
			} ).catch( function ( err ) {
				if ( token === latestRef.current ) {
					setResults( null );
					setLoading( false );
					setError( ( err && err.message ) || '地図検索に失敗しました。' );
				}
			} );
		}

		function onChange( value ) {
			setQuery( value );
			setCopied( -1 );
			if ( timerRef.current ) {
				clearTimeout( timerRef.current );
			}
			timerRef.current = setTimeout( function () {
				runSearch( value.trim() );
			}, 400 );
		}

		function copyLatLng( place, index ) {
			var text = place.lat.toFixed( 6 ) + ',' + place.lng.toFixed( 6 );
			if ( window.navigator.clipboard ) {
				window.navigator.clipboard.writeText( text ).then( function () {
					setCopied( index );
				} );
			}
		}

		var children = [
			el( TextControl, {
				key: 'search',
				label: '店名・住所で検索',
				placeholder: '例: 餃子のかっちゃん 姫路',
				value: query,
				onChange: onChange,
				__nextHasNoMarginBottom: true,
			} ),
		];

		if ( ! config.configured ) {
			children.push( el( 'p', { key: 'nokey', className: 'himeji-assistant__help' },
				'Google Maps APIキーが未設定のため候補検索は使えません(設定 → 姫路の種アシスタント)。下のボタンで検索語をそのまま地図にできます。' ) );
			if ( query.trim() ) {
				children.push( el( Button, {
					key: 'fallback',
					variant: 'secondary',
					onClick: function () {
						insertMap( { q: query } );
					},
				}, '「' + query.trim() + '」の地図を挿入' ) );
			}
			return el( 'div', { className: 'himeji-assistant__panel' }, children );
		}

		if ( loading ) {
			children.push( el( 'div', { key: 'spinner', className: 'himeji-assistant__spinner' }, el( Spinner ) ) );
		} else if ( error ) {
			children.push( el( 'p', { key: 'error', className: 'himeji-assistant__help' }, error ) );
		} else if ( results && results.length === 0 ) {
			children.push( el( 'p', { key: 'empty', className: 'himeji-assistant__help' }, '候補が見つかりませんでした。' ) );
		} else if ( results ) {
			children.push( el(
				'ul',
				{ key: 'results', className: 'himeji-assistant__results' },
				results.map( function ( place, index ) {
					return el(
						'li',
						{ key: index, className: 'himeji-assistant__item' },
						el(
							'div',
							{ className: 'himeji-assistant__meta' },
							el( 'div', { className: 'himeji-assistant__title' }, place.name ),
							el( 'div', { className: 'himeji-assistant__url' }, place.address ),
							el( 'div', { className: 'himeji-assistant__latlng' },
								place.lat.toFixed( 6 ) + ', ' + place.lng.toFixed( 6 ) ),
							el(
								'div',
								{ className: 'himeji-assistant__actions' },
								el( Button, {
									variant: 'secondary',
									isSmall: true,
									onClick: function () {
										insertMap( place );
									},
								}, '地図を挿入' ),
								el( Button, {
									variant: 'tertiary',
									isSmall: true,
									onClick: function () {
										copyLatLng( place, index );
									},
								}, copied === index ? 'コピーしました' : '緯度経度をコピー' )
							)
						)
					);
				} )
			) );
		} else {
			children.push( el( 'p', { key: 'help', className: 'himeji-assistant__help' },
				'Googleマップを開かなくても、ここから店名で検索してそのまま地図を記事に挿入できます。' ) );
		}

		return el( 'div', { className: 'himeji-assistant__panel' }, children );
	}

	assistant.registerPanel( {
		name: 'map-search',
		title: 'Googleマップ検索',
		order: 20,
		render: MapSearchPanel,
	} );
} )( window.wp );
