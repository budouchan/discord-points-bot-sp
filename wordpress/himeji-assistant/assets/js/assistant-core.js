/**
 * 姫路の種アシスタント — 編集OSコア(ブロックエディタ)。
 *
 * 役割:
 * - サイドバーの「器」を提供し、登録されたパネルを並べる
 * - パネルの登録API: window.HimejiAssistant.registerPanel(...)
 * - パネルの表示/非表示設定(ユーザーごとに保存)
 * - AIヘルパー: window.HimejiAssistant.ai.complete(prompt, options)
 *
 * 新しいパネルの追加はスクリプト1本で完結する:
 *
 *   window.HimejiAssistant.registerPanel( {
 *       name: 'category-suggest',   // PHP側パネルの id と揃える
 *       title: 'カテゴリー提案',
 *       order: 30,
 *       render: MyPanelComponent,   // wp.element コンポーネント
 *   } );
 *
 * ビルド不要で動くよう wp.element.createElement で書いている。
 */
( function ( wp ) {
	'use strict';

	var el = wp.element.createElement;
	var Fragment = wp.element.Fragment;
	var useState = wp.element.useState;
	var registerPlugin = wp.plugins.registerPlugin;
	// WP 6.6 以降は wp.editor、それ以前は wp.editPost に PluginSidebar がある。
	var editorPkg = ( wp.editor && wp.editor.PluginSidebar ) ? wp.editor : wp.editPost;
	var PluginSidebar = editorPkg.PluginSidebar;
	var PluginSidebarMoreMenuItem = editorPkg.PluginSidebarMoreMenuItem;
	var PanelBody = wp.components.PanelBody;
	var ToggleControl = wp.components.ToggleControl;
	var apiFetch = wp.apiFetch;

	var data = window.HimejiAssistantData || { panels: [], hiddenPanels: [], aiAvailable: false };

	// ---- 公開API ----------------------------------------------------------
	var registry = window.HimejiAssistant = window.HimejiAssistant || {};
	registry.panels = registry.panels || [];
	registry.registerPanel = function ( panel ) {
		registry.panels.push( panel );
	};

	/**
	 * AIサービス層への窓口。パネルはどのAIプロバイダーが背後にいるかを
	 * 意識せずに使える。プロバイダー未設定時は available が false。
	 */
	registry.ai = {
		available: !! data.aiAvailable,
		complete: function ( prompt, options ) {
			options = options || {};
			return apiFetch( {
				path: '/himeji-assistant/v1/ai/complete',
				method: 'POST',
				data: {
					prompt: prompt,
					task: options.task || '',
					post_id: options.postId || 0,
				},
			} );
		},
	};

	// ---- パネル設定(表示/非表示) ----------------------------------------
	function findMeta( id ) {
		for ( var i = 0; i < data.panels.length; i++ ) {
			if ( data.panels[ i ].id === id ) {
				return data.panels[ i ];
			}
		}
		return null;
	}

	function SettingsPanel( props ) {
		return el(
			Fragment,
			null,
			el( 'p', { className: 'himeji-assistant__help' },
				'使わないパネルは非表示にできます(自分の画面にだけ反映されます)。' ),
			props.panels.map( function ( panel ) {
				var meta = findMeta( panel.name );
				return el( ToggleControl, {
					key: panel.name,
					label: panel.title,
					help: meta ? meta.description : '',
					checked: props.hidden.indexOf( panel.name ) === -1,
					onChange: function ( visible ) {
						props.onToggle( panel.name, visible );
					},
					__nextHasNoMarginBottom: true,
				} );
			} )
		);
	}

	// ---- サイドバー本体 ---------------------------------------------------
	function sortedPanels() {
		return registry.panels.slice().sort( function ( a, b ) {
			return ( a.order || 10 ) - ( b.order || 10 );
		} );
	}

	function Sidebar() {
		var hiddenState = useState( data.hiddenPanels || [] );
		var hidden = hiddenState[ 0 ];
		var setHidden = hiddenState[ 1 ];

		function onToggle( id, visible ) {
			var next = visible
				? hidden.filter( function ( h ) { return h !== id; } )
				: hidden.concat( id );
			setHidden( next );
			apiFetch( {
				path: '/himeji-assistant/v1/prefs',
				method: 'POST',
				data: { hidden: next },
			} );
		}

		var panels = sortedPanels();
		var visiblePanels = panels.filter( function ( panel ) {
			return hidden.indexOf( panel.name ) === -1;
		} );

		return el(
			Fragment,
			null,
			PluginSidebarMoreMenuItem
				? el( PluginSidebarMoreMenuItem, { target: 'himeji-assistant-sidebar', icon: 'lightbulb' }, '姫路の種アシスタント' )
				: null,
			el(
				PluginSidebar,
				{ name: 'himeji-assistant-sidebar', title: '姫路の種アシスタント', icon: 'lightbulb' },
				visiblePanels.map( function ( panel, i ) {
					return el(
						PanelBody,
						{ key: panel.name, title: panel.title, initialOpen: i === 0 },
						el( panel.render )
					);
				} ),
				el(
					PanelBody,
					{ key: '__settings', title: 'パネル設定', initialOpen: false, className: 'himeji-assistant__settings' },
					el( SettingsPanel, { panels: panels, hidden: hidden, onToggle: onToggle } )
				)
			)
		);
	}

	registerPlugin( 'himeji-assistant', {
		render: Sidebar,
		icon: 'lightbulb',
	} );
} )( window.wp );
