/**
 * パネル: AI関連記事推薦。
 *
 * ボタン1つで、執筆中のタイトル・本文をサーバーに送り、
 * WordPressが検索した候補をAIが並び替えた結果を表示する。
 * 結果は共通の記事リストUIなので、そのまま「カードを挿入」できる。
 */
( function ( wp ) {
	'use strict';

	var el = wp.element.createElement;
	var useState = wp.element.useState;
	var Button = wp.components.Button;
	var Spinner = wp.components.Spinner;
	var apiFetch = wp.apiFetch;
	var assistant = window.HimejiAssistant;

	function RelatedSuggestPanel() {
		var resultState = useState( null ); // { items, ai, provider }
		var result = resultState[ 0 ];
		var setResult = resultState[ 1 ];
		var loadingState = useState( false );
		var loading = loadingState[ 0 ];
		var setLoading = loadingState[ 1 ];
		var errorState = useState( '' );
		var error = errorState[ 0 ];
		var setError = errorState[ 1 ];

		function run() {
			var editor = wp.data.select( 'core/editor' );
			var title = editor.getEditedPostAttribute( 'title' ) || '';
			var content = editor.getEditedPostContent() || '';
			var postId = editor.getCurrentPostId() || 0;

			if ( ! title ) {
				setError( 'タイトルを入力してから実行してください。' );
				return;
			}

			setLoading( true );
			setError( '' );
			apiFetch( {
				path: '/himeji-assistant/v1/recommend',
				method: 'POST',
				data: {
					title: title,
					content: content.slice( 0, 5000 ),
					post_id: postId,
				},
			} ).then( function ( res ) {
				setResult( res );
				setLoading( false );
			} ).catch( function ( err ) {
				setLoading( false );
				setError( ( err && err.message ) || '推薦の取得に失敗しました。' );
			} );
		}

		var children = [
			el( 'p', { key: 'help', className: 'himeji-assistant__help' },
				'執筆中の記事に合う関連記事を提案します。WordPressが候補を検索し、AIが最適な記事を選びます。' ),
			el( Button, {
				key: 'run',
				variant: 'primary',
				isBusy: loading,
				disabled: loading,
				onClick: run,
			}, loading ? '探しています…' : 'この記事に合う関連記事を探す' ),
		];

		if ( loading ) {
			children.push( el( 'div', { key: 'spinner', className: 'himeji-assistant__spinner' }, el( Spinner ) ) );
		} else if ( error ) {
			children.push( el( 'p', { key: 'error', className: 'himeji-assistant__help' }, error ) );
		} else if ( result ) {
			if ( ! result.items.length ) {
				children.push( el( 'p', { key: 'empty', className: 'himeji-assistant__help' }, '関連しそうな記事が見つかりませんでした。' ) );
			} else {
				children.push( el( 'p', { key: 'mode', className: 'himeji-assistant__help' },
					result.ai
						? 'AI(' + result.provider + ')が選んだ関連記事です。'
						: 'AIが未設定のため、カテゴリー・検索の関連度スコア順で表示しています。' ) );
				children.push( el( assistant.ui.ArticleList, { key: 'results', items: result.items } ) );
			}
		}

		return el( 'div', { className: 'himeji-assistant__panel' }, children );
	}

	assistant.registerPanel( {
		name: 'related-suggest',
		title: 'AI関連記事推薦',
		order: 40,
		render: RelatedSuggestPanel,
	} );
} )( window.wp );
