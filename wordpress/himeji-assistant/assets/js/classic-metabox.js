/**
 * 姫路の種アシスタント — クラシックエディタ用メタボックス。
 *
 * window.send_to_editor() を使い、TinyMCE / テキストエディタの
 * どちらでもカーソル位置にショートコードを挿入する。
 */
( function () {
	'use strict';

	var config = window.HimejiAssistantConfig || {};
	var input = document.getElementById( 'himeji-assistant-q' );
	var resultsBox = document.getElementById( 'himeji-assistant-results' );
	if ( ! input || ! resultsBox || ! config.restUrl ) {
		return;
	}

	var timer = null;
	var latest = 0;

	input.addEventListener( 'input', function () {
		if ( timer ) {
			clearTimeout( timer );
		}
		timer = setTimeout( function () {
			search( input.value.trim() );
		}, 350 );
	} );

	function search( q ) {
		if ( ! q ) {
			resultsBox.innerHTML = '';
			return;
		}
		var token = ++latest;
		resultsBox.innerHTML = '<p class="himeji-assistant__help">検索中…</p>';

		fetch( config.restUrl + '?q=' + encodeURIComponent( q ), {
			headers: { 'X-WP-Nonce': config.nonce },
			credentials: 'same-origin',
		} )
			.then( function ( res ) { return res.json(); } )
			.then( function ( items ) {
				if ( token !== latest ) {
					return;
				}
				renderResults( items );
			} )
			.catch( function () {
				if ( token === latest ) {
					resultsBox.innerHTML = '<p class="himeji-assistant__help">検索に失敗しました。</p>';
				}
			} );
	}

	function renderResults( items ) {
		resultsBox.innerHTML = '';
		if ( ! items || ! items.length ) {
			resultsBox.innerHTML = '<p class="himeji-assistant__help">該当する記事が見つかりませんでした。</p>';
			return;
		}

		var list = document.createElement( 'ul' );
		list.className = 'himeji-assistant__results';

		items.forEach( function ( item ) {
			var li = document.createElement( 'li' );
			li.className = 'himeji-assistant__item';

			if ( item.thumbnail ) {
				var img = document.createElement( 'img' );
				img.className = 'himeji-assistant__thumb';
				img.src = item.thumbnail;
				img.alt = '';
				li.appendChild( img );
			} else {
				var ph = document.createElement( 'span' );
				ph.className = 'himeji-assistant__thumb himeji-assistant__thumb--empty';
				li.appendChild( ph );
			}

			var meta = document.createElement( 'div' );
			meta.className = 'himeji-assistant__meta';

			var title = document.createElement( 'div' );
			title.className = 'himeji-assistant__title';
			title.textContent = item.title;
			title.title = item.title;
			meta.appendChild( title );

			var url = document.createElement( 'a' );
			url.className = 'himeji-assistant__url';
			url.href = item.url;
			url.target = '_blank';
			url.rel = 'noreferrer noopener';
			url.textContent = item.url.replace( /^https?:\/\//, '' );
			meta.appendChild( url );

			var button = document.createElement( 'button' );
			button.type = 'button';
			button.className = 'button button-small himeji-assistant__insert';
			button.textContent = 'カードを挿入';
			button.addEventListener( 'click', function () {
				window.send_to_editor( '[himeji_card id="' + item.id + '"]' );
			} );
			meta.appendChild( button );

			li.appendChild( meta );
			list.appendChild( li );
		} );

		resultsBox.appendChild( list );
	}
} )();
