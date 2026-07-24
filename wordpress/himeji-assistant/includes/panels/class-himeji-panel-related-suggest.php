<?php
/**
 * パネル: AI関連記事推薦。
 *
 * 構成は「WordPressが検索 → AIが選ぶ」:
 *
 *   1. WordPress側で候補を集める(タイトル検索 + 同カテゴリー + 新着)
 *   2. AIプロバイダーが設定されていれば、候補一覧を渡して
 *      「執筆中の記事に最適な関連記事」を選ばせる(= 並び替え役)
 *   3. AI未設定なら、共通タームの一致数によるヒューリスティックで並べる
 *
 * AIは検索エンジンではないので、毎回全記事を読むことはない。
 * 候補はWordPressのインデックスから引くため高速で、AIコールも
 * タイトル一覧を渡す1回だけ。
 */

defined( 'ABSPATH' ) || exit;

class Himeji_Panel_Related_Suggest extends Himeji_Assistant_Panel {

	const CANDIDATE_LIMIT = 20;
	const RESULT_LIMIT    = 5;

	public function id() {
		return 'related-suggest';
	}

	public function title() {
		return 'AI関連記事推薦';
	}

	public function description() {
		return '執筆中の記事に合う関連記事を提案します(AI未設定時は関連度スコア順)。';
	}

	public function order() {
		return 40;
	}

	public function editor_script() {
		return array(
			'handle' => 'himeji-panel-related-suggest',
			'src'    => HIMEJI_ASSISTANT_URL . 'assets/js/panels/related-suggest.js',
			'deps'   => array(),
		);
	}

	public function register() {
		add_action( 'rest_api_init', array( $this, 'register_routes' ) );
	}

	public function register_routes() {
		register_rest_route(
			Himeji_Assistant_REST::NAMESPACE,
			'/recommend',
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => array( $this, 'recommend' ),
				'permission_callback' => array( 'Himeji_Assistant_REST', 'can_use' ),
				'args'                => array(
					'title'   => array(
						'type'              => 'string',
						'default'           => '',
						'sanitize_callback' => 'sanitize_text_field',
					),
					'content' => array(
						'type'    => 'string',
						'default' => '',
					),
					'post_id' => array(
						'type'    => 'integer',
						'default' => 0,
					),
				),
			)
		);
	}

	public function recommend( WP_REST_Request $request ) {
		$title   = $request['title'];
		$post_id = (int) $request['post_id'];
		$content = wp_html_excerpt( wp_strip_all_tags( (string) $request['content'] ), 600, '…' );

		if ( '' === $title && ! $post_id ) {
			return new WP_Error( 'himeji_recommend_no_input', 'タイトルを入力してから実行してください。', array( 'status' => 400 ) );
		}

		// 1. WordPressが候補を検索する。
		$candidates = $this->collect_candidates( $title, $post_id );
		if ( empty( $candidates ) ) {
			return rest_ensure_response( array( 'items' => array(), 'ai' => false, 'provider' => null ) );
		}

		// 2. AIが並び替える(未設定ならヒューリスティック順のまま)。
		$provider = Himeji_Assistant_AI::active_provider();
		$used_ai  = false;
		$ordered  = array_keys( $candidates );

		if ( $provider ) {
			$picked = $this->rerank_with_ai( $provider, $title, $content, $candidates, $post_id );
			if ( ! empty( $picked ) ) {
				$ordered = $picked;
				$used_ai = true;
			}
		}

		$items = array();
		foreach ( array_slice( $ordered, 0, self::RESULT_LIMIT ) as $id ) {
			$post = get_post( $id );
			if ( ! $post ) {
				continue;
			}
			$items[] = array(
				'id'        => $post->ID,
				'title'     => html_entity_decode( get_the_title( $post ), ENT_QUOTES, 'UTF-8' ),
				'url'       => get_permalink( $post ),
				'date'      => get_the_date( 'Y-m-d', $post ),
				'thumbnail' => get_the_post_thumbnail_url( $post, 'thumbnail' ) ?: '',
			);
		}

		return rest_ensure_response(
			array(
				'items'    => $items,
				'ai'       => $used_ai,
				'provider' => $used_ai ? $provider->id() : null,
			)
		);
	}

	/**
	 * 候補集め: タイトル検索 + 同カテゴリー + 新着で最大20件。
	 * 共通ターム数 + 新しさで軽くスコアリングして返す(id => タイトル)。
	 */
	private function collect_candidates( $title, $post_id ) {
		$post_types = apply_filters( 'himeji_assistant_search_post_types', array( 'post', 'page' ) );
		$base       = array(
			'post_type'              => $post_types,
			'post_status'            => 'publish',
			'fields'                 => 'ids',
			'no_found_rows'          => true,
			'update_post_term_cache' => false,
			'ignore_sticky_posts'    => true,
		);
		if ( $post_id ) {
			$base['post__not_in'] = array( $post_id );
		}

		$ids = array();

		if ( '' !== $title ) {
			$by_title = new WP_Query( array_merge( $base, array( 's' => $title, 'posts_per_page' => 10, 'orderby' => 'relevance' ) ) );
			$ids      = array_merge( $ids, $by_title->posts );
		}

		$current_terms = array();
		if ( $post_id ) {
			$current_terms = wp_get_post_categories( $post_id );
			if ( $current_terms ) {
				$by_cat = new WP_Query( array_merge( $base, array( 'category__in' => $current_terms, 'posts_per_page' => 10 ) ) );
				$ids    = array_merge( $ids, $by_cat->posts );
			}
		}

		if ( count( array_unique( $ids ) ) < self::CANDIDATE_LIMIT ) {
			$recent = new WP_Query( array_merge( $base, array( 'posts_per_page' => 10 ) ) );
			$ids    = array_merge( $ids, $recent->posts );
		}

		$ids = array_slice( array_unique( $ids ), 0, self::CANDIDATE_LIMIT );

		// ヒューリスティック: 共通カテゴリー数で降順(検索ヒット順は維持)。
		if ( $current_terms ) {
			$scores = array();
			foreach ( $ids as $i => $id ) {
				$shared        = count( array_intersect( $current_terms, wp_get_post_categories( $id ) ) );
				$scores[ $id ] = $shared * 1000 - $i; // 同点は元の順序を保つ
			}
			usort(
				$ids,
				function ( $a, $b ) use ( $scores ) {
					return $scores[ $b ] - $scores[ $a ];
				}
			);
		}

		$candidates = array();
		foreach ( $ids as $id ) {
			$candidates[ $id ] = get_the_title( $id );
		}
		return $candidates;
	}

	/**
	 * AIに候補一覧から選ばせる。返り値は選ばれた記事IDの配列(関連度順)。
	 * パースに失敗したら空配列(呼び出し側でヒューリスティックにフォールバック)。
	 */
	private function rerank_with_ai( $provider, $title, $content, array $candidates, $post_id ) {
		$list = '';
		foreach ( $candidates as $id => $candidate_title ) {
			$list .= sprintf( "- %d: %s\n", $id, $candidate_title );
		}

		$prompt = "あなたは地域メディア「姫路の種」の編集者です。\n"
			. "執筆中の記事の末尾に「あわせて読みたい」として添える関連記事を、候補一覧から最大5件選んでください。\n\n"
			. "# 執筆中の記事\n"
			. 'タイトル: ' . $title . "\n"
			. ( $content ? '本文冒頭: ' . $content . "\n" : '' )
			. "\n# 候補一覧(ID: タイトル)\n" . $list
			. "\n関連度が高い順に、選んだ記事のIDだけをJSON配列で出力してください。例: [123, 456, 789]";

		$result = $provider->complete( $prompt, array( 'task' => 'related-suggest', 'post_id' => $post_id ) );
		if ( is_wp_error( $result ) || ! is_string( $result ) ) {
			return array();
		}

		if ( ! preg_match( '/\[[\d,\s]*\]/', $result, $matches ) ) {
			return array();
		}
		$ids = json_decode( $matches[0], true );
		if ( ! is_array( $ids ) ) {
			return array();
		}

		// AIの答えは候補に実在するIDだけ採用する(幻覚ID対策)。
		return array_values( array_intersect( array_map( 'intval', $ids ), array_keys( $candidates ) ) );
	}
}
